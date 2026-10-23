"""
Orchestrates the end-to-end pipeline:
  Gmail fetch -> dedup check -> classify -> persist to Postgres -> forward -> mark read

Each step is defensive: a failure in routing/forwarding does not lose the
classification result, it's just recorded with routing_status='failed'.
"""
import logging
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

from sqlalchemy.orm import Session

from backend.services.gmail_service import GmailService
from backend.services.classifier_service import classify_email
from database import crud
from config.settings import settings

logger = logging.getLogger(__name__)

_gmail_service = GmailService()


def _parse_timestamp(raw_date: str):
    try:
        return parsedate_to_datetime(raw_date) if raw_date else None
    except Exception:
        return None


def process_unread_emails(db: Session, max_results: int = 20) -> dict:
    """
    Fetch unread emails from Gmail, classify each new one, store it, and
    (if enabled) auto-route it to the right department mailbox.

    Returns a summary: {"fetched": n, "new": n, "duplicates": n, "routed": n, "failed": n}
    """
    summary = {"fetched": 0, "new": 0, "duplicates": 0, "routed": 0, "failed": 0}

    emails = _gmail_service.fetch_unread_emails(max_results=max_results)
    summary["fetched"] = len(emails)

    for email in emails:
        # Duplicate-processing guard
        if crud.email_exists(db, email["gmail_message_id"]):
            summary["duplicates"] += 1
            continue

        start = time.time()
        try:
            result = classify_email(email["subject"], email["body"])
        except Exception as e:
            logger.error(f"Classification failed for {email['gmail_message_id']}: {e}")
            continue

        processing_time_ms = int((time.time() - start) * 1000)

        record_data = {
            "gmail_message_id": email["gmail_message_id"],
            "thread_id": email["thread_id"],
            "sender": email["sender"],
            "receiver": email["receiver"],
            "subject": email["subject"],
            "body": email["body"],
            "has_attachments": email["has_attachments"],
            "attachment_names": email["attachment_names"],
            "received_at": _parse_timestamp(email["timestamp"]),
            "predicted_category": result["category"],
            "predicted_department": result["department_name"],
            "department_email": result["department_email"],
            "confidence": result["confidence"],
            "sentiment_label": result["sentiment_label"],
            "sentiment_score": result["sentiment_score"],
            "urgency_level": result["urgency_level"],
            "priority": result["priority"],
            "routing_status": "pending",
            "processing_time_ms": processing_time_ms,
        }

        record = crud.create_email_record(db, record_data)
        summary["new"] += 1

        if settings.auto_routing_enabled:
            ok = route_email(db, record.id)
            if ok:
                summary["routed"] += 1
            else:
                summary["failed"] += 1

        # Mark read in Gmail regardless of routing outcome, so we don't reprocess it
        try:
            _gmail_service.mark_as_read(email["gmail_message_id"])
        except Exception as e:
            logger.warning(f"Could not mark {email['gmail_message_id']} as read: {e}")

    return summary


def route_email(db: Session, email_id: int) -> bool:
    """Forward a single stored email to its predicted department mailbox."""
    record = crud.get_email(db, email_id)
    if not record:
        return False

    success, error = _gmail_service.forward_email(
        original_subject=record.subject or "",
        original_body=record.body or "",
        original_sender=record.sender or "",
        to_address=record.department_email,
        department_name=record.predicted_department,
    )

    if success:
        crud.update_routing_status(db, email_id, status="routed")
    else:
        crud.update_routing_status(db, email_id, status="failed", error=error)

    return success
