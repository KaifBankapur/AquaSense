"""SQLAlchemy metadata store.

The analytical pipeline writes Parquet + JSON outputs; PostgreSQL (or the
SQLite fallback for laptops) stores *application metadata*: pipeline runs,
data-quality snapshots, and API-facing bookkeeping. This keeps the 
data-heavy path free of transactional overhead while demonstrating a real
metadata layer with indexes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (JSON, Column, DateTime, Float, Integer, MetaData,
                        String, create_engine)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)


class PipelineRun(Base):
    """One executed Spark pipeline run (metadata only)."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ran_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    master = Column(String(64), nullable=True)
    spark_version = Column(String(32), nullable=True)
    processed_records = Column(Integer, nullable=True)
    total_seconds = Column(Float, nullable=True)
    stage_times = Column(JSON, nullable=True)
    cluster = Column(JSON, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PipelineRun id={self.id} ran_at={self.ran_at}>"


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables (and indexes) on startup; safe to call repeatedly."""
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()