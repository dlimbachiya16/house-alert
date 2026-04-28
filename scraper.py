"""
scraper.py
Fetches listings from Redfin's undocumented CSV download endpoint.
Returns a list of dicts, one per listing.
"""

import csv
import io
import time
import logging
import requests
from config import (
    CITIES, STATE, MIN_BEDS, MIN_BATHS,
    MAX_PRICE, MIN_PRICE, PROPERTY_TYPES,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.redfin.com/",
}

# ── Step 1: resolve city → Redfin region_id ──────────────────────────────────

REGION_SEARCH_URL = "https://www.redfin.com/stingray/do/location-autocomplete"

def get_region_id(city: str, state: str) -> str | None:
    """Query Redfin autocomplete to get the region_id for a city."""
    params = {
        "location": f"{city}, {state}",
        "start": 0,
        "count": 5,
        "v": 2,
        "market": "chicago",
        "al": 1,
        "iss": "false",
        "ooa": "true",
    }
    try:
        r = requests.get(REGION_SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        # Redfin wraps JSON in "{}&&" prefix — strip it
        text = r.text
        if text.startswith("{}&&"):
            text = text[4:]
        import json
        data = json.loads(text)
        items = data.get("payload", {}).get("sections", [])
        for section in items:
            for row in section.get("rows", []):
                if row.get("type") == "2":  # type 2 = city
                    return row["id"].split("_")[1]  # e.g. "city_29401" → "29401"
    except Exception as e:
        logger.warning(f"Could not resolve region_id for {city}: {e}")
    return None


# ── Step 2: download CSV for a region ────────────────────────────────────────

CSV_DOWNLOAD_URL = "https://www.redfin.com/stingray/api/gis-csv"

def fetch_city_listings(city: str) -> list[dict]:
    """Fetch all matching listings for one city as a list of dicts."""
    region_id = get_region_id(city, STATE)
    if not region_id:
        logger.warning(f"Skipping {city} — could not get region_id")
        return []

    params = {
        "al": 1,
        "market": "chicago",
        "min_beds": MIN_BEDS,
        "min_baths": MIN_BATHS,
        "max_price": MAX_PRICE,
        "min_price": MIN_PRICE,
        "property_type": PROPERTY_TYPES,
        "region_id": region_id,
        "region_type": 6,          # 6 = city
        "status": 9,               # 9 = active + contingent + pending
        "uipt": PROPERTY_TYPES,
        "v": 8,
        "num_homes": 350,
    }

    try:
        r = requests.get(CSV_DOWNLOAD_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        content = r.text

        # Redfin sometimes returns an error page if bot-detected
        if "<html" in content[:200].lower():
            logger.warning(f"Got HTML instead of CSV for {city} — possibly blocked")
            return []

        listings = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            parsed = parse_row(row, city)
            if parsed:
                listings.append(parsed)
        logger.info(f"  {city}: {len(listings)} listings fetched")
        return listings

    except Exception as e:
        logger.error(f"Error fetching {city}: {e}")
        return []


# ── Step 3: parse a CSV row into a clean dict ─────────────────────────────────

def parse_row(row: dict, city: str) -> dict | None:
    """Normalize a Redfin CSV row. Returns None if row is unusable."""
    try:
        mls_id = row.get("MLS#", "").strip()
        if not mls_id:
            return None

        price_raw = row.get("PRICE", "0").replace("$", "").replace(",", "").strip()
        price = int(float(price_raw)) if price_raw else 0

        beds_raw = row.get("BEDS", "0").strip()
        beds = float(beds_raw) if beds_raw else 0

        baths_raw = row.get("BATHS", "0").strip()
        baths = float(baths_raw) if baths_raw else 0

        sqft_raw = row.get("SQUARE FEET", "0").replace(",", "").strip()
        sqft = int(float(sqft_raw)) if sqft_raw else 0

        status = row.get("STATUS", "").strip()
        address = row.get("ADDRESS", "").strip()
        zip_code = row.get("ZIP OR POSTAL CODE", "").strip()
        url = row.get("URL (SEE http://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)", "").strip()
        if url and not url.startswith("http"):
            url = "https://www.redfin.com" + url

        return {
            "id": mls_id,
            "address": f"{address}, {city}, {STATE} {zip_code}".strip(", "),
            "price": price,
            "beds": beds,
            "baths": baths,
            "sqft": sqft,
            "status": status,
            "url": url,
            "city": city,
        }
    except Exception as e:
        logger.debug(f"Row parse error: {e} | row={row}")
        return None


# ── Public entry point ────────────────────────────────────────────────────────

def fetch_all_listings() -> list[dict]:
    """Fetch listings for ALL configured cities. Returns combined list."""
    all_listings = []
    for city in CITIES:
        logger.info(f"Fetching: {city}")
        listings = fetch_city_listings(city)
        all_listings.extend(listings)
        time.sleep(2)  # be polite — avoid hammering Redfin
    logger.info(f"Total listings fetched: {len(all_listings)}")
    return all_listings
