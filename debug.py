"""
debug.py - v3
Fixes: blank first row, client-side filtering, prints ALL column names so we know exact headers.
Also tests region_type=2 vs region_type=6 to see which returns more results.
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

CITIES = {
    "Hoffman Estates":  "29873",
    "Schaumburg":       "30313",
    "Bartlett":         "29132",
    "Carol Stream":     "29342",
    "Hanover Park":     "29827",
    "Elk Grove Village":"29598",
    "Streamwood":       "30526",
}

def fetch_csv(region_id, region_type=6):
    url = "https://www.redfin.com/stingray/api/gis-csv"
    params = {
        "al": 1,
        "market": "chicago",
        "num_homes": 350,
        "ord": "redfin-recommended-asc",
        "page_number": 1,
        "region_id": region_id,
        "region_type": region_type,
        "status": 9,
        "uipt": "1,3",
        "v": 8,
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    return r.text

def parse_csv(csv_text):
    """Redfin CSVs have a blank/disclaimer first row — skip lines until we hit the real header."""
    lines = csv_text.strip().splitlines()
    # Find the line that contains 'ADDRESS' — that's the real header
    header_idx = None
    for i, line in enumerate(lines):
        if "ADDRESS" in line and "BEDS" in line:
            header_idx = i
            break
    if header_idx is None:
        return [], []
    real_csv = "\n".joi
