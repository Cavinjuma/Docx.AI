from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Create a session factory configured for SQLite or PostgreSQL."""
    url = database_url or get_settings().database_url
    engine_kwargs = {"future": True}
    if url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        })

    engine = create_engine(url, **engine_kwargs)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def init_db(database_url: str | None = None) -> Engine:
    """Create tables for the current database URL."""
    url = database_url or get_settings().database_url
    engine_kwargs = {"future": True}
    if url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        })

    engine = create_engine(url, **engine_kwargs)
    Base.metadata.create_all(bind=engine)
    return engine
