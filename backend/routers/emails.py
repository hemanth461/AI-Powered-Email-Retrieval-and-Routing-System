"""
Endpoints for fetching emails from Gmail and browsing/searching stored records.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.db import get_db
from database import crud
from backend.services.routing_service import process_unread_emails, simulate_inbound_emails
from backend.schemas import (
    FetchEmailsResponse,
    EmailListResponse,
    EmailRecordResponse,
)

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.post("/simulate", response_model=FetchEmailsResponse)
def simulate_emails(count: int = 5, db: Session = Depends(get_db)):
    """Simulates realistic inbound customer emails and routes them into the database."""
    return simulate_inbound_emails(db, count=min(count, 5))


@router.post("/fetch", response_model=FetchEmailsResponse)
def fetch_emails(max_results: int = 20, db: Session = Depends(get_db)):
    """
    Fetch unread emails from the monitored Gmail inbox, classify each new one,
    persist it, and (if AUTO_ROUTING_ENABLED) forward it to the right department.
    """
    try:
        summary = process_unread_emails(db, max_results=max_results)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gmail fetch failed: {e}")
    return summary


@router.get("", response_model=EmailListResponse)
def list_emails(
    department: str | None = None,
    priority: str | None = None,
    routing_status: str | None = None,
    search: str | None = Query(None, description="Search subject, body, or sender"),
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    results, total = crud.list_emails(
        db,
        department=department,
        priority=priority,
        routing_status=routing_status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "results": results}


@router.get("/{email_id}", response_model=EmailRecordResponse)
def get_email(email_id: int, db: Session = Depends(get_db)):
    record = crud.get_email(db, email_id)
    if not record:
        raise HTTPException(status_code=404, detail="Email not found")
    return record
