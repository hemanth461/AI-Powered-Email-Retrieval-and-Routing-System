"""
Database engine + session management for PostgreSQL.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from database.models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db():
    """Create all tables if they don't already exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context-managed DB session: `with get_session() as session: ...`"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI dependency-injectable session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
