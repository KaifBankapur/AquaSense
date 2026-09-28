"""Static area master data (roster).

These are *area-level* metadata used by the Spark analytics stage so that
``areas.json`` reports the territory's reference population — not a roll-up of
the (small) set of sampled household meters. The CSV generator in
``scripts/generate_dataset.py`` keeps its own copy of the same roster so the
script stays runnable without a Spark installation; keep the two in sync.

``population`` is used downstream by the API/UI ("Population" stat per area).
"""

AREA_ROSTER: dict[str, dict] = {
    "A1":  {"name": "Hubballi Central", "zone": "Central",    "population": 125400},
    "A2":  {"name": "Vidyanagar",       "zone": "East",       "population":  86400},
    "A3":  {"name": "Gokul Road",       "zone": "South",      "population":  71200},
    "A4":  {"name": "Keshwapur",        "zone": "West",       "population":  58200},
    "A5":  {"name": "Unkal",            "zone": "North-East", "population":  49300},
    "A6":  {"name": "Old Hubballi",     "zone": "Central",    "population": 112800},
    "A7":  {"name": "Dharwad Central",  "zone": "Central",    "population":  95600},
    "A8":  {"name": "Navanagar",        "zone": "South",      "population":  68400},
    "A9":  {"name": "Jubilee Circle",   "zone": "West",       "population":  42100},
    "A10": {"name": "Industrial Area",  "zone": "Industrial", "population":  18900},
}