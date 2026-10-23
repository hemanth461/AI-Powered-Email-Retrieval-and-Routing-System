"""
Maps the BERT model's predicted category to:
  1. A human-readable department name (shown in the dashboard)
  2. The mailbox that the email should be auto-forwarded to

Categories come from the existing fine-tuned BERT classifier:
sales, support, billing, hr, it, legal, complaint, general
"""
from config.settings import settings


def get_department_map() -> dict:
    """Returns category -> {name, email} mapping. Built as a function (not a
    module-level constant) so it always reflects the current settings/.env."""
    return {
        "sales": {"name": "Sales", "email": settings.dept_sales_email},
        "support": {"name": "IT Support", "email": settings.dept_support_email},
        "billing": {"name": "Finance", "email": settings.dept_billing_email},
        "hr": {"name": "HR", "email": settings.dept_hr_email},
        "it": {"name": "IT", "email": settings.dept_it_email},
        "legal": {"name": "Legal", "email": settings.dept_legal_email},
        "complaint": {"name": "Escalations", "email": settings.dept_complaint_email},
        "general": {"name": "General", "email": settings.dept_general_email},
    }


def get_department_for_category(category: str) -> dict:
    """Look up department info for a predicted category, with a safe fallback
    to 'General' for any category the model returns that isn't mapped."""
    mapping = get_department_map()
    return mapping.get(
        category.lower().strip(),
        {"name": "General", "email": settings.dept_general_email},
    )
