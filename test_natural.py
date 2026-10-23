from backend.services.classifier_service import classify_email

natural_tests = [
    (
        "Taking tomorrow off for family emergency",
        "Hi, I will not be able to log in tomorrow as I need to travel to my hometown for a family medical matter. I will be on casual time off and back on Monday."
    ),
    (
        "Workstation screen turned blue and crashed",
        "When I booted my workstation laptop today it showed a blue screen error and shut down. Can someone check the hardware or issue a replacement?"
    ),
    (
        "Looking to evaluate the platform for 50 users",
        "Hello, our organization is expanding. What are the annual subscription costs for 50 seats, and can we schedule a walkthrough demo?"
    ),
    (
        "Extra 200 dollars debited from my Mastercard",
        "Hi, my bank statement shows two identical deductions on Sept 12. Please reverse the duplicate charge and send the updated receipt."
    )
]

print("=" * 60)
print("TESTING WITHOUT ANY 'HR', 'IT', 'SALES' DEPARTMENT NAMES")
print("=" * 60)

for subj, body in natural_tests:
    res = classify_email(subj, body)
    print(f"\nSubject: {subj}")
    print(f"Body:    {body[:80]}...")
    print(f"  -> Predicted Category: {res['category'].upper()}")
    print(f"  -> Routed Department:  {res['department_name']} ({res['department_email']})")
    print(f"  -> Confidence:         {res['confidence'] * 100:.1f}%")
