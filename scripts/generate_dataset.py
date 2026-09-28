"""
SMART WATER CONSUMPTION ANALYTICS
=================================
Synthetic water-consumption dataset generator.

Generates realistic, *hourly per-property (household meter)* water usage
records with defensible domain patterns:

  * higher consumption in the morning (06-09) and evening (18-21)
  * lower consumption at night
  * weekend profiles differing from weekdays
  * temperature drives consumption up (hotter => more water used)
  * rainfall suppresses outdoor / incidental usage
  * industrial & commercial properties consume more than residential
  * distinct building-type & zone profiles
  * occasional abnormal spikes (meter faults / events)
  * occasional leakage / wastage events
  * deterministic seeding for reproducible experiments

The generator is deliberately NOT "completely random" data: every row is a
function of profile parameters + time-of-day + weather + random noise.

Usage
-----
    python scripts/generate_dataset.py --rows 100000
    python scripts/generate_dataset.py --rows 1000000 --months 12
    python scripts/generate_dataset.py --households 600 --months 12 --seed 42

Output
------
    bigdata/data/raw/consumption_hourly.csv        (parquet-compatible CSV)
    bigdata/data/raw/meta_areas.json               (area roster / metadata)
    bigdata/data/raw/generation_report.json        (actual counts produced)
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "bigdata" / "data" / "raw"

# ---------------------------------------------------------------------------
# Static reference metadata (synthetic, demo-only — NOT real government data)
# ---------------------------------------------------------------------------

AREAS: list[dict] = [
    {"area_id": "A1",  "area_name": "Hubballi Central", "zone": "Central",   "population": 125400, "industrial_factor": 1.30, "base_per_capita_l": 150},
    {"area_id": "A2",  "area_name": "Vidyanagar",       "zone": "East",      "population":  86400, "industrial_factor": 1.15, "base_per_capita_l": 140},
    {"area_id": "A3",  "area_name": "Gokul Road",       "zone": "South",     "population":  71200, "industrial_factor": 1.10, "base_per_capita_l": 135},
    {"area_id": "A4",  "area_name": "Keshwapur",        "zone": "West",      "population":  58200, "industrial_factor": 1.05, "base_per_capita_l": 132},
    {"area_id": "A5",  "area_name": "Unkal",            "zone": "North-East", "population":  49300, "industrial_factor": 1.00, "base_per_capita_l": 128},
    {"area_id": "A6",  "area_name": "Old Hubballi",     "zone": "Central",   "population": 112800, "industrial_factor": 1.08, "base_per_capita_l": 138},
    {"area_id": "A7",  "area_name": "Dharwad Central",  "zone": "Central",   "population":  95600, "industrial_factor": 1.12, "base_per_capita_l": 142},
    {"area_id": "A8",  "area_name": "Navanagar",        "zone": "South",     "population":  68400, "industrial_factor": 1.25, "base_per_capita_l": 148},
    {"area_id": "A9",  "area_name": "Jubilee Circle",   "zone": "West",      "population":  42100, "industrial_factor": 1.02, "base_per_capita_l": 130},
    {"area_id": "A10", "area_name": "Industrial Area",  "zone": "Industrial","population":  18900, "industrial_factor": 2.20, "base_per_capita_l": 175},
]

BUILDING_TYPES = [  # weight, min_members, max_members, profile multiplier
    ("residential_flat",    0.34, 2, 5, 0.85),
    ("residential_house",   0.42, 3, 7, 1.00),
    ("commercial",          0.13, 1, 4, 1.55),
    ("industrial",          0.05, 2, 6, 2.40),
    ("institutional",       0.06, 2, 8, 1.35),
]

# Standard 24h diurnal profile as *percent* of daily volume per hour (sums to 100).
# Morning peak 06-09, evening peak 18-21, night trough, midday shoulder.
BASE_HOURLY_SHAPE_PCT: list[float] = [
    1.5, 1.2, 1.0, 0.9, 1.1, 1.7,                  # 00-05 night trough
    6.0, 6.4, 6.0, 4.7,                            # 06-09 morning peak
    3.8, 3.4, 3.6, 3.8, 4.0, 4.2, 4.7, 5.6,        # 10-17 afternoon shoulder
    7.3, 8.1, 7.7, 6.0, 4.3, 3.0,                  # 18-23 evening peak
]
BASE_HOURLY_SHAPE = [p / 100.0 for p in BASE_HOURLY_SHAPE_PCT]
_shape_total = sum(BASE_HOURLY_SHAPE)
assert abs(_shape_total - 1.0) < 1e-9, (
    f"hourly shape must sum to 1, got {_shape_total}"
)

WEEKEND_FACTOR = {"mon": 0.98, "tue": 0.96, "wed": 0.97, "thu": 0.98,
                  "fri": 1.00, "sat": 1.10, "sun": 1.14}
MONTHLY_FACTOR = {1: 0.86, 2: 0.88, 3: 0.95, 4: 1.12, 5: 1.22, 6: 1.28,
                  7: 0.94, 8: 0.90, 9: 0.96, 10: 1.02, 11: 0.94, 12: 0.90}
RAIN_SUPPRESSION_PER_MM = 0.018   # per mm of rain in the hour
TEMP_BASE = 27.0                  # consumption scales with |temperature| delta

METER_STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "SUSPECT", "FAULTY"]
NAME_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# ---------------------------------------------------------------------------
# Household profile
# ---------------------------------------------------------------------------


@dataclass
class HouseholdProfile:
    household_id: str
    area_id: str
    area_name: str
    zone: str
    building_type: str
    population: int
    daily_base_l: float          # litres / day reference volume
    peak_time_shift_h: float     # shift diurnal curve (lifestyle differences)
    leak_prone: float            # 0..1 probability of a leakage window
    spike_prone: float           # 0..1 probability of an anomalous spike
    supply_overhead: float       # typical non-consumed supply overhead (0..1)
    meter_bias: float            # meter under/over-report factor


def _weighted_choice(rng: random.Random, options: list[tuple]) -> object:
    total = sum(opt[-2] if isinstance(opt[-2], (int, float)) else 1 for opt in options)
    r = rng.uniform(0, total)
    acc = 0.0
    for opt in options:
        acc += opt[-2]
        if r <= acc:
            return opt
    return options[-1]


def _roll_households(rng: random.Random, count: int) -> list[HouseholdProfile]:
    """Distribute `count` households across areas proportional to population."""
    profiles: list[HouseholdProfile] = []
    total_pop = sum(a["population"] for a in AREAS)
    n_areas = len(AREAS)
    idx = 0
    for area_i, area in enumerate(AREAS):
        share = area["population"] / total_pop
        n = max(1, round(count * share))
        # last area absorbs the rounding remainder so the total is exact;
        # compare AREA indices (area_i), not the household counter (idx)
        n = n if area_i < n_areas - 1 else count - len(profiles)
        for _ in range(n):
            btype, _, lo, hi, mult = _weighted_choice(rng, BUILDING_TYPES)
            members = rng.randint(lo, hi)
            per_capita = area["base_per_capita_l"] * area["industrial_factor"]
            daily = per_capita * members * mult * rng.uniform(0.85, 1.18)
            profiles.append(HouseholdProfile(
                household_id=f"H{idx:05d}",
                area_id=area["area_id"],
                area_name=area["area_name"],
                zone=area["zone"],
                building_type=btype,
                population=members,
                daily_base_l=round(daily, 2),
                peak_time_shift_h=rng.normalvariate(0, 0.35),
                leak_prone=rng.uniform(0.0, 0.10),
                spike_prone=rng.uniform(0.0, 0.12),
                supply_overhead=rng.uniform(0.02, 0.07),
                meter_bias=rng.normalvariate(1.0, 0.02),
            ))
            idx += 1
    return profiles


def _weather_for(dt: datetime, rng: random.Random, seed: int) -> tuple[float, float]:
    """Annual temperature (mean ± seasonal wave) + rainfall model for Hubli-Dharwad."""
    t_mean = 25.8 + 4.2 * math.sin(2 * math.pi * (dt.timetuple().tm_yday - 100) / 365.0)
    temp = t_mean + rng.normalvariate(0, 2.2)
    month = dt.month
    rain_chance = {1: 0.02, 2: 0.02, 3: 0.03, 4: 0.10, 5: 0.18, 6: 0.55,
                   7: 0.80, 8: 0.70, 9: 0.48, 10: 0.22, 11: 0.05, 12: 0.02}[month]
    rain = 0.0
    if rng.random() < rain_chance:
        rain = rng.expovariate(1 / 6.0)  # mm in the hour
        rain = min(rain, 42.0)
    return max(12.0, min(44.0, temp)), round(rain, 2)


def _hour_factor(hour: int, shift_h: float) -> float:
    """Diurnal multiplier for a household with the given lifestyle shift."""
    pos = (hour + shift_h) % 24
    i = int(pos)
    frac = pos - i
    lo = BASE_HOURLY_SHAPE[i % 24]
    hi = BASE_HOURLY_SHAPE[(i + 1) % 24]
    return lo * (1 - frac) + hi * frac


def _generate_rows(rng: random.Random, households: list[HouseholdProfile],
                   start: date, end: date) -> int:
    """Emit hourly records for every household in [start, end]. Returns count."""
    path = RAW_DIR / "consumption_hourly.csv"
    day = start
    n_days = (end - start).days + 1
    total_rows = len(households) * n_days * 24
    reported = 0

    with path.open("w", newline="", encoding="utf-8") as fh:
        header = ("timestamp,date,hour,day_of_week,weekday,month,year,area_id,area_name,"
                  "zone,household_id,building_type,population,supplied_water_liters,"
                  "consumed_water_liters,wastage_liters,temperature_c,rainfall_mm,"
                  "pressure_bar,meter_status")
        fh.write(header + "\n")
        for d_idx in range(n_days):
            weekday = NAME_DAYS[day.weekday()]
            wd_factor = WEEKEND_FACTOR[weekday]
            month = day.month
            m_factor = MONTHLY_FACTOR[month]
            for hh in range(24):
                dt = datetime.combine(day, datetime.min.time()).replace(hour=hh)
                temp, rain = _weather_for(dt, rng, 0)
                hf = _hour_factor(hh, 0.0)
                for hp in households:
                    # --- per-property daily volume for this day -----------------
                    daily = hp.daily_base_l
                    daily *= wd_factor * m_factor
                    daily *= 1.0 + (temp - TEMP_BASE) * 0.011
                    daily *= max(0.55, 1.0 - RAIN_SUPPRESSION_PER_MM * rain)
                    hour_factor = _hour_factor(hh, hp.peak_time_shift_h)

                    consumed = daily * hour_factor
                    consumed *= hp.meter_bias * rng.uniform(0.93, 1.07)

                    # --- leakage window (multi-hour event) ----------------------
                    is_leak_window = False
                    leak_on_day = rng.random() < hp.leak_prone / 30.0  # a few / month
                    if leak_on_day and 0 <= hh <= 22:
                        is_leak_window = True

                    # --- abnormal consumption spike -----------------------------
                    spike = 1.0
                    if rng.random() < hp.spike_prone / (30.0 * 24.0):
                        spike = rng.uniform(2.2, 5.0)

                    if is_leak_window:
                        deficit = rng.uniform(0.08, 0.25)
                        supplied = consumed * (1 + hp.supply_overhead + deficit)
                        consumed *= 0.98
                    else:
                        supplied = consumed * (1 + hp.supply_overhead)

                    supplied *= spike * rng.uniform(0.97, 1.03)
                    consumed *= spike
                    consumed = max(0.0, round(consumed, 1))
                    supplied = max(consumed, round(supplied, 1))
                    wastage = supplied - consumed

                    pressure = rng.normalvariate(2.8, 0.22)
                    meter_status = rng.choice(METER_STATUSES)
                    if hp.building_type == "industrial":
                        pressure *= rng.uniform(0.9, 1.1)

                    row = [
                        dt.isoformat(timespec="seconds"), dt.date().isoformat(), dt.hour,
                        dt.weekday(), weekday, month, dt.year,
                        hp.area_id, hp.area_name, hp.zone,
                        hp.household_id, hp.building_type, hp.population,
                        round(supplied, 1), consumed, round(wastage, 1),
                        round(temp, 1), rain, round(pressure, 2), meter_status,
                    ]
                    fh.write(",".join(map(str, row)) + "\n")
                    reported += 1
            day += timedelta(days=1)
    return reported


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic water consumption data")
    ap.add_argument("--rows", type=int, default=100_000,
                    help="target number of rows (household count is derived unless "
                         "--households is given)")
    ap.add_argument("--months", type=int, default=12, help="number of months")
    ap.add_argument("--households", type=int, default=None,
                    help="explicit household count (overrides --rows derivation)")
    ap.add_argument("--seed", type=int, default=42, help="random seed")
    ap.add_argument("--start", default=None, help="start date YYYY-MM-DD")
    args = ap.parse_args()

    rng = random.Random(args.seed)

    days_in_month = 30.44
    hour_count = max(24, round(args.months * days_in_month * 24))
    if args.households is not None:
        households_n = args.households
    else:
        households_n = max(40, round(args.rows / hour_count))
        households_n = min(households_n, 1200)

    end_dt = datetime.now().date()
    n_days = max(1, round(args.months * days_in_month))
    start = end_dt - timedelta(days=n_days - 1)
    end = end_dt

    if args.start:
        start = date.fromisoformat(args.start)
        end = start + timedelta(days=n_days - 1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    households = _roll_households(rng, households_n)
    written = _generate_rows(rng, households, start, end)
    elapsed = time.perf_counter() - t0

    report = {
        "generator_version": "1.0",
        "seed": args.seed,
        "target_rows": args.rows,
        "households": households_n,
        "months": args.months,
        "date_range": [start.isoformat(), end.isoformat()],
        "rows_written": written,
        "columns": 20,
        "file": str(RAW_DIR / "consumption_hourly.csv"),
        "generation_seconds": round(elapsed, 2),
        "synthetic_demo_data": True,
        "note": "Entirely synthetic demo data. No real government records.",
    }
    (RAW_DIR / "generation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    (RAW_DIR / "meta_areas.json").write_text(
        json.dumps({"areas": AREAS, "synthetic_demo_data": True}, indent=2),
        encoding="utf-8")

    print(f"[generate] wrote {written:,} rows -> {RAW_DIR / 'consumption_hourly.csv'}")
    print(f"[generate] households={households_n} span={start}..{end} "
          f"time={elapsed:.2f}s")
    print(f"[generate] report -> {RAW_DIR / 'generation_report.json'}")


if __name__ == "__main__":
    main()