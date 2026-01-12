import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from tqdm import tqdm
import json
import copy

MODEL_NAME = "distilbert-base-uncased"
BATCH_SIZE = 16
EPOCHS = 20
LR = 2e-5
MAX_LEN = 64
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")
EARLY_STOPPING_PATIENCE = 3
LR_PATIENCE = 2
LR_FACTOR = 0.05

df = pd.read_csv("intent_dataset.csv")

labels = sorted(df["label"].unique())
label2id = {l: i for i, l in enumerate(labels)}
id2label = {i: l for l, i in label2id.items()}
df["label_id"] = df["label"].map(label2id)

with open("../label_map.json", "w") as f:
    json.dump({"label2id": label2id, "id2label": id2label}, f)

train_df, val_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["label_id"],
    random_state=42
)

class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt"
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long)
        }

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME,local_files_only=True)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

model.to(DEVICE)

train_ds = IntentDataset(
    train_df["text"].tolist(),
    train_df["label_id"].tolist(),
    tokenizer
)

val_ds = IntentDataset(
    val_df["text"].tolist(),
    val_df["label_id"].tolist(),
    tokenizer
)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

optimizer = AdamW(model.parameters(), lr=LR)

scheduler = ReduceLROnPlateau(
    optimizer,
    mode="max",
    patience=LR_PATIENCE,
    factor=LR_FACTOR,
)

best_acc = 0.0
best_model_state = None
epochs_no_improve = 0

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0.0

    for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        optimizer.zero_grad()
        batch = {k: v.to(DEVICE) for k, v in batch.items()}
        out = model(**batch)
        loss = out.loss
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    model.eval()
    preds, gold = [], []

    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validating"):
            batch = {k: v.to(DEVICE) for k, v in batch.items()}
            logits = model(**batch).logits
            preds.extend(torch.argmax(logits, dim=1).cpu().numpy())
            gold.extend(batch["labels"].cpu().numpy())

    acc = accuracy_score(gold, preds)
    scheduler.step(acc)

    print(f"Epoch {epoch+1} Loss: {train_loss / len(train_loader):.4f}  Acc: {acc:.4f}")

    if acc > best_acc:
        best_acc = acc
        best_model_state = copy.deepcopy(model.state_dict())
        epochs_no_improve = 0
    else:
        epochs_no_improve += 1

    if epochs_no_improve >= EARLY_STOPPING_PATIENCE:
        print("Early stopping triggered")
        break

model.load_state_dict(best_model_state)

print(classification_report(
    gold,
    preds,
    target_names=[id2label[i] for i in range(len(labels))]
))

model.save_pretrained("intent_model")
tokenizer.save_pretrained("intent_model")
