"""Spark job entry points (spark-submit friendly).

Each job runs one stage so you can demonstrate individual Spark programs:
    spark-submit bigdata/jobs/run_analytics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bigdata.spark.context import build_spark          # noqa: E402
from bigdata.spark.common import ensure_dirs            # noqa: E402
from bigdata.spark.preprocessing.preprocess import read_clean  # noqa: E402
from bigdata.spark.analytics import (totals, areas, peaks,  # noqa: E402
                                     wastage, households, timeseries)
from bigdata.spark.anomaly_detection import detect      # noqa: E402
from bigdata.spark.forecasting import forecast          # noqa: E402

STAGES = {
    "totals": totals.run,
    "areas": areas.run,
    "peaks": peaks.run,
    "wastage": wastage.run,
    "households": households.run,
    "timeseries": timeseries.run,
    "anomalies": detect.run,
    "forecast": forecast.run,
}


def main() -> None:
    ensure_dirs()
    stage = sys.argv[1] if len(sys.argv) > 1 else "totals"
    if stage not in STAGES:
        print("valid stages:", ", ".join(STAGES))
        raise SystemExit(2)
    spark = build_spark(app_name=f"SmartWater-{stage}")
    try:
        clean = read_clean(spark)
        result = STAGES[stage](spark, clean)
        print(f"[job:{stage}] ok — keys: {list(result)[:8]}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()