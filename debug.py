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

    for i, row in enumerate(rows):
        # Skip the MLS disclaimer row
        if "accordance" in (row.get("SALE TYPE") or "").lower():
            continue

        state = (row.get("STATE OR PROVINCE") or "").strip().upper()
        price_raw = (row.get("PRICE") or "0").replace("$","").replace(",","").strip()
        price = int(float(price_raw)) if price_raw else 0
        beds_raw  = row.get("BEDS") or "0"
        baths_raw = row.get("BATHS") or "0"
        beds  = float(beds_raw) if beds_raw else 0
        baths = float(baths_raw) if baths_raw else 0

        # Show why it fails filter
        reasons = []
        if state != "IL":        reasons.append(f"state={state}")
        if beds < MIN_BEDS:      reasons.append(f"beds={beds}")
        if baths < MIN_BATHS:    reasons.append(f"baths={baths}")
        if price > MAX_PRICE:    reasons.append(f"price=${price:,}")
        if price == 0:           reasons.append("price=0/missing")

        status = "PASS" if not reasons else f"FAIL ({', '.join(reasons)})"

        print(f"  Row {i+1}: {row.get('ADDRESS')}, {row.get('CITY')}, {state} | "
              f"${price:,} | {beds}bd {baths}ba | {row.get('STATUS')} | {status}", flush=True)

print("\nScript finished", flush=True)
