"""
Benchmarking script for Email Triage System models.
Compares Logistic Regression vs. BERT on the test set.
"""
import pandas as pd
import joblib
import torch
import time
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ml_model.bert_classifier import BertEmailClassifier
from sklearn.metrics import classification_report, accuracy_score
import re

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def benchmark_models():
    # 1. Load test data
    data_path = 'data/email_training_data.csv'
    if not os.path.exists(data_path):
        print("Data not found.")
        return
        
    df = pd.read_csv(data_path)
    # We'll use a portion of the data for testing (same as validation split used in training)
    _, df_test = pd.read_csv('data/email_training_data.csv').pipe(lambda x: (x.sample(frac=0.9, random_state=42), x.drop(x.sample(frac=0.9, random_state=42).index)))
    # Actually, simpler to just use a fixed subset
    df_test = df.sample(n=100, random_state=123)
    
    X = df_test['message'].values
    y_true = df_test['category'].values
    
    print(f"Benchmarking on {len(df_test)} test samples...")
    print("-" * 50)
    
    # --- Logistic Regression ---
    print("\nEvaluating Logistic Regression...")
    try:
        log_model = joblib.load('models/model.joblib')
        vectorizer = joblib.load('models/vectorizer.joblib')
        
        start_time = time.time()
        X_processed = [preprocess_text(msg) for msg in X]
        X_vectorized = vectorizer.transform(X_processed)
        y_pred_log = log_model.predict(X_vectorized)
        log_time = time.time() - start_time
        
        log_acc = accuracy_score(y_true, y_pred_log)
        print(f"Logistic Accuracy: {log_acc:.4f}")
        print(f"Total time: {log_time:.2f}s ({log_time/len(df_test):.4f}s per email)")
    except Exception as e:
        print(f"Logistic evaluation failed: {e}")
        log_acc = 0
    
    # --- BERT ---
    print("\nEvaluating BERT Model...")
    bert_classifier = BertEmailClassifier()
    if not bert_classifier.model:
        print("BERT model weights not found yet. Please wait for training to complete.")
        return
        
    start_time = time.time()
    y_pred_bert = []
    for subject, body in zip([""] * len(X), X): # Subject is empty for simplicity
        res = bert_classifier.predict(subject, body)
        y_pred_bert.append(res['category'])
    bert_time = time.time() - start_time
    
    bert_acc = accuracy_score(y_true, y_pred_bert)
    print(f"BERT Accuracy: {bert_acc:.4f}")
    print(f"Total time: {bert_time:.2f}s ({bert_time/len(df_test):.4f}s per email)")
    
    print("\n" + "="*50)
    print("FINAL COMPARISON")
    print("="*50)
    print(f"Model      | Accuracy | Latency (s/email)")
    print(f"-----------|----------|------------------")
    print(f"Logistic   | {log_acc:.2%}  | {log_time/len(df_test):.4f}")
    print(f"BERT       | {bert_acc:.2%}  | {bert_time/len(df_test):.4f}")
    print("-" * 50)
    
    if bert_acc > log_acc:
        print(f"[OK] BERT is {bert_acc - log_acc:.2%} more accurate!")
    else:
        print("Note: Performance might improve with more epochs or data.")

if __name__ == "__main__":
    benchmark_models()
