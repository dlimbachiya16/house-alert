import csv
import io
import time
import logging
import requests

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

# Correct region IDs pulled directly from Redfin URLs
CITY_REGION_IDS = {
    "Hoffman Estates":   "29487",
    "Schaumburg":        "29511",
    "Bartlett":          "29462",
    "Carol Stream":      "2933",
    "Hanover Park":      "29485",
    "Elk Grove Village": "29478",
    "Streamwood":        "18644",
    "Roselle":           "29508",
}

URL_COL = "URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)"

from config import MIN_BEDS, MIN_BATHS, MAX_PRICE, MIN_PRICE


def fetch_csv(region_id):
    url = "https://www.redfin.com/stingray/api/gis-csv"
    params = {
        "al": 1,
        "market": "chicago",
        "num_homes": 350,
        "region_id": region_id,
        "region_type": 6,
        "status": 9,
        "uipt": "1,3",
        "v": 8,
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def parse_csv(csv_text):
    lines = csv_text.strip().splitlines()
    # Find real header line (skip disclaimer row)
    header_idx = None
    for i, line in enumerate(lines):
        if "ADDRESS" in line and "BEDS" in line:
            header_idx = i
            break
    if header_idx is None:
        return []
    real_csv = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(real_csv))
    return list(reader)


def passes_filter(row):
    """Client-side filter since Redfin ignores server-side params."""
    try:
        # Skip disclaimer/blank rows
        if not row.get("ADDRESS") and not row.get("MLS#"):
            return False
        # Skip rows where SALE TYPE is the disclaimer text
        if "accordance" in (row.get("SALE TYPE") or "").lower():
            return False

        price = int(float((row.get("PRICE") or "0").replace("$", "").replace(",", "") or 0))
        beds  = float(row.get("BEDS") or 0)
        baths = float(row.get("BATHS") or 0)
        state = (row.get("STATE OR PROVINCE") or "").strip().upper()

        return (
            state == "IL"
            and beds >= MIN_BEDS
            and baths >= MIN_BATHS
            and MIN_PRICE <= price <= MAX_PRICE
        )
    except Exception:
        return False


def parse_row(row, city):
    try:
        price_raw = (row.get("PRICE") or "0").replace("$", "").replace(",", "").strip()
        price = int(float(price_raw)) if price_raw else 0

        beds  = float(row.get("BEDS")  or 0)
        baths = float(row.get("BATHS") or 0)

        sqft_raw = (row.get("SQUARE FEET") or "0").replace(",", "").strip()
        sqft = int(float(sqft_raw)) if sqft_raw else 0

        address  = row.get("ADDRESS", "").strip()
        city_val = row.get("CITY", city).strip()
        state    = row.get("STATE OR PROVINCE", "IL").strip()
        zip_code = row.get("ZIP OR POSTAL CODE", "").strip()
        status   = row.get("STATUS", "").strip()
        mls_id   = row.get("MLS#", "").strip()
        url      = row.get(URL_COL, "").strip()

        if not mls_id:
            return None

        return {
            "id":      mls_id,
            "address": f"{address}, {city_val}, {state} {zip_code}".strip(", "),
            "price":   price,
            "beds":    beds,
            "baths":   baths,
            "sqft":    sqft,
            "status":  status,
            "url":     url,
            "city":    city_val,
        }
    except Exception as e:
        logger.debug(f"Row parse error: {e}")
        return None


def fetch_city_listings(city):
    region_id = CITY_REGION_IDS.get(city)
    if not region_id:
        logger.warning(f"No region ID for {city}")
        return []

    try:
        csv_text = fetch_csv(region_id)
    except Exception as e:
        logger.error(f"Failed to fetch {city}: {e}")
        return []

    if "<html" in csv_text[:300].lower():
        logger.warning(f"Got HTML for {city} — blocked")
        return []

    rows = parse_csv(csv_text)
    listings = []
    for row in rows:
        if passes_filter(row):
            parsed = parse_row(row, city)
            if parsed:
                listings.append(parsed)

    logger.info(f"  {city}: {len(listings)} listings after filter")
    return listings


def fetch_all_listings():
    all_listings = []
    for city in CITY_REGION_IDS:
        logger.info(f"Fetching: {city}")
        listings = fetch_city_listings(city)
        all_listings.extend(listings)
        time.sleep(2)
    logger.info(f"Total listings: {len(all_listings)}")
    return all_listings
