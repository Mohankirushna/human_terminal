import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import copy
import os

MODEL_NAME = "distilbert-base-uncased"
BATCH_SIZE = 16
EPOCHS = 20
LR = 3e-5
MAX_LEN = 64

EARLY_STOPPING_PATIENCE = 3
LR_PATIENCE = 2
LR_FACTOR = 0.5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CSV_PATH = "rename_spans.csv"
OUT_DIR = "rename_span_model"

df = pd.read_csv(CSV_PATH)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class RenameSpanDataset(Dataset):
    def __init__(self, df):
        self.texts = df["text"].tolist()
        self.src_s = df["src_start"].tolist()
        self.src_e = df["src_end"].tolist()
        self.dst_s = df["dst_start"].tolist()
        self.dst_e = df["dst_end"].tolist()

    def __len__(self):
        return len(self.texts)

    def _char_to_token(self, offsets, start, end):
        ts, te = 0, 0
        for i, (s, e) in enumerate(offsets):
            if s <= start < e:
                ts = i
            if s < end <= e:
                te = i
                break
        return ts, te

    def __getitem__(self, idx):
        enc = tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_offsets_mapping=True,
            return_tensors="pt"
        )

        offsets = enc.pop("offset_mapping")[0]

        src_ts, src_te = self._char_to_token(
            offsets, self.src_s[idx], self.src_e[idx]
        )
        dst_ts, dst_te = self._char_to_token(
            offsets, self.dst_s[idx], self.dst_e[idx]
        )

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "start_positions": torch.tensor(src_ts),
            "end_positions": torch.tensor(dst_te),
        }

train_ds = RenameSpanDataset(train_df)
val_ds = RenameSpanDataset(val_df)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

model = AutoModelForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)

optimizer = AdamW(model.parameters(), lr=LR)
scheduler = ReduceLROnPlateau(
    optimizer,
    mode="min",
    patience=LR_PATIENCE,
    factor=LR_FACTOR
)

best_val = float("inf")
best_state = None
no_improve = 0

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
    val_loss = 0.0

    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(DEVICE) for k, v in batch.items()}
            val_loss += model(**batch).loss.item()

    val_loss /= len(val_loader)
    scheduler.step(val_loss)

    print(f"Epoch {epoch+1} Train: {train_loss/len(train_loader):.4f}  Val: {val_loss:.4f}")

    if val_loss < best_val:
        best_val = val_loss
        best_state = copy.deepcopy(model.state_dict())
        no_improve = 0
    else:
        no_improve += 1

    if no_improve >= EARLY_STOPPING_PATIENCE:
        print("Early stopping triggered")
        break

model.load_state_dict(best_state)
os.makedirs(OUT_DIR, exist_ok=True)
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)

print(f"Model saved → {OUT_DIR}")
