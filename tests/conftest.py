"""Shared pytest fixtures for the AquaSense test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force the deterministic local assistant path regardless of any .env key.
os.environ.setdefault("AI_MODE", "local")