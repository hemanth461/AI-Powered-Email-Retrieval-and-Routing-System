"""
Manual classification endpoint — classifies subject/body text on demand
without touching Gmail or the database. Used by the Streamlit "Manual
Classification" tab.
"""
from fastapi import APIRouter, HTTPException

from backend.services.classifier_service import classify_email, is_bert_ready
from backend.schemas import ManualClassifyRequest, ManualClassifyResponse

router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post("", response_model=ManualClassifyResponse)
def classify(request: ManualClassifyRequest):
    if not is_bert_ready():
        raise HTTPException(
            status_code=503,
            detail="BERT model not loaded. Train it first (see ml_model/train_bert.py).",
        )
    if not request.subject and not request.body:
        raise HTTPException(status_code=400, detail="Provide at least a subject or body.")

    return classify_email(request.subject, request.body)
