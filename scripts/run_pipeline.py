"""
End-to-end runner for the AquaSense big-data pipeline.

    python scripts/run_pipeline.py                 # generate + run Spark
    python scripts/run_pipeline.py --skip-generate # only run Spark
    python scripts/run_pipeline.py --rows 1000000  # scale to millions
    python scripts/run_pipeline.py --households 600 --months 12

It generates the dataset if missing (or always, unless --skip-generate),
then launches the PySpark pipeline and writes pipeline_meta.json.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(cmd)}\n")
    subprocess.check_call(cmd, cwd=cwd)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the AquaSense Spark pipeline end-to-end")
    ap.add_argument("--rows", type=int, default=None, help="target dataset rows")
    ap.add_argument("--households", type=int, default=None)
    ap.add_argument("--months", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-generate", action="store_true",
                    help="reuse the existing CSV in bigdata/data/raw")
    ap.add_argument("--python", default="py -3.14",
                    help="interpreter used to run python calls (default: py -3.14)")
    args = ap.parse_args()

    raw = ROOT / "bigdata" / "data" / "raw" / "consumption_hourly.csv"

    if args.skip_generate:
        if not raw.exists():
            sys.exit(f"raw CSV missing: {raw} — drop --skip-generate to create it")
        print(f"[run] reusing existing dataset: {raw}")
    else:
        cmd = [*(args.python.split()), str(ROOT / "scripts" / "generate_dataset.py")]
        if args.rows:
            cmd += ["--rows", str(args.rows)]
        if args.households:
            cmd += ["--households", str(args.households)]
        if args.months:
            cmd += ["--months", str(args.months)]
        cmd += ["--seed", str(args.seed)]
        run(cmd, ROOT)

    t0 = time.perf_counter()
    run([*(args.python.split()), "-m", "bigdata.spark.pipeline"], ROOT)
    elapsed = time.perf_counter() - t0

    meta_path = ROOT / "bigdata" / "outputs" / "pipeline_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        print(f"\n[run] pipeline OK in {elapsed:.1f}s wall-clock; Spark reported "
              f"{meta['total_seconds']}s stage time")
        print(f"[run] records={meta['processed_records']:,} areas={meta['areas']}")
        print(f"[run] artifacts: {meta['outputs']['analytics']}")
    else:
        print("\n[run] pipeline finished but pipeline_meta.json not found!")


if __name__ == "__main__":
    main()