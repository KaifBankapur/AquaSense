"""Structured logging for the API service."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def _rich_timestamp(record: logging.LogRecord) -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    # keep uvicorn access logs at INFO
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)