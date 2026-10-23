"""
Database engine + session management for PostgreSQL.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from database.models import Base

db_url = settings.database_url or ""
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(db_url, pool_pre_ping=True, future=True)
except Exception as e:
    print(f"Warning: Failed to create engine with {db_url}: {e}. Falling back to SQLite.")
    engine = create_engine("sqlite:///./email_triage.db", future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db():
    """Create all tables if they don't already exist. Safe to call on every startup."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Failed to create tables in database: {e}")


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
