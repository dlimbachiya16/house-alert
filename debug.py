import json
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

print("Script started", flush=True)

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
        "num_homes": 350,
        "ord": "redfin-recommended-asc",
        "page_number": 1,
        "region_id": region_id,
        "region_type": 6,
        "status": 9,
        "uipt": "1,3",
        "v": 8,
        "sf": "1,2,3,5,6,7",  # include coming soon, active, pending
    }

    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    print(f"  HTTP {r.status_code} | size: {len(r.text)} chars", flush=True)

    text = r.text
    if text.startswith("{}&&"):
        text = text[4:]

    if "<html" in text[:200].lower():
        print("  BLOCKED — got HTML", flush=True)
        continue

    try:
        data = json.loads(text)
    except Exception as e:
        print(f"  JSON parse error: {e}", flush=True)
        print(f"  Raw: {r.text[:300]}", flush=True)
        continue

    homes = data.get("payload", {}).get("homes", [])
    print(f"  Homes returned: {len(homes)}", flush=True)

    for i, home in enumerate(homes[:5]):
        info = home.get("homeData", {})
        address_info = info.get("addressInfo", {})
        price_info   = info.get("priceInfo", {})
        beds  = info.get("beds", "?")
        baths = info.get("baths", "?")
        sqft  = info.get("sqFt", {}).get("value", "?")
        price = price_info.get("amount", "?")
        status = info.get("statusInfo", {}).get("displayStatus", "?")
        street = address_info.get("formattedStreetLine", "?")
        city_name = address_info.get("city", "?")
        state = address_info.get("state", "?")
        zipcode = address_info.get("zip", "?")
        listing_id = info.get("listingId", "?")
        url_path = info.get("url", "")

        print(f"\n  Listing {i+1}:", flush=True)
        print(f"    ADDRESS: {street}, {city_name}, {state} {zipcode}", flush=True)
        print(f"    PRICE:   ${price:,}" if isinstance(price, int) else f"    PRICE:   {price}", flush=True)
        print(f"    BEDS:    {beds}", flush=True)
        print(f"    BATHS:   {baths}", flush=True)
        print(f"    SQFT:    {sqft}", flush=True)
        print(f"    STATUS:  {status}", flush=True)
        print(f"    URL:     https://www.redfin.com{url_path}", flush=True)

print("\nScript finished", flush=True)
