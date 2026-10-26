"""
BERT Inference Module for Email Triage System.
Handles loading the fine-tuned model and predicting categories.
"""
import joblib
import os
import re


class BertEmailClassifier:
    def __init__(self, model_dir=None):
        if model_dir is None:
            src_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(src_dir)
            model_dir = os.path.join(project_root, 'models', 'bert')

        self.model_path = os.path.join(model_dir, 'fine_tuned_model')
        self.tokenizer_path = os.path.join(model_dir, 'tokenizer')
        self.encoder_path = os.path.join(model_dir, 'label_encoder.joblib')

        if self._check_model_exists():
            import torch
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self._load_model()
        else:
            self.device = None
            self.model = None
            self.tokenizer = None
            self.label_encoder = None

    def _check_model_exists(self):
        """Check if all necessary files exist."""
        return (
            os.path.exists(self.model_path)
            and os.path.exists(self.tokenizer_path)
            and os.path.exists(self.encoder_path)
        )

    def _load_model(self):
        """Load the model, tokenizer and label encoder."""
        import torch
        from transformers import BertTokenizer, BertForSequenceClassification

        print(f"Loading BERT model from {self.model_path}...")
        self.tokenizer = BertTokenizer.from_pretrained(self.tokenizer_path)
        self.model = BertForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()
        self.label_encoder = joblib.load(self.encoder_path)
        print("[OK] BERT model loaded successfully.")

    def preprocess_text(self, text):
        """Clean email text: strip HTML tags, URLs, special chars, and normalize whitespace."""
        if not text:
            return ""
        # Remove any HTML tags if present
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
        text = text.lower()
        # Keep alphanumeric and basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def predict(self, subject, body):
        """Predict category for an email."""
        if not self.model:
            if self._check_model_exists():
                self._load_model()
            else:
                return None

        import torch

        clean_subj = self.preprocess_text(subject or "")
        clean_body = self.preprocess_text(body or "")
        # Subject carries high diagnostic value, give it prominence
        combined_text = f"{clean_subj} {clean_subj} {clean_body}".strip()

        encoding = self.tokenizer(
            combined_text,
            add_special_tokens=True,
            max_length=256,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=1)
            confidence, prediction = torch.max(probs, dim=1)

            category_idx = prediction.item()
            category_name = self.label_encoder.inverse_transform([category_idx])[0]

            # Get all class probabilities
            all_probs = probs.flatten().cpu().numpy()
            class_probs = {
                name: float(prob)
                for name, prob in zip(self.label_encoder.classes_, all_probs)
            }

            return {
                'category': category_name,
                'confidence': float(confidence.item()),
                'category_probs': class_probs
            }


if __name__ == "__main__":
    # Test inference if model exists
    classifier = BertEmailClassifier()
    if classifier.model:
        res = classifier.predict("Subject: Urgent issue", "Body: My account is locked.")
        print(f"Result: {res}")
    else:
        print("Model files not found. Please train the model first.")
