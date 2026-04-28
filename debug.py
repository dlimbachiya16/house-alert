"""
debug.py
Run this to see exactly what Redfin is returning.
Prints region IDs, raw CSV headers, and parsed listings.
"""

import csv
import io
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

CITIES = [
    "Hoffman Estates",
    "Schaumburg",
    "Bartlett",
    "Carol Stream",
    "Hanover Park",
    "Elk Grove Village",
    "Streamwood",
]

STATE = "IL"

def get_region_id(city):
    url = "https://www.redfin.com/stingray/do/location-autocomplete"
    params = {
        "location": f"{city}, {STATE}",
        "start": 0,
        "count": 10,
        "v": 2,
        "market": "chicago",
        "al": 1,
        "iss": "false",
        "ooa": "true",
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    text = r.text
    if text.startswith("{}&&"):
        text = text[4:]
    data = json.loads(text)

    print(f"\n--- Autocomplete response for {city} ---")
    sections = data.get("payload", {}).get("sections", [])
    for section in sections:
        for row in section.get("rows", []):
            print(f"  type={row.get('type')}  id={row.get('id')}  name={row.get('name')}")
            # Return first type=6 (city) or type=2 match
            if row.get("type") in ("2", "6", 2, 6):
                raw_id = row["id"]
                # id format examples: "city_29401" or "6_29401"
                region_id = raw_id.split("_")[-1]
                print(f"  => Using region_id: {region_id}")
                return region_id, raw_id

    print(f"  => No city match found for {city}")
    return None, None


def fetch_csv(region_id):
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
    return r.text


def main():
    for city in CITIES:
        print(f"\n{'='*50}")
        print(f"CITY: {city}")

        try:
            region_id, raw_id = get_region_id(city)
        except Exception as e:
            print(f"  ERROR getting region_id: {e}")
            continue

        if not region_id:
            continue

        try:
            csv_text = fetch_csv(region_id)
        except Exception as e:
            print(f"  ERROR fetching CSV: {e}")
            continue

        # Check if we got HTML (bot block)
        if "<html" in csv_text[:300].lower():
            print(f"  GOT HTML INSTEAD OF CSV — likely blocked")
            print(f"  First 300 chars: {csv_text[:300]}")
            continue

        # Print CSV headers
        lines = csv_text.strip().splitlines()
        print(f"  CSV lines returned: {len(lines)}")
        if lines:
            print(f"  Headers: {lines[0][:300]}")

        # Parse rows
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        print(f"  Parsed rows: {len(rows)}")

        for i, row in enumerate(rows[:3]):  # print first 3 listings
            print(f"\n  Listing {i+1}:")
            print(f"    MLS#:   {row.get('MLS#', 'N/A')}")
            print(f"    STATUS: {row.get('STATUS', 'N/A')}")
            print(f"    PRICE:  {row.get('PRICE', 'N/A')}")
            print(f"    BEDS:   {row.get('BEDS', 'N/A')}")
            print(f"    BATHS:  {row.get('BATHS', 'N/A')}")
            print(f"    SQFT:   {row.get('SQUARE FEET', 'N/A')}")
            print(f"    ADDR:   {row.get('ADDRESS', 'N/A')}")

        if len(rows) > 3:
            print(f"\n  ... and {len(rows) - 3} more listings")


if __name__ == "__main__":
    main()
