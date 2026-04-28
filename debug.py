"""
debug.py - v2
Skips autocomplete entirely. Uses hardcoded region IDs and tests CSV fetch directly.
"""

import csv
import io
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

# Hardcoded Redfin region IDs for Chicago suburbs
# region_type=6 means city-level
CITIES = {
    "Hoffman Estates": "29873",
    "Schaumburg":      "30313",
    "Bartlett":        "29132",
    "Carol Stream":    "29342",
    "Hanover Park":    "29827",
    "Elk Grove Village": "29598",
    "Streamwood":      "30526",
}

def fetch_csv(region_id, city):
    url = "https://www.redfin.com/stingray/api/gis-csv"
    params = {
        "al": 1,
        "market": "chicago",
        "min_beds": 4,
        "min_baths": 2,
        "max_price": 451000,
        "min_price": 0,
        "property_type": "1,3",
        "region_id": region_id,
        "region_type": 6,
        "status": 9,
        "uipt": "1,3",
        "v": 8,
        "num_homes": 350,
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    print(f"  HTTP status: {r.status_code}")
    print(f"  Response size: {len(r.text)} chars")
    print(f"  First 200 chars: {r.text[:200]}")
    return r.text

def main():
    for city, region_id in CITIES.items():
        print(f"\n{'='*50}")
        print(f"CITY: {city} | region_id: {region_id}")

        try:
            csv_text = fetch_csv(region_id, city)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        if "<html" in csv_text[:300].lower():
            print(f"  BLOCKED — got HTML instead of CSV")
            continue

        if not csv_text.strip():
            print(f"  EMPTY RESPONSE")
            continue

        lines = csv_text.strip().splitlines()
        print(f"  CSV lines: {len(lines)}")

        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        print(f"  Parsed rows: {len(rows)}")

        for i, row in enumerate(rows[:2]):
            print(f"\n  Listing {i+1}:")
            print(f"    MLS#:   {row.get('MLS#', 'N/A')}")
            print(f"    STATUS: {row.get('STATUS', 'N/A')}")
            print(f"    PRICE:  {row.get('PRICE', 'N/A')}")
            print(f"    BEDS:   {row.get('BEDS', 'N/A')}")
            print(f"    BATHS:  {row.get('BATHS', 'N/A')}")
            print(f"    SQFT:   {row.get('SQUARE FEET', 'N/A')}")
            print(f"    ADDR:   {row.get('ADDRESS', 'N/A')}")

if __name__ == "__main__":
    main()
