"""
FastAPI backend entrypoint.

Run with:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Exposes:
    POST /emails/fetch      - pull unread mail from Gmail, classify, store, route
    GET  /emails            - list/search/filter stored emails
    GET  /emails/{id}       - single email detail
    POST /classify          - ad-hoc classify subject/body text (no Gmail/DB)
    POST /route/{id}        - (re)route a stored email
    GET  /dashboard/stats   - aggregate counts for the dashboard
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import settings
from database.db import init_db, SessionLocal
from backend.routers import emails, classification, routing, dashboard
from backend.services.routing_service import process_unread_emails

# ---- Logging ----
os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)
logger = logging.getLogger("email_triage")

app = FastAPI(
    title="AI Email Classification & Routing System",
    description="Classifies incoming Gmail messages with BERT, scores sentiment/priority "
    "with VADER, and automatically routes them to the right department.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Streamlit runs on a different port; tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emails.router)
app.include_router(classification.router)
app.include_router(routing.router)
app.include_router(dashboard.router)

scheduler = BackgroundScheduler()


def _scheduled_poll():
    """Background job: periodically pull unread Gmail and process it."""
    db = SessionLocal()
    try:
        summary = process_unread_emails(db)
        if summary["new"]:
            logger.info(f"Scheduled poll processed {summary['new']} new emails: {summary}")
    except Exception as e:
        logger.error(f"Scheduled Gmail poll failed: {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        logger.info("Database tables ensured.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    # Only start the poller if Gmail credentials are actually present -
    # avoids crash-looping in environments that haven't set up OAuth yet.
    if os.path.exists(settings.gmail_credentials_path):
        scheduler.add_job(
            _scheduled_poll,
            "interval",
            seconds=settings.poll_interval_seconds,
            id="gmail_poll",
        )
        scheduler.start()
        logger.info(
            f"Background Gmail polling started (every {settings.poll_interval_seconds}s)."
        )
    else:
        logger.warning(
            "Gmail credentials not found - background polling disabled. "
            "Use POST /emails/fetch manually once credentials are configured."
        )


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()


@app.get("/")
def root():
    return {
        "service": "AI Email Classification & Routing System",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
