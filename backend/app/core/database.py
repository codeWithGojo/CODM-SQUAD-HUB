"""SQLAlchemy engine and request-scoped session management."""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


def _engine_options(database_url: str) -> dict:
    if not database_url.startswith("sqlite"):
        return {"pool_pre_ping": True, "pool_recycle": 300}

    options: dict = {"connect_args": {"check_same_thread": False}}
    if ":memory:" in database_url:
        options["poolclass"] = StaticPool
    return options


engine = create_engine(settings.database_url, **_engine_options(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(Engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
