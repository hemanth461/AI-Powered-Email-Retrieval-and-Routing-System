"""
Dashboard aggregate endpoints: totals, pending/processed counts, department
breakdown, high-priority counts. Backs the Streamlit dashboard tab.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from database import crud
from backend.schemas import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def stats(db: Session = Depends(get_db)):
    return crud.get_dashboard_stats(db)
