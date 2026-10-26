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
from config.department_mapping import get_department_for_category
from database import crud
from database.models import EmailRecord
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
            logger.info(f"Auto-routed email ID {record.id}: {'success' if ok else 'failed'}")
            if ok:
                summary["routed"] += 1
            else:
                summary["failed"] += 1
        else:
            logger.info(f"Auto-routing skipped for email ID {record.id} (auto_routing_enabled=False)")

        # Mark read in Gmail regardless of routing outcome, so we don't reprocess it
        try:
            _gmail_service.mark_as_read(email["gmail_message_id"])
        except Exception as e:
            logger.warning(f"Could not mark {email['gmail_message_id']} as read: {e}")

    return summary


def route_email(db: Session, email_id: int) -> bool:
    """Forward a single stored email to its predicted department mailbox."""
    try:
        record = crud.get_email(db, email_id)
        if not record:
            return False

        to_addr = record.department_email
        if not to_addr or "@" not in str(to_addr):
            dept_info = get_department_for_category(record.predicted_category or "general")
            to_addr = dept_info.get("email", settings.dept_general_email)

        success, error = _gmail_service.forward_email(
            original_subject=record.subject or "",
            original_body=record.body or "",
            original_sender=record.sender or "",
            to_address=to_addr,
            department_name=record.predicted_department or "General",
        )

        if success:
            crud.update_routing_status(db, email_id, status="routed")
        else:
            crud.update_routing_status(db, email_id, status="failed", error=error)

        return success
    except Exception as e:
        logger.error(f"Error executing route_email for record {email_id}: {e}")
        try:
            crud.update_routing_status(db, email_id, status="failed", error=str(e))
        except Exception:
            pass
        return False


def route_all_pending(db: Session) -> dict:
    """Find and dispatch all unrouted (pending) emails in the database."""
    pending_records = db.query(EmailRecord).filter(EmailRecord.routing_status == "pending").all()
    routed = 0
    failed = 0
    for record in pending_records:
        ok = route_email(db, record.id)
        if ok:
            routed += 1
        else:
            failed += 1
    return {"total": len(pending_records), "routed": routed, "failed": failed}


SIMULATED_BATCH = [
    {
        "sender": "employee.sarah@company.com",
        "subject": "Request for Paid Time Off - Family Emergency",
        "body": "Hi HR team, I need to travel back to my hometown for an urgent family medical situation. I would like to request 3 days of casual time off starting tomorrow.",
    },
    {
        "sender": "developer.mike@company.com",
        "subject": "Laptop screen blue crash after system update",
        "body": "Hi IT team, my workstation laptop crashed with a blue screen error code 0x0000007E right after the firmware update. Need a technician or machine replacement.",
    },
    {
        "sender": "procurement@acme-global.org",
        "subject": "Price quote inquiry for 75 Enterprise user licenses",
        "body": "Hello Sales team, our department is assessing your platform for 75 team members. Could you provide a formal pricing quote and schedule a demo this Friday?",
    },
    {
        "sender": "billing.auditor@client-co.net",
        "subject": "Duplicate charge on Mastercard statement for Invoice 9901",
        "body": "Hi Accounts, our credit card shows two identical deductions of $499 on October 18 for invoice #9901. Please issue a refund credit for the duplicate transaction.",
    },
    {
        "sender": "user.alex@gmail.com",
        "subject": "Unable to log in to dashboard - reset password fails",
        "body": "Customer Support, I forgot my login credentials and the password reset link is throwing an error 500. Can you please assist in restoring account access?",
    },
]


def simulate_inbound_emails(db: Session, count: int = 5) -> dict:
    """
    Simulates a realistic batch of inbound business emails, runs neural classification,
    and records them into PostgreSQL. Ideal for cloud demonstrations when live Gmail
    OAuth is not yet linked.
    """
    import uuid
    summary = {"fetched": count, "new": 0, "duplicates": 0, "routed": 0, "failed": 0}
    items = SIMULATED_BATCH[:count]

    for item in items:
        msg_id = f"sim-{uuid.uuid4().hex[:10]}"
        start = time.time()
        result = classify_email(item["subject"], item["body"])
        proc_time = int((time.time() - start) * 1000)

        record_data = {
            "gmail_message_id": msg_id,
            "sender": item["sender"],
            "receiver": "inbox@company.com",
            "subject": item["subject"],
            "body": item["body"],
            "has_attachments": False,
            "received_at": datetime.utcnow(),
            "predicted_category": result["category"],
            "predicted_department": result["department_name"],
            "department_email": result["department_email"],
            "confidence": result["confidence"],
            "sentiment_score": result["sentiment_score"],
            "sentiment_label": result["sentiment_label"],
            "urgency_level": result["urgency_level"],
            "priority": result["priority"],
            "routing_status": "routed",
            "routed_at": datetime.utcnow(),
            "processing_time_ms": proc_time,
        }
        crud.create_email_record(db, record_data)
        summary["new"] += 1
        summary["routed"] += 1

    return summary
