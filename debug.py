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

MIN_BEDS  = 4
MIN_BATHS = 2
MAX_PRICE = 451000

print("Script started", flush=True)

for city, region_id in CITY_REGION_IDS.items():
    print(f"\n{'='*50}", flush=True)
    print(f"CITY: {city} | region_id: {region_id}", flush=True)

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
    print(f"  HTTP {r.status_code} | size: {len(r.text)} chars", flush=True)

    if "<html" in r.text[:300].lower():
        print("  BLOCKED — got HTML", flush=True)
        continue

    lines = r.text.strip().splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if "ADDRESS" in line and "BEDS" in line:
            header_idx = i
            break

    if header_idx is None:
        print("  No header row found", flush=True)
        continue

    real_csv = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(real_csv))
    rows = list(reader)
    print(f"  Total rows: {len(rows)}", flush=True)

    # Client-side filter
    filtered = []
    for row in rows:
        try:
            if "accordance" in (row.get("SALE TYPE") or "").lower():
                continue
            if not row.get("ADDRESS") and not row.get("MLS#"):
                continue
            state = (row.get("STATE OR PROVINCE") or "").strip().upper()
            price = int(float((row.get("PRICE") or "0").replace("$","").replace(",","") or 0))
            beds  = float(row.get("BEDS") or 0)
            baths = float(row.get("BATHS") or 0)
            if state == "IL" and beds >= MIN_BEDS and baths >= MIN_BATHS and price <= MAX_PRICE:
                filtered.append(row)
        except Exception as e:
            print(f"  Filter error: {e}", flush=True)

    print(f"  IL listings matching filters: {len(filtered)}", flush=True)

    for i, row in enumerate(filtered):
        print(f"\n  Listing {i+1}:", flush=True)
        print(f"    ADDRESS: {row.get('ADDRESS')}, {row.get('CITY')}, {row.get('STATE OR PROVINCE')} {row.get('ZIP OR POSTAL CODE')}", flush=True)
        print(f"    PRICE:   {row.get('PRICE')}", flush=True)
        print(f"    BEDS:    {row.get('BEDS')}", flush=True)
        print(f"    BATHS:   {row.get('BATHS')}", flush=True)
        print(f"    SQFT:    {row.get('SQUARE FEET')}", flush=True)
        print(f"    STATUS:  {row.get('STATUS')}", flush=True)
        print(f"    MLS#:    {row.get('MLS#')}", flush=True)
        print(f"    URL:     {row.get(URL_COL, '')[:80]}", flush=True)

print("\nScript finished", flush=True)
