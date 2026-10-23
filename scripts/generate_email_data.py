"""
Enhanced dataset generator for email triage system.
Includes business-relevant categories and realistic email scenarios.
"""
import pandas as pd
import random
import os

# Define business email categories with realistic examples
CATEGORIES = {
    'sales': [
        "I'm interested in purchasing your enterprise plan",
        "Can you provide a quote for 100 licenses",
        "What are your pricing options for small businesses",
        "I'd like to schedule a product demo",
        "Do you offer volume discounts",
        "We're looking to upgrade our current subscription",
        "Can you send me information about your premium features",
        "I want to discuss a partnership opportunity",
        "What's included in the professional tier",
        "I need pricing for annual vs monthly plans",
        "Please send a formal quotation for our procurement team",
        "We are looking to buy 50 user seats for our sales organization",
        "Could a sales representative reach out to discuss custom pricing",
        "We want to compare your enterprise tier with our current provider",
        "Can we get a trial extension before finalizing our purchase"
    ],
    'support': [
        "I'm having trouble logging into my account",
        "The application keeps crashing when I click submit",
        "I can't find the export feature",
        "How do I reset my password",
        "The page is showing a 404 error",
        "I need help configuring the settings",
        "The system is running very slowly",
        "I'm getting an error message that says connection failed",
        "Can you help me understand how to use this feature",
        "The mobile app won't sync with the web version",
        "There is a bug in the reporting module that gives incorrect totals",
        "I am receiving a 500 internal server error when saving my profile",
        "The button to download CSV is completely unresponsive",
        "Search results are taking over a minute to load or timing out"
    ],
    'billing': [
        "I was charged twice for my subscription",
        "I need a refund for last month's payment",
        "Can you send me an invoice for my recent purchase",
        "My credit card was declined but I was still charged",
        "I want to update my payment method",
        "When will my refund be processed",
        "I don't recognize this charge on my statement",
        "Can I get a receipt for tax purposes",
        "I need to cancel my subscription and get a refund",
        "There's an error in my billing statement",
        "Please provide the GST tax invoice for transaction #84920",
        "Our annual renewal payment failed due to an expired card",
        "We were overcharged by $150 on our latest monthly statement",
        "Can you change our billing address and company VAT number"
    ],
    'hr': [
        "I need to update my personal information",
        "Can I request time off for next week",
        "I have a question about my benefits package",
        "I need to report a workplace concern",
        "Can you send me my employment verification letter",
        "I want to enroll in the health insurance plan",
        "I need information about the retirement plan",
        "Can I change my direct deposit information",
        "I have a question about the company policy",
        "I need to request parental leave",
        "Please approve my casual leave request for the upcoming holidays",
        "Could you send me my salary slip and payslip for last month",
        "I have an inquiry regarding my annual appraisal and compensation review",
        "I would like to submit my resignation and understand my notice period",
        "Can you please issue a relieving letter and experience certificate",
        "How do I add my newborn dependent to the group medical insurance",
        "There is a discrepancy in my provident fund PF deduction this month",
        "Request for leave approval from next Monday to Wednesday"
    ],
    'it': [
        "I need access to the shared drive",
        "My computer won't connect to the VPN",
        "Can you reset my network password",
        "I need software installed on my laptop",
        "The printer is not working",
        "I can't access the internal portal",
        "My email is not syncing properly",
        "I need permissions for the database",
        "The video conferencing tool keeps disconnecting",
        "Can you help me set up my new work phone",
        "My external monitor is flickering and not detecting the HDMI signal",
        "I am getting a blue screen error on my workstation laptop",
        "Please grant me read-write access to the AWS development bucket",
        "My corporate Wi-Fi keeps disconnecting every 10 minutes",
        "I need admin rights to install Docker and Python on my MacBook"
    ],
    'legal': [
        "I need to review the terms of service",
        "Can you send me a copy of our contract",
        "I have concerns about data privacy compliance",
        "I need legal approval for this vendor agreement",
        "Can you clarify the liability clause",
        "I want to report a potential compliance issue",
        "I need the NDA template",
        "Can you review this partnership agreement",
        "I have questions about intellectual property rights",
        "I need legal guidance on this customer dispute",
        "Please review this non-disclosure agreement before we share client data",
        "Does our data processing comply with GDPR and CCPA requirements",
        "We received a formal legal notice from a competitor regarding trademark"
    ],
    'complaint': [
        "This is completely unacceptable service",
        "I am extremely disappointed with your company",
        "Your staff was rude and unprofessional",
        "I've been waiting for weeks with no response",
        "This is the worst customer experience I've ever had",
        "I want to file a formal complaint",
        "Your product quality has significantly declined",
        "I demand to speak with a manager immediately",
        "This is not what was promised to me",
        "I'm considering legal action if this isn't resolved",
        "You charged my account without permission and your support is ignoring me",
        "Your representative hung up on me while I was explaining our outage"
    ],
    'general': [
        "What are your business hours",
        "Where is your office located",
        "Do you have a mobile app",
        "Can you add me to your mailing list",
        "I have a general question about your services",
        "How can I contact customer service",
        "Do you offer training sessions",
        "I'd like to provide feedback on your website",
        "Can you tell me more about your company",
        "I have a suggestion for improvement",
        "What is the contact email for media and press inquiries",
        "Could you send me your company brochure and overview deck"
    ]
}

def generate_variations(base_messages, num_variations=15):
    """Generate variations of base messages to create more training data."""
    variations = []
    
    # Email-style prefixes and suffixes
    prefixes = [
        "",
        "Hi, ",
        "Hello, ",
        "Dear Support Team, ",
        "Good morning, ",
        "URGENT: ",
        "Quick question: ",
        "Need help: ",
    ]
    
    suffixes = [
        "",
        " Thanks!",
        " Please help.",
        " This is urgent.",
        " Thank you for your assistance.",
        " Looking forward to your response.",
        " Best regards",
        " Please respond ASAP.",
        " Appreciate your help.",
    ]
    
    for _ in range(num_variations):
        msg = random.choice(base_messages)
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        variations.append(f"{prefix}{msg}{suffix}")
    
    return variations

def generate_dataset(output_path='data/email_training_data.csv', samples_per_category=80):
    """Generate a synthetic email dataset with labeled messages."""
    
    data = []
    
    for category, base_messages in CATEGORIES.items():
        # Generate variations for each category
        messages = generate_variations(base_messages, samples_per_category)
        
        for message in messages:
            data.append({
                'message': message,
                'category': category
            })
    
    # Create DataFrame and shuffle
    df = pd.DataFrame(data)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"✓ Generated {len(df)} labeled email messages")
    print(f"✓ Saved to: {output_path}")
    print(f"\nCategory distribution:")
    print(df['category'].value_counts().sort_index())
    
    return df

if __name__ == "__main__":
    generate_dataset()
