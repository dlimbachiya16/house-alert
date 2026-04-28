# ─────────────────────────────────────────────
#  SEARCH FILTERS  — edit these to your liking
# ─────────────────────────────────────────────

CITIES = [
    "Hoffman Estates",
    "Schaumburg",
    "Bartlett",
    "Carol Stream",
    "Hanover Park",
    "Elk Grove Village",
    "Streamwood",
]

MIN_BEDS = 4
MIN_BATHS = 2
MAX_PRICE = 451_000
MIN_PRICE = 0  # set higher if you want to exclude cheap listings

# Redfin property type codes (comma-separated string)
# 1=house, 2=condo, 3=townhouse, 4=multi-family, 5=land, 6=other, 8=mobile
PROPERTY_TYPES = "1,3"  # single-family + townhouse

# State (used to build Redfin URLs)
STATE = "IL"

# ─────────────────────────────────────────────
#  STORAGE
# ─────────────────────────────────────────────
SEEN_FILE = "seen_listings.json"

# ─────────────────────────────────────────────
#  STATUSES to watch for changes
# ─────────────────────────────────────────────
ACTIVE_STATUSES   = {"Active", "Coming Soon"}
PENDING_STATUSES  = {"Pending", "Contingent", "Under Contract"}
SOLD_STATUSES     = {"Sold", "Closed"}
