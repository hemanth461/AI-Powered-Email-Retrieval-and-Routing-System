"""
CRUD operations for EmailRecord, plus the aggregate queries used by the
dashboard (counts, department breakdown, high-priority list, search).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import EmailRecord


def email_exists(db: Session, gmail_message_id: str) -> bool:
    """Duplicate-processing guard: check by Gmail message ID before doing any work."""
    return (
        db.query(EmailRecord.id)
        .filter(EmailRecord.gmail_message_id == gmail_message_id)
        .first()
        is not None
    )


def create_email_record(db: Session, data: dict) -> EmailRecord:
    record = EmailRecord(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_routing_status(
    db: Session,
    email_id: int,
    status: str,
    error: Optional[str] = None,
):
    record = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not record:
        return None
    record.routing_status = status
    record.routing_error = error
    if status == "routed":
        record.routed_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


def get_email(db: Session, email_id: int) -> Optional[EmailRecord]:
    return db.query(EmailRecord).filter(EmailRecord.id == email_id).first()


def list_emails(
    db: Session,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    routing_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(EmailRecord)

    if department:
        query = query.filter(EmailRecord.predicted_department == department)
    if priority:
        query = query.filter(EmailRecord.priority == priority)
    if routing_status:
        query = query.filter(EmailRecord.routing_status == routing_status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (EmailRecord.subject.ilike(like))
            | (EmailRecord.body.ilike(like))
            | (EmailRecord.sender.ilike(like))
        )

    total = query.count()
    results = (
        query.order_by(EmailRecord.processed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return results, total


def get_dashboard_stats(db: Session) -> dict:
    total = db.query(func.count(EmailRecord.id)).scalar() or 0
    routed = (
        db.query(func.count(EmailRecord.id))
        .filter(EmailRecord.routing_status == "routed")
        .scalar()
        or 0
    )
    pending = (
        db.query(func.count(EmailRecord.id))
        .filter(EmailRecord.routing_status == "pending")
        .scalar()
        or 0
    )
    failed = (
        db.query(func.count(EmailRecord.id))
        .filter(EmailRecord.routing_status == "failed")
        .scalar()
        or 0
    )
    high_priority = (
        db.query(func.count(EmailRecord.id))
        .filter(EmailRecord.priority == "high")
        .scalar()
        or 0
    )

    dept_rows = (
        db.query(EmailRecord.predicted_department, func.count(EmailRecord.id))
        .group_by(EmailRecord.predicted_department)
        .all()
    )
    department_counts = {dept or "Unknown": count for dept, count in dept_rows}

    priority_rows = (
        db.query(EmailRecord.priority, func.count(EmailRecord.id))
        .group_by(EmailRecord.priority)
        .all()
    )
    priority_counts = {p or "unknown": count for p, count in priority_rows}

    return {
        "total_emails": total,
        "processed_emails": routed + failed,
        "pending_emails": pending,
        "high_priority_emails": high_priority,
        "department_counts": department_counts,
        "priority_counts": priority_counts,
    }
