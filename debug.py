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
    "Hoffman Estates, IL",
    "Schaumburg, IL",
    "Bartlett, IL",
    "Carol Stream, IL",
    "Hanover Park, IL",
    "Elk Grove Village, IL",
    "Streamwood, IL",
]

for city in CITIES:
    url = "https://www.redfin.com/stingray/do/location-autocomplete"
    params = {
        "location": city,
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
    print(f"\n=== {city} ===")
    for section in data.get("payload", {}).get("sections", []):
        for row in section.get("rows", []):
            print(f"  type={row.get('type')}  id={row.get('id')}  name={row.get('name')}")
