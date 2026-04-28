import json
import time
import requests

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

MIN_BEDS  = 4
MIN_BATHS = 2
MAX_PRICE = 451000
MIN_PRICE = 0
STATE     = "IL"

print("Script started", flush=True)

total_matched = 0

for city, region_id in CITY_REGION_IDS.items():
    print(f"\n{'='*50}", flush=True)
    print(f"CITY: {city} | region_id: {region_id}", flush=True)

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
        "uipt": "1",
        "v": 8,
        "sf": "1,2,3,5,6,7",
    }

    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    text = r.text
    if text.startswith("{}&&"):
        text = text[4:]

    data = json.loads(text)
    homes = data.get("payload", {}).get("homes", [])
    print(f"  Raw homes returned: {len(homes)}", flush=True)

    matched = []
    for home in homes:
        if home.get("uiPropertyType") != 1:
            continue
        if home.get("state", "").upper() != STATE:
            continue
        price = (home.get("price") or {}).get("value", 0) or 0
        beds  = home.get("beds", 0) or 0
        baths = home.get("baths", 0) or 0
        if price > MAX_PRICE or price < MIN_PRICE:
            continue
        if beds < MIN_BEDS or baths < MIN_BATHS:
            continue
        matched.append(home)

    print(f"  Matched after filter: {len(matched)}", flush=True)
    total_matched += len(matched)

    for i, home in enumerate(matched):
        street   = (home.get("streetLine") or {}).get("value", "N/A")
        city_val = home.get("city", "N/A")
        state    = home.get("state", "N/A")
        zip_code = home.get("zip", "N/A")
        price    = (home.get("price") or {}).get("value", 0)
        beds     = home.get("beds", "?")
        baths    = home.get("baths", "?")
        sqft     = (home.get("sqFt") or {}).get("value", "?")
        status   = home.get("mlsStatus", "?")
        mls      = (home.get("mlsId") or {}).get("value", "?")
        url_path = home.get("url", "")
        listing_url = f"https://www.redfin.com{url_path}"

        print(f"\n  [{i+1}] {street}, {city_val}, {state} {zip_code}", flush=True)
        print(f"       ${price:,} | {beds}bd {baths}ba | {sqft} sqft | {status}", flush=True)
        print(f"       MLS: {mls}", flush=True)
        print(f"       URL: {listing_url}", flush=True)

    time.sleep(2)

print(f"\n{'='*50}", flush=True)
print(f"TOTAL MATCHED ACROSS ALL CITIES: {total_matched}", flush=True)
print("\nScript finished", flush=True)
