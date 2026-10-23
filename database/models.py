"""
SQLAlchemy ORM models for the PostgreSQL-backed email triage database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EmailRecord(Base):
    """
    One row per processed email. `gmail_message_id` is unique so the same
    email is never processed/routed twice (duplicate-processing guard).
    """
    __tablename__ = "email_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Gmail metadata
    gmail_message_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), nullable=True)
    sender = Column(Text, nullable=False)
    receiver = Column(Text, nullable=True)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    has_attachments = Column(Boolean, default=False)
    attachment_names = Column(Text, nullable=True)  # comma-separated list
    received_at = Column(DateTime, nullable=True)

    # Classification results
    predicted_category = Column(String(50), nullable=True)
    predicted_department = Column(String(100), nullable=True)
    department_email = Column(String(320), nullable=True)
    confidence = Column(Float, nullable=True)

    # Sentiment / priority
    sentiment_label = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    urgency_level = Column(String(20), nullable=True)
    priority = Column(String(20), nullable=True)  # low / medium / high

    # Routing status: pending -> routed -> failed
    routing_status = Column(String(20), default="pending", nullable=False)
    routed_at = Column(DateTime, nullable=True)
    routing_error = Column(Text, nullable=True)

    # Bookkeeping
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_email_records_category", "predicted_category"),
        Index("ix_email_records_priority", "priority"),
        Index("ix_email_records_routing_status", "routing_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "gmail_message_id": self.gmail_message_id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "subject": self.subject,
            "body": self.body,
            "has_attachments": self.has_attachments,
            "attachment_names": self.attachment_names,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "predicted_category": self.predicted_category,
            "predicted_department": self.predicted_department,
            "department_email": self.department_email,
            "confidence": self.confidence,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "urgency_level": self.urgency_level,
            "priority": self.priority,
            "routing_status": self.routing_status,
            "routed_at": self.routed_at.isoformat() if self.routed_at else None,
            "routing_error": self.routing_error,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time_ms": self.processing_time_ms,
        }
