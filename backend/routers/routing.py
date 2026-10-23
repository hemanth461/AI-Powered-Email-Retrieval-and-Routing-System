"""
Manual routing endpoint — (re)forwards a specific stored email to its
department mailbox. Useful for retrying after a routing failure.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database import crud
from backend.services.routing_service import route_email
from backend.schemas import RouteResponse

router = APIRouter(prefix="/route", tags=["Routing"])


@router.post("/{email_id}", response_model=RouteResponse)
def route(email_id: int, db: Session = Depends(get_db)):
    record = crud.get_email(db, email_id)
    if not record:
        raise HTTPException(status_code=404, detail="Email not found")

    success = route_email(db, email_id)
    updated = crud.get_email(db, email_id)

    return {
        "email_id": email_id,
        "success": success,
        "routing_status": updated.routing_status,
    }
