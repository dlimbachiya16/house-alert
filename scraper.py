import json
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

from config import MIN_BEDS, MIN_BATHS, MAX_PRICE, MIN_PRICE, STATE


def fetch_gis(region_id):
    url = "https://www.redfin.com/stingray/api/gis"
    params = {
        "al": 1,
        "market": "chicago",
        "min_beds": MIN_BEDS,
        "min_baths": MIN_BATHS,
        "max_price": MAX_PRICE,
        "min_price": MIN_PRICE,
        "num_homes": 350,
        "page_number": 1,
        "region_id": region_id,
        "region_type": 6,
        "status": 9,
        "uipt": "1",        # single family only
        "v": 8,
        "sf": "1,2,3,5,6,7",
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    text = r.text
    if text.startswith("{}&&"):
        text = text[4:]
    return json.loads(text)


def parse_home(home, city):
    try:
        # Skip non-single-family
        if home.get("uiPropertyType") != 1:
            return None

        # Skip wrong state
        if home.get("state", "").upper() != STATE:
            return None

        price = (home.get("price") or {}).get("value", 0) or 0
        beds  = home.get("beds", 0) or 0
        baths = home.get("baths", 0) or 0
        sqft  = (home.get("sqFt") or {}).get("value", 0) or 0

        # Client-side filter (server filters don't always apply)
        if price > MAX_PRICE or price < MIN_PRICE:
            return None
        if beds < MIN_BEDS or baths < MIN_BATHS:
            return None

        street   = (home.get("streetLine") or {}).get("value", "").strip()
        city_val = home.get("city", city).strip()
        state    = home.get("state", STATE).strip()
        zip_code = home.get("zip", "").strip()
        status   = home.get("mlsStatus", "").strip()
        mls_id   = (home.get("mlsId") or {}).get("value", "").strip()
        url_path = home.get("url", "")
        url      = f"https://www.redfin.com{url_path}" if url_path else ""
        listing_id = str(home.get("listingId") or home.get("propertyId") or mls_id)

        if not listing_id:
            return None

        return {
            "id":      listing_id,
            "address": f"{street}, {city_val}, {state} {zip_code}".strip(", "),
            "price":   price,
            "beds":    beds,
            "baths":   baths,
            "sqft":    sqft,
            "status":  status,
            "url":     url,
            "city":    city_val,
        }
    except Exception as e:
        logger.debug(f"Parse error: {e}")
        return None


def fetch_city_listings(city):
    region_id = CITY_REGION_IDS.get(city)
    if not region_id:
        logger.warning(f"No region ID for {city}")
        return []

    try:
        data = fetch_gis(region_id)
    except Exception as e:
        logger.error(f"Failed to fetch {city}: {e}")
        return []

    homes = data.get("payload", {}).get("homes", [])
    listings = []
    for home in homes:
        parsed = parse_home(home, city)
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
