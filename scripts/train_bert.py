"""
Training script for BERT-based email classification.
Fine-tunes bert-base-uncased on the business email dataset.
"""
import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from tqdm import tqdm
import joblib

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

class EmailDataset(Dataset):
    def __init__(self, messages, labels, tokenizer, max_len=128):
        self.messages = messages
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, item):
        message = str(self.messages[item])
        label = self.labels[item]

        encoding = self.tokenizer(
            message,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'message_text': message,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_bert():
    # 1. Load data
    data_path = 'data/email_training_data.csv'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    
    # 2. Encode labels
    label_encoder = LabelEncoder()
    df['label_idx'] = label_encoder.fit_transform(df['category'])
    num_labels = len(label_encoder.classes_)
    
    # Save label encoder
    os.makedirs('models/bert', exist_ok=True)
    joblib.dump(label_encoder, 'models/bert/label_encoder.joblib')
    
    # 3. Split data
    df_train, df_val = train_test_split(df, test_size=0.1, random_state=42, stratify=df['label_idx'])
    
    # 4. Initialize Tokenizer
    print("Loading BERT tokenizer...")
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    
    # 5. Create DataLoaders
    train_dataset = EmailDataset(
        messages=df_train.message.to_numpy(),
        labels=df_train.label_idx.to_numpy(),
        tokenizer=tokenizer
    )
    
    val_dataset = EmailDataset(
        messages=df_val.message.to_numpy(),
        labels=df_val.label_idx.to_numpy(),
        tokenizer=tokenizer
    )
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    
    # 6. Initialize BERT Model
    print(f"Initializing BERT for {num_labels} classes...")
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-uncased',
        num_labels=num_labels
    )
    model.to(device)
    
    # 7. Optimizer and Scheduler
    epochs = 4
    optimizer = AdamW(model.parameters(), lr=2e-5)
    total_steps = len(train_loader) * epochs
    
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )
    
    # 8. Training Loop
    print("\nStarting fine-tuning...")
    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 10)
        
        model.train()
        train_loss = 0
        
        for batch in tqdm(train_loader, desc="Training"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            model.zero_grad()
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            train_loss += loss.item()
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            
        avg_train_loss = train_loss / len(train_loader)
        print(f"Train loss: {avg_train_loss:.4f}")
        
        # Validation
        model.eval()
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                logits = outputs.logits
                preds = torch.argmax(logits, dim=1).flatten()
                
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())
                
        accuracy = accuracy_score(val_labels, val_preds)
        print(f"Validation Accuracy: {accuracy:.4f}")
    
    # 9. Final Evaluation
    print("\nFinal Evaluation Report:")
    print(classification_report(val_labels, val_preds, target_names=label_encoder.classes_))
    
    # 10. Save Model
    print("\nSaving fine-tuned model...")
    model.save_pretrained('models/bert/fine_tuned_model')
    tokenizer.save_pretrained('models/bert/tokenizer')
    print("[OK] Model and tokenizer saved in models/bert/")

if __name__ == "__main__":
    train_bert()
