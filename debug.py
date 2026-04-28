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

CITIES = {
    "Hoffman Estates":   "29873",
    "Schaumburg":        "30313",
    "Bartlett":          "29132",
    "Carol Stream":      "29342",
    "Hanover Park":      "29827",
    "Elk Grove Village": "29598",
    "Streamwood":        "30526",
}

print("Script started", flush=True)

for city, region_id in CITIES.items():
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
    print(f"  First 500 chars:\n{r.text[:500]}", flush=True)

    # Find real header line
    lines = r.text.strip().splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if "ADDRESS" in line and "BEDS" in line:
            header_idx = i
            break

    if header_idx is None:
        print("  Could not find header row", flush=True)
        continue

    print(f"  Header found at line index: {header_idx}", flush=True)
    real_csv = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(real_csv))
    rows = list(reader)
    print(f"  Total rows: {len(rows)}", flush=True)
    if rows:
        print(f"  Column names: {list(rows[0].keys())}", flush=True)
    for i, row in enumerate(rows[:3]):
        print(f"  Row {i+1}: {dict(row)}", flush=True)

print("\nScript finished", flush=True)
