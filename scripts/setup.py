"""
One-shot environment setup for AquaSense on Windows.

Checks / installs the pieces PySpark needs on this machine:

  * a JDK (17) at a known location, JAVA_HOME exported for the session
  * Hadoop binary helpers (winutils.exe / hadoop.dll) + HADOOP_HOME
  * all Python packages from requirements files

Usage:
    python scripts/setup.py --check     # print a report, do nothing
    python scripts/setup.py --install   # pip install + write .env defaults

The generated credentials/behaviour are documented in .env.example.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

KNOWN_JAVA = ROOT.parent / "kaifb"  # not used; see below
JAVA_CANDIDATES = [
    Path(os.environ.get("JAVA_HOME", "") or "."),
    Path("C:/Users/kaifb/AppData/Local/Programs/Temurin17/jdk-17.0.20.1+1"),
    *sorted(Path("C:/Program Files/Eclipse Adoptium").glob("jdk-17*"))
    if (Path("C:/Program Files/Eclipse Adoptium")).exists() else [],
]

HADOOP_CANDIDATES = [
    TOOLS / "hadoop",
    Path("C:/hadoop"),
]


def find_java() -> Path | None:
    for cand in JAVA_CANDIDATES:
        if cand and (cand / "bin" / "java.exe").exists():
            return cand
    # fall back to PATH
    java = shutil.which("java")
    if java:
        return Path(java).resolve().parent.parent
    return None


def find_hadoop() -> Path | None:
    for cand in HADOOP_CANDIDATES:
        if cand.exists() and (cand / "bin" / "winutils.exe").exists():
            return cand
    return None


def report() -> None:
    print("=== AquaSense environment report ===")
    print(f"python      : {sys.version.split()[0]} ({sys.executable})")
    j = find_java()
    print(f"java        : {j or 'NOT FOUND'}" + (f" ({os.environ.get('JAVA_HOME')})" if "JAVA_HOME" in os.environ else ""))
    h = find_hadoop()
    print(f"hadoop dir  : {h or 'NOT FOUND'}"
          + (f" (HADOOP_HOME={os.environ.get('HADOOP_HOME')})" if os.environ.get("HADOOP_HOME") else ""))
    try:
        import pyspark
        print(f"pyspark     : {pyspark.__version__}")
    except ImportError:
        print("pyspark     : NOT INSTALLED")
    try:
        import fastapi
        print(f"fastapi     : {fastapi.__version__}")
    except ImportError:
        print("fastapi     : NOT INSTALLED")
    for name, path in [("raw csv", ROOT / "bigdata/data/raw/consumption_hourly.csv"),
                       ("clean parquet", ROOT / "bigdata/data/processed/consumption_clean"),
                       ("analytics", ROOT / "bigdata/outputs/analytics"),
                       ("pipeline meta", ROOT / "bigdata/outputs/pipeline_meta.json")]:
        exists = path.exists()
        print(f"{name + ' ' * (16 - len(name))}: {'present' if exists else 'missing'}  {path}")
    print("=== end report ===")


def install() -> None:
    print("[setup] installing Python requirements…")
    for req in [ROOT / "requirements.txt", ROOT / "backend/requirements.txt",
                ROOT / "backend/requirements-dev.txt"]:
        if req.exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                   "-r", str(req)])
    j = find_java()
    h = find_hadoop()
    env_path = ROOT / ".env"
    existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    additions: list[str] = []
    if j and "JAVA_HOME" not in existing:
        additions.append(f"JAVA_HOME={j}")
    if h and "HADOOP_HOME" not in existing:
        additions.append(f"HADOOP_HOME={h}")
    if additions:
        with env_path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + "\n".join(additions) + "\n")
    print("[setup] done. Run `python scripts/run_pipeline.py` next.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--install", action="store_true")
    args = ap.parse_args()
    if args.install:
        install()
    report()


if __name__ == "__main__":
    main()