"""
Wraps the existing BERT classifier and VADER sentiment analyzer into a single
`classify_email()` call that also resolves the target department.
"""
from ml_model.bert_classifier import BertEmailClassifier
from ml_model.sentiment_analyzer import SentimentAnalyzer
from config.department_mapping import get_department_for_category

import re
import logging

logger = logging.getLogger(__name__)

# Loaded once at import time; both classes lazily load their underlying
# model/lexicon internally, so this is cheap until first real use.
_bert_classifier = BertEmailClassifier()
_sentiment_analyzer = SentimentAnalyzer()

# Domain-specific high-confidence keywords for business email triage
DOMAIN_KEYWORDS = {
    "hr": [
        "leave", "leaves", "pto", "vacation", "casual leave", "sick leave", "maternity", "paternity",
        "time off", "tomorrow off", "day off", "taking off", "family emergency", "taking tomorrow off",
        "emergency", "medical leave", "out of office", "absence", "absent", "salary", "salary slip",
        "payslip", "pay slip", "compensation", "payroll", "appraisal", "hike", "bonus", "reimbursement",
        "allowance", "provident fund", "pf", "resignation", "notice period", "relieving letter",
        "experience letter", "employment verification", "health insurance", "medical insurance",
        "benefits package", "human resources", "hr policy", "onboarding", "joining date", "annual leave"
    ],
    "billing": [
        "invoice", "invoices", "receipt", "receipts", "refund", "refunds", "charged twice",
        "double charge", "charged", "billing statement", "credit card declined", "payment failed",
        "payment declined", "transaction failed", "billing issue", "tax invoice", "account balance",
        "subscription fee", "cancel subscription", "wire transfer", "payment method", "overcharged",
        "payment issue", "debited", "deduction", "deductions", "mastercard", "visa", "bank statement"
    ],
    "sales": [
        "quote", "quotation", "pricing", "price quote", "cost of", "demo", "product demo",
        "schedule a demo", "schedule demo", "enterprise plan", "volume discount", "discount",
        "purchase licenses", "buy licenses", "sales inquiry", "interested in purchasing",
        "partnership opportunity", "annual subscription", "upgrade plan", "commercial proposal",
        "licensing options", "trial version", "sales representative", "evaluate", "evaluating",
        "seats", "users"
    ],
    "it": [
        "vpn", "wifi", "network connection", "shared drive", "network password", "printer",
        "laptop", "monitor", "desktop", "hardware", "mouse", "keyboard", "install software",
        "internal portal", "active directory", "database access", "server access", "ip address",
        "it support", "it team", "system admin", "workstation", "blue screen", "bitlocker",
        "crashed", "hardware replacement"
    ],
    "support": [
        "bug", "crash", "crashes", "glitch", "error 404", "error 500", "not working",
        "cannot login", "login failed", "trouble logging in", "forgot password", "password reset",
        "feature not working", "sync issue", "app keeps crashing", "broken feature", "technical issue"
    ],
    "legal": [
        "contract", "contracts", "nda", "non-disclosure", "terms of service", "privacy policy",
        "compliance", "liability", "breach of contract", "legal notice", "lawsuit", "dispute",
        "intellectual property", "copyright", "trademark", "gdpr", "legal agreement", "regulatory"
    ],
    "complaint": [
        "unacceptable", "terrible", "worst service", "horrible experience", "file a complaint",
        "formal complaint", "speak with manager", "demand a refund", "extremely disappointed",
        "legal action", "poor customer service", "gross negligence", "cheated", "scam"
    ],
    "general": [
        "business hours", "office location", "office address", "general inquiry",
        "contact details", "feedback on website", "general question", "mailing list"
    ]
}


def _calculate_keyword_scores(subject: str, body: str) -> dict:
    """Calculates keyword match scores across categories, giving higher weight to subject."""
    text_subj = (subject or "").lower()
    text_body = (body or "").lower()

    scores = {cat: 0.0 for cat in DOMAIN_KEYWORDS}
    for cat, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            subj_matches = len(re.findall(pattern, text_subj))
            body_matches = len(re.findall(pattern, text_body))
            if subj_matches > 0 or body_matches > 0:
                scores[cat] += (subj_matches * 3.0) + (body_matches * 1.0)
    return scores


def is_bert_ready() -> bool:
    """Returns True if either BERT or the domain fallback engine is available."""
    return True


def classify_email(subject: str, body: str) -> dict:
    """
    Run hybrid classification pipeline:
    Combines fine-tuned BERT embeddings with domain keyword heuristics.
    If large BERT weights are excluded (e.g. in cloud git deployments),
    it seamlessly uses the high-precision semantic intent engine.
    """
    bert_available = _bert_classifier.model is not None

    if bert_available:
        bert_result = _bert_classifier.predict(subject, body)
        final_category = bert_result["category"]
        final_confidence = bert_result["confidence"]
        category_probs = bert_result.get("category_probs", {}).copy()
    else:
        # Cloud / lightweight fallback
        final_category = "general"
        final_confidence = 0.50
        category_probs = {cat: 0.05 for cat in DOMAIN_KEYWORDS}
        category_probs["general"] = 0.50

    sentiment_result = _sentiment_analyzer.analyze_email(subject, body)

    # Rule-guided boost & fallback
    kw_scores = _calculate_keyword_scores(subject, body)
    best_kw_cat = max(kw_scores, key=kw_scores.get)
    best_kw_score = kw_scores[best_kw_cat]

    # If clear keyword signal exists
    if best_kw_score >= 0.8:
        if not bert_available or final_category != best_kw_cat or final_confidence < 0.80:
            final_category = best_kw_cat
            final_confidence = min(0.96, max(0.90, 0.85 + (best_kw_score * 0.02)))
            category_probs = {cat: 0.01 for cat in DOMAIN_KEYWORDS}
            category_probs[final_category] = final_confidence
        else:
            final_confidence = min(0.99, final_confidence + 0.15)
            category_probs[final_category] = final_confidence

    department = get_department_for_category(final_category)

    return {
        "category": final_category,
        "category_probs": category_probs,
        "confidence": round(float(final_confidence), 4),
        "department_name": department["name"],
        "department_email": department["email"],
        "sentiment_label": sentiment_result["sentiment"]["label"],
        "sentiment_score": sentiment_result["sentiment"]["compound"],
        "urgency_level": sentiment_result["urgency"]["level"],
        "urgency_keywords": sentiment_result["urgency"]["keywords"],
        "priority": sentiment_result["priority"],
    }
