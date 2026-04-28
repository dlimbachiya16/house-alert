"""
notifier.py
Sends Telegram messages via Bot API.
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _send(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def _fmt_price(price: int) -> str:
    return f"${price:,}" if price else "N/A"


def _fmt_num(val) -> str:
    if val == int(val):
        return str(int(val))
    return str(val)


def alert_new_listing(listing: dict):
    url_line = f'\n🔗 <a href="{listing["url"]}">View on Redfin</a>' if listing.get("url") else ""
    msg = (
        f"🏠 <b>NEW LISTING</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 {listing['address']}\n"
        f"💰 {_fmt_price(listing['price'])}\n"
        f"🛏  {_fmt_num(listing['beds'])} beds  "
        f"🚿 {_fmt_num(listing['baths'])} baths  "
        f"📐 {listing['sqft']:,} sqft\n"
        f"📋 Status: {listing['status']}"
        f"{url_line}"
    )
    _send(msg)


def alert_status_change(listing: dict, old_status: str):
    emoji = "⏳"
    label = "STATUS CHANGE"
    status = listing["status"].upper()

    if any(s in status for s in ["SOLD", "CLOSED"]):
        emoji = "🔴"
        label = "SOLD / CLOSED"
    elif any(s in status for s in ["PENDING", "CONTINGENT", "UNDER CONTRACT"]):
        emoji = "🟡"
        label = "PENDING / CONTINGENT"

    url_line = f'\n🔗 <a href="{listing["url"]}">View on Redfin</a>' if listing.get("url") else ""
    msg = (
        f"{emoji} <b>{label}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 {listing['address']}\n"
        f"💰 {_fmt_price(listing['price'])}\n"
        f"🛏  {_fmt_num(listing['beds'])} beds  "
        f"🚿 {_fmt_num(listing['baths'])} baths  "
        f"📐 {listing['sqft']:,} sqft\n"
        f"📋 {old_status}  →  {listing['status']}"
        f"{url_line}"
    )
    _send(msg)


def alert_price_change(listing: dict, old_price: int):
    direction = "📉 PRICE DROP" if listing["price"] < old_price else "📈 PRICE INCREASE"
    url_line = f'\n🔗 <a href="{listing["url"]}">View on Redfin</a>' if listing.get("url") else ""
    msg = (
        f"{direction}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 {listing['address']}\n"
        f"💰 {_fmt_price(old_price)}  →  {_fmt_price(listing['price'])}\n"
        f"🛏  {_fmt_num(listing['beds'])} beds  "
        f"🚿 {_fmt_num(listing['baths'])} baths  "
        f"📐 {listing['sqft']:,} sqft"
        f"{url_line}"
    )
    _send(msg)


def alert_run_summary(new: int, changed: int, errors: int):
    """Optional heartbeat — fires only if something happened."""
    if new == 0 and changed == 0:
        return
    msg = (
        f"📊 <b>Run Summary</b>\n"
        f"New listings: {new}\n"
        f"Status/price changes: {changed}\n"
        f"Errors: {errors}"
    )
    _send(msg)
