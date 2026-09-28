"""PySpark session factory for the Smart Water Analytics pipeline.

All Spark entry points (jobs, tests, CLI) build their session through
:meth:`build_spark` so configuration lives in one place.

Windows notes
-------------
* ``PYSPARK_PYTHON`` must point at a real interpreter (not the WindowsApps
  store stub) or Python workers fail to start.
* ``JAVA_HOME`` must point to a JDK 8/11/17 installation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TMP_SPARK_DIR = PROJECT_ROOT / "bigdata" / "tmp"


def _ensure_python_worker_env() -> None:
    """Windows helper: force workers to use the current interpreter."""
    if os.name == "nt" and sys.executable:
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def build_spark(app_name: str = "SmartWaterAnalytics",
                master: str | None = None,
                shuffle_partitions: int = 8,
                enable_hive: bool = False):
    """Create (or reuse) a SparkSession.

    Parameters
    ----------
    app_name : str
        Spark application name shown in the UI.
    master : str | None
        Override the master (``local[*]``, ``yarn``, ``spark://...``).
        Defaults to ``local[*]`` (configurable via ``SPARK_MASTER``).
    shuffle_partitions : int
        ``spark.sql.shuffle.partitions``. Small by default because this
        project targets a laptop-sized cluster; production values are
        documented in ``docs/big-data-workflow.md``.
    enable_hive : bool
        Enable the Hive catalog (optional HDFS/Hive deployments).
    """
    from pyspark.sql import SparkSession

    _ensure_python_worker_env()
    TMP_SPARK_DIR.mkdir(parents=True, exist_ok=True)

    master = master or os.environ.get("SPARK_MASTER", "local[*]")
    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.files.maxPartitionBytes", str(64 * 1024 * 1024))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.local.dir", str(TMP_SPARK_DIR))
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.python.worker.faulthandler.enabled", "true")
        .config("spark.sql.execution.pyspark.udf.faulthandler.enabled", "true")
    )
    if enable_hive:
        builder = builder.enableHiveSupport()
    return builder.getOrCreate()


def describe_cluster(spark) -> dict:
    """Return basic cluster facts (used by the /api/pipeline endpoints)."""
    sc = spark.sparkContext
    return {
        "app_name": sc.appName,
        "master": sc.master,
        "version": spark.version,
        "default_parallelism": sc.defaultParallelism,
        "spark_ui": f"http://localhost:{sc.uiWebUrl.split(':')[-1]}"
        if sc.uiWebUrl else None,
    }
