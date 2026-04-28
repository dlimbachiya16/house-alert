"""
main.py
Orchestrates: fetch → diff against seen_listings.json → alert → save.
"""

import json
import logging
import os
import sys
from pathlib import Path

from config import SEEN_FILE, ACTIVE_STATUSES, PENDING_STATUSES, SOLD_STATUSES
from scraper import fetch_all_listings
from notifier import alert_new_listing, alert_status_change, alert_price_change, alert_run_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_seen() -> dict:
    path = Path(SEEN_FILE)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.warning(f"Could not load {SEEN_FILE}: {e} — starting fresh")
    return {}


def save_seen(seen: dict):
    Path(SEEN_FILE).write_text(json.dumps(seen, indent=2))
    logger.info(f"Saved {len(seen)} listings to {SEEN_FILE}")


def normalize_status(status: str) -> str:
    s = status.strip().title()
    return s


def is_sold_or_pending(status: str) -> bool:
    su = status.upper()
    return any(s in su for s in ["SOLD", "CLOSED", "PENDING", "CONTINGENT", "UNDER CONTRACT"])


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    logger.info("=== House Alert Run Started ===")

    seen = load_seen()
    new_count = 0
    changed_count = 0
    error_count = 0

    try:
        fresh_listings = fetch_all_listings()
    except Exception as e:
        logger.error(f"Fatal error fetching listings: {e}")
        sys.exit(1)

    if not fresh_listings:
        logger.warning("No listings returned — possible block or network issue")
        sys.exit(0)

    # Build a lookup by MLS id from fresh fetch
    fresh_by_id: dict[str, dict] = {}
    for listing in fresh_listings:
        lid = listing["id"]
        # If duplicate MLS id across cities (shouldn't happen), last one wins
        fresh_by_id[lid] = listing

    # ── Diff ──────────────────────────────────────────────────────────────────

    for lid, listing in fresh_by_id.items():
        if lid not in seen:
            # Brand new listing
            logger.info(f"NEW: {listing['address']} ({listing['status']})")
            try:
                alert_new_listing(listing)
                new_count += 1
            except Exception as e:
                logger.error(f"Alert failed for new listing {lid}: {e}")
                error_count += 1
            seen[lid] = {
                "status": listing["status"],
                "price": listing["price"],
                "address": listing["address"],
            }
        else:
            prev = seen[lid]
            old_status = prev.get("status", "")
            old_price = prev.get("price", 0)

            status_changed = normalize_status(listing["status"]) != normalize_status(old_status)
            price_changed = listing["price"] != old_price and listing["price"] > 0

            if status_changed:
                logger.info(f"STATUS CHANGE: {listing['address']} | {old_status} → {listing['status']}")
                try:
                    alert_status_change(listing, old_status)
                    changed_count += 1
                except Exception as e:
                    logger.error(f"Status alert failed {lid}: {e}")
                    error_count += 1

            elif price_changed:
                logger.info(f"PRICE CHANGE: {listing['address']} | ${old_price:,} → ${listing['price']:,}")
                try:
                    alert_price_change(listing, old_price)
                    changed_count += 1
                except Exception as e:
                    logger.error(f"Price alert failed {lid}: {e}")
                    error_count += 1

            # Update seen record
            seen[lid]["status"] = listing["status"]
            seen[lid]["price"] = listing["price"]

    # ── Check for listings that disappeared from results ──────────────────────
    # (Redfin sometimes drops them before showing Sold — don't spam, just log)
    fresh_ids = set(fresh_by_id.keys())
    for lid in list(seen.keys()):
        if lid not in fresh_ids:
            logger.info(f"Listing no longer in results: {seen[lid].get('address', lid)}")
            # Don't delete — keep in seen so we don't re-alert if it reappears

    save_seen(seen)

    logger.info(f"Done. New={new_count}, Changed={changed_count}, Errors={error_count}")
    alert_run_summary(new_count, changed_count, error_count)
    logger.info("=== Run Complete ===")


if __name__ == "__main__":
    run()
