"""
Sentiment Analysis Module for Email Triage System
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) for sentiment scoring.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

class SentimentAnalyzer:
    """Analyzes sentiment and urgency of text messages."""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Urgency keywords for priority detection
        self.urgency_keywords = {
            'critical': 3,
            'urgent': 3,
            'emergency': 3,
            'asap': 2,
            'immediately': 2,
            'priority': 2,
            'important': 1,
            'soon': 1,
            'quickly': 1,
        }
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Sentiment scores and classification
        """
        # Get VADER scores
        scores = self.analyzer.polarity_scores(text)
        
        # Classify sentiment
        compound = scores['compound']
        if compound >= 0.05:
            sentiment_label = 'positive'
        elif compound <= -0.05:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return {
            'label': sentiment_label,
            'compound': compound,
            'positive': scores['pos'],
            'neutral': scores['neu'],
            'negative': scores['neg']
        }
    
    def detect_urgency(self, text):
        """
        Detect urgency level based on keywords.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Urgency score and level
        """
        text_lower = text.lower()
        urgency_score = 0
        found_keywords = []
        
        # Check for urgency keywords
        for keyword, weight in self.urgency_keywords.items():
            if keyword in text_lower:
                urgency_score += weight
                found_keywords.append(keyword)
        
        # Classify urgency level
        if urgency_score >= 5:
            urgency_level = 'critical'
        elif urgency_score >= 3:
            urgency_level = 'high'
        elif urgency_score >= 1:
            urgency_level = 'medium'
        else:
            urgency_level = 'low'
        
        return {
            'level': urgency_level,
            'score': urgency_score,
            'keywords': found_keywords
        }
    
    def calculate_priority(self, text):
        """
        Calculate overall priority combining sentiment and urgency.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Complete analysis with priority
        """
        sentiment = self.analyze_sentiment(text)
        urgency = self.detect_urgency(text)
        
        # Priority calculation
        # High priority: negative sentiment + high urgency
        # Medium priority: negative sentiment OR medium urgency
        # Low priority: positive/neutral sentiment + low urgency
        
        if sentiment['label'] == 'negative' and urgency['level'] in ['critical', 'high']:
            priority = 'high'
        elif sentiment['label'] == 'negative' or urgency['level'] in ['high', 'medium']:
            priority = 'medium'
        else:
            priority = 'low'
        
        return {
            'sentiment': sentiment,
            'urgency': urgency,
            'priority': priority
        }
    
    def analyze_email(self, subject, body):
        """
        Analyze complete email (subject + body).
        
        Args:
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            dict: Complete analysis
        """
        # Combine subject and body (subject weighted more)
        combined_text = f"{subject} {subject} {body}"
        
        analysis = self.calculate_priority(combined_text)
        
        # Add email-specific metadata
        analysis['subject_sentiment'] = self.analyze_sentiment(subject)
        analysis['body_sentiment'] = self.analyze_sentiment(body)
        
        return analysis


def test_sentiment_analyzer():
    """Test the sentiment analyzer with sample emails."""
    
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        {
            'subject': 'URGENT: System Down - Critical Issue',
            'body': 'Our production system is completely down. We need immediate assistance. This is affecting all customers.',
            'expected_priority': 'high'
        },
        {
            'subject': 'Question about invoice',
            'body': 'Hi, I have a question about my recent invoice. Could you please help when you get a chance?',
            'expected_priority': 'low'
        },
        {
            'subject': 'Complaint about service',
            'body': 'I am very disappointed with the service quality. This needs to be addressed soon.',
            'expected_priority': 'medium'
        },
        {
            'subject': 'Thank you for excellent support',
            'body': 'I wanted to thank your team for the excellent support. Everything is working perfectly now.',
            'expected_priority': 'low'
        }
    ]
    
    print("="*70)
    print("SENTIMENT ANALYZER TEST")
    print("="*70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Subject: {test['subject']}")
        print(f"Body: {test['body'][:60]}...")
        
        result = analyzer.analyze_email(test['subject'], test['body'])
        
        print(f"\nSentiment: {result['sentiment']['label']} (score: {result['sentiment']['compound']:.3f})")
        print(f"Urgency: {result['urgency']['level']} (keywords: {result['urgency']['keywords']})")
        print(f"Priority: {result['priority']} (expected: {test['expected_priority']})")
        
        if result['priority'] == test['expected_priority']:
            print("✓ CORRECT")
        else:
            print("✗ MISMATCH")
        
        print("-"*70)


if __name__ == "__main__":
    test_sentiment_analyzer()
