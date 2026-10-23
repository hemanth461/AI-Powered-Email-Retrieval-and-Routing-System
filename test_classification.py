import sys
from backend.services.classifier_service import classify_email

tests = [
    ("Request for Leave Approval", "Hi, I would like to apply for casual leave from next Monday to Wednesday. Please approve."),
    ("Subject: Request for Salary Slip", "Dear HR, please send me my salary slip and payslip for the month of August."),
    ("VPN connection failure", "My laptop cannot connect to the corporate VPN and wifi network."),
    ("Product Demo and Pricing", "Can you send us a quote for 100 enterprise licenses? We want to schedule a product demo."),
    ("Invoice #84920 Duplicate Charge", "I was charged twice on my credit card for last month's subscription invoice. Please refund."),
    ("Broken submit button", "There is a 500 error on the web portal when clicking submit. The app keeps crashing."),
]

print("=" * 60)
print("TESTING CLASSIFICATION PIPELINE")
print("=" * 60)

for subject, body in tests:
    res = classify_email(subject, body)
    print(f"\nSubject: {subject}")
    print(f"  -> Predicted Category:   {res['category']}")
    print(f"  -> Routed Department:    {res['department_name']} ({res['department_email']})")
    print(f"  -> Confidence:           {res['confidence'] * 100:.1f}%")
    print(f"  -> Priority:             {res['priority'].upper()}")
