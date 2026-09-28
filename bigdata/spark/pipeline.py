"""Smart Water Analytics — full PySpark pipeline.

Stages
------
1. ingestion          load raw CSV
2. preprocessing      clean, dedupe, enrich, write partitioned Parquet
3. quality            data-quality report
4. analytics A-H      totals, areas, peaks, wastage, households, timeseries,
                      anomalies, forecast
5. publish            write pipeline_meta.json for the API layer

Runs::

    python -m bigdata.spark.pipeline
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from .context import build_spark, describe_cluster
from .common import (ANALYTICS_OUTPUT_DIR, OUTPUT_DIR, ensure_dirs,
                     load_area_meta)
from .ingestion.ingest import load_raw
from .preprocessing.preprocess import preprocess, CleaningStats
from .preprocessing.quality import build_quality_report
from .analytics import (totals, areas, peaks, wastage, households, timeseries)
from .anomaly_detection import detect
from .forecasting import forecast

PIPELINE_META = OUTPUT_DIR / "pipeline_meta.json"


class Pipeline:
    """Sequential Spark job runner with stage timing."""

    def __init__(self, spark, raw_csv: str | None = None) -> None:
        self.spark = spark
        self.raw_csv = raw_csv
        self.stage_times: dict[str, float] = {}
        self.clean_df = None

    def _stage(self, name: str, fn, *args):
        t0 = time.perf_counter()
        out = fn(self.spark, *args)
        self.stage_times[name] = time.perf_counter() - t0
        print(f"[pipeline] {name:>14s}  {self.stage_times[name]:7.2f}s")
        return out

    def run(self) -> dict:
        print("[pipeline] Spark session:", describe_cluster(self.spark))

        raw = self._stage("ingestion", load_raw, self.raw_csv) \
            if self.raw_csv else load_raw(self.spark)
        stats = CleaningStats()
        self.clean_df = self._stage("preprocessing", preprocess, raw, stats)
        self._stage("quality", build_quality_report, self.clean_df, stats)
        self._stage("analytics.totals", totals.run, self.clean_df)
        self._stage("analytics.areas", areas.run, self.clean_df)
        self._stage("analytics.peaks", peaks.run, self.clean_df)
        self._stage("analytics.wastage", wastage.run, self.clean_df)
        self._stage("analytics.households", households.run, self.clean_df)
        self._stage("analytics.timeseries", timeseries.run, self.clean_df)
        self._stage("anomaly.detection", detect.run, self.clean_df)
        self._stage("forecasting", forecast.run, self.clean_df)

        meta = {
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cluster": describe_cluster(self.spark),
            "stage_times_seconds": self.stage_times,
            "total_seconds": round(sum(self.stage_times.values()), 2),
            "processed_records": int(self.clean_df.count()),
            "areas": int(self.clean_df.select("area_id").distinct().count()),
            "outputs": {
                "clean_parquet": str(Path("bigdata/data/processed/consumption_clean")),
                "analytics": str(ANALYTICS_OUTPUT_DIR),
                "analytics_files": sorted(p.name for p in ANALYTICS_OUTPUT_DIR.glob("*.json")),
            },
        }
        (PIPELINE_META).write_text(
            json.dumps(meta, indent=2, default=str), encoding="utf-8")
        print("[pipeline] meta ->", PIPELINE_META)
        return meta


def main() -> None:
    ensure_dirs()
    spark = build_spark(app_name="SmartWaterPipeline")
    try:
        meta = Pipeline(spark).run()
        print(json.dumps(meta, indent=2, default=str))
    except Exception:  # noqa: BLE001 - surface as clean failure
        print("[pipeline] FAILED")
        traceback.print_exc()
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()