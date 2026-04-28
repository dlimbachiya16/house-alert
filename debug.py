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

print("Script started", flush=True)

# Just test ONE city
url = "https://www.redfin.com/stingray/api/gis"
params = {
    "al": 1,
    "market": "chicago",
    "min_beds": 4,
    "min_baths": 2,
    "max_price": 451000,
    "num_homes": 10,
    "page_number": 1,
    "region_id": "29487",
    "region_type": 6,
    "status": 9,
    "uipt": "1,3",
    "v": 8,
    "sf": "1,2,3,5,6,7",
}

r = requests.get(url, params=params, headers=HEADERS, timeout=20)
text = r.text
if text.startswith("{}&&"):
    text = text[4:]

data = json.loads(text)
homes = data.get("payload", {}).get("homes", [])
print(f"Homes returned: {len(homes)}", flush=True)

if homes:
    print("\n--- RAW FIRST HOME JSON ---", flush=True)
    print(json.dumps(homes[0], indent=2), flush=True)
    print("\n--- RAW SECOND HOME JSON ---", flush=True)
    if len(homes) > 1:
        print(json.dumps(homes[1], indent=2), flush=True)

print("\nScript finished", flush=True)
