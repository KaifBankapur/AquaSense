"""Spark forecasting — H.

Method: seasonal linear regression (Spark ML) on the *daily* aggregated
consumption series.

Features
--------
* day index (0, 1, 2, …) — captures the long-term trend
* sin/cos of the 7-day weekly seasonality — captures weekly rhythm
* sin/cos of the 365-day yearly seasonality — captures seasonal demand

The Spark ML ``LinearRegression`` model is trained on the historical daily
totals and used to forecast ``H`` days ahead. Confidence intervals (`lower`,
`upper`) are derived from the model's residual standard deviation
(prediction ± 1.96 × σ_residual) and are clearly labelled as estimates.

The same series is also smoothed with a simple exponential moving average for
cross-checking. **Forecast values are always identified as predictions, never
as measured data.**
"""

from __future__ import annotations

import math

from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression

from ..common import ANALYTICS_OUTPUT_DIR, FORECAST_PARQUET_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "forecast.json"
HISTORY_DAYS = 120     # number of historical daily points to embed in the payload
HORIZONS = {"7d": 7, "30d": 30}


def _seasonal_features(day_index: float, period: int) -> tuple[float, float]:
    r = 2.0 * math.pi * day_index / period
    return math.cos(r), math.sin(r)


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Forecast next 7 and next 30 days from daily Spark aggregates."""
    daily = (
        clean.groupBy("date")
        .agg(F.sum("consumed_water_liters").alias("consumed"))
        .orderBy("date")
    )
    rows = daily.collect()
    if len(rows) < 14:
        raise RuntimeError(
            "Too little history for forecasting (need ≥ 14 days, "
            f"have {len(rows)}). Re-run the pipeline with a longer dataset.")

    dates = [str(r["date"]) for r in rows]
    consumed = [float(r["consumed"]) for r in rows]
    day_index = list(range(len(consumed)))

    # ---- build feature frame ------------------------------------------------
    feat_rows = []
    for i, (di, c) in enumerate(zip(day_index, consumed)):
        c7, s7 = _seasonal_features(di, 7)
        c365, s365 = _seasonal_features(di, 365)
        feat_rows.append((di, c7, s7, c365, s365, c))

    feats = spark.createDataFrame(feat_rows, ["day_index", "cos7", "sin7",
                                              "cos365", "sin365", "consumed"])
    assembler = VectorAssembler(
        inputCols=["day_index", "cos7", "sin7", "cos365", "sin365"],
        outputCol="features")
    feats = assembler.transform(feats)

    # ---- train Seasonal Linear Regression -----------------------------------
    lr = LinearRegression(featuresCol="features", labelCol="consumed")
    model = lr.fit(feats)
    fitted = model.transform(feats).select("consumed", "prediction").collect()
    residuals = [float(f["consumed"]) - float(f["prediction"]) for f in fitted]
    n = len(residuals)
    mse = sum(r * r for r in residuals) / max(1, n)
    mae = sum(abs(r) for r in residuals) / max(1, n)
    rmse = math.sqrt(mse)
    resid_std = rmse  # approx std of residuals

    # ---- history tail (embedded for charts) ----------------------------------
    tail = HISTORY_DAYS
    history = [
        {"date": d, "consumed": round(c, 2)}
        for d, c in zip(dates[-tail:], consumed[-tail:])
    ]

    # ---- exponential moving average (cross-check smooth) ----------------------
    alpha = 0.3
    ema_series: list[float] = []
    ema = consumed[0]
    for c in consumed:
        ema = alpha * c + (1 - alpha) * ema
        ema_series.append(ema)

    outputs = {}
    future_start = len(consumed)

    # ---- batch all future feature rows in one frame, transform once ----------
    from datetime import datetime, timedelta
    horizon_rows: list[list] = []
    meta: list[tuple[str, str]] = []          # (horizon_key, date)
    di = future_start - 1
    for key, h in HORIZONS.items():
        for k in range(1, h + 1):
            di += 1
            d = (datetime.strptime(dates[-1], "%Y-%m-%d")
                 + timedelta(days=k)).date().isoformat()
            c7, s7 = _seasonal_features(di, 7)
            c365, s365 = _seasonal_features(di, 365)
            horizon_rows.append([di, c7, s7, c365, s365])
            meta.append((key, d))

    horizon_df = spark.createDataFrame(
        horizon_rows, ["day_index", "cos7", "sin7", "cos365", "sin365"])
    pred_values = [
        float(r["prediction"])
        for r in model.transform(assembler.transform(horizon_df))
        .select("prediction").collect()
    ]

    outputs: dict[str, dict] = {
        key: {"horizon_days": h, "is_forecast": True, "points": []}
        for key, h in HORIZONS.items()
    }
    for (key, d), p in zip(meta, pred_values):
        outputs[key]["points"].append({
            "date": d, "predicted": round(p, 2),
            "lower": round(max(0.0, p - 1.96 * resid_std), 2),
            "upper": round(p + 1.96 * resid_std, 2),
        })

    result = {
        "method": "seasonal_linear_regression (Spark ML)",
        "features": ["day_index", "cos/sin(7d)", "cos/sin(365d)"],
        "trained_on_days": len(consumed),
        "history": history,
        "ema_history": [round(v, 2) for v in ema_series[-tail:]],
        "model_metrics": {
            "mse": round(mse, 2),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "residual_std": round(resid_std, 2),
            "intercept": round(float(model.intercept), 2),
        },
        "forecast_7d": outputs["7d"],
        "forecast_30d": outputs["30d"],
        "disclaimer": "Forecast values are model predictions, not measurements.",
    }

    # persist the full forecast frame as Parquet (analytical reuse)
    from datetime import datetime, timedelta
    frows = [
        {"date": d, "kind": "actual", "value": c, "lower": None, "upper": None}
        for d, c in zip(dates, consumed)
    ]
    for key in ("7d", "30d"):
        for p in outputs[key]["points"]:
            frows.append({"date": p["date"], "kind": "forecast",
                          "value": p["predicted"],
                          "lower": p["lower"], "upper": p["upper"]})
    spark.createDataFrame(frows).write.mode("overwrite").format("parquet") \
        .option("compression", "snappy").save(str(FORECAST_PARQUET_DIR))

    write_json(OUT_FILE, result)
    return result