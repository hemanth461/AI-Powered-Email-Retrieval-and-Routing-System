"""
Pydantic schemas for FastAPI request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ManualClassifyRequest(BaseModel):
    subject: str = ""
    body: str = ""


class ManualClassifyResponse(BaseModel):
    category: str
    category_probs: dict
    confidence: float
    department_name: str
    department_email: str
    sentiment_label: str
    sentiment_score: float
    urgency_level: str
    urgency_keywords: list
    priority: str


class EmailRecordResponse(BaseModel):
    id: int
    gmail_message_id: str
    thread_id: Optional[str] = None
    sender: str
    receiver: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    has_attachments: bool
    attachment_names: Optional[str] = None
    received_at: Optional[datetime] = None
    predicted_category: Optional[str] = None
    predicted_department: Optional[str] = None
    department_email: Optional[str] = None
    confidence: Optional[float] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    urgency_level: Optional[str] = None
    priority: Optional[str] = None
    routing_status: str
    routed_at: Optional[datetime] = None
    routing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None

    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    total: int
    results: list[EmailRecordResponse]


class FetchEmailsResponse(BaseModel):
    fetched: int
    new: int
    duplicates: int
    routed: int
    failed: int


class DashboardStatsResponse(BaseModel):
    total_emails: int
    processed_emails: int
    pending_emails: int
    high_priority_emails: int
    department_counts: dict
    priority_counts: dict


class RouteResponse(BaseModel):
    email_id: int
    success: bool
    routing_status: str
