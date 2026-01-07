import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, AutoConfig
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import copy
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

MODEL_NAME = "distilbert-base-uncased"
BATCH_SIZE = 16
EPOCHS = 20
LR = 3e-5
MAX_LEN = 64

EARLY_STOPPING_PATIENCE = 3
LR_PATIENCE = 2
LR_FACTOR = 0.5

CSV_PATH = "rename_spans.csv"
OUT_DIR = "rename_span_model"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(CSV_PATH)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# --------------------------------------------------
# DATASET
# --------------------------------------------------

class RenameSpanDataset(Dataset):
    def __init__(self, df):
        self.df = df.reset_index(drop=True)

    def __len__(self):
        return len(self.df)

    def _char_to_token(self, offsets, start, end):
        ts = te = 0
        for i, (s, e) in enumerate(offsets):
            if s <= start < e:
                ts = i
            if s < end <= e:
                te = i
                break
        return ts, te

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        enc = tokenizer(
            row.text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_offsets_mapping=True,
            return_tensors="pt"
        )

        offsets = enc.pop("offset_mapping")[0]

        src_ts, src_te = self._char_to_token(
            offsets, row.src_start, row.src_end
        )
        dst_ts, dst_te = self._char_to_token(
            offsets, row.dst_start, row.dst_end
        )

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "src_start_positions": torch.tensor(src_ts),
            "src_end_positions": torch.tensor(src_te),
            "dst_start_positions": torch.tensor(dst_ts),
            "dst_end_positions": torch.tensor(dst_te),
        }

train_ds = RenameSpanDataset(train_df)
val_ds = RenameSpanDataset(val_df)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

# --------------------------------------------------
# MODEL (ONE ENCODER, TWO QA HEADS)
# --------------------------------------------------

class DualSpanQA(nn.Module):
    def __init__(self, model_name):
        super().__init__()
        self.config = AutoConfig.from_pretrained(model_name)
        self.encoder = AutoModel.from_pretrained(model_name)
        h = self.config.hidden_size

        self.src_start = nn.Linear(h, 1)
        self.src_end   = nn.Linear(h, 1)
        self.dst_start = nn.Linear(h, 1)
        self.dst_end   = nn.Linear(h, 1)

    def forward(
        self,
        input_ids,
        attention_mask,
        src_start_positions=None,
        src_end_positions=None,
        dst_start_positions=None,
        dst_end_positions=None,
    ):
        out = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )

        seq = out.last_hidden_state  # (B, T, H)

        src_start_logits = self.src_start(seq).squeeze(-1)
        src_end_logits   = self.src_end(seq).squeeze(-1)
        dst_start_logits = self.dst_start(seq).squeeze(-1)
        dst_end_logits   = self.dst_end(seq).squeeze(-1)

        loss = None
        if src_start_positions is not None:
            ce = nn.CrossEntropyLoss()
            loss = (
                ce(src_start_logits, src_start_positions) +
                ce(src_end_logits,   src_end_positions) +
                ce(dst_start_logits, dst_start_positions) +
                ce(dst_end_logits,   dst_end_positions)
            ) / 4

        return {
            "loss": loss,
            "src_start_logits": src_start_logits,
            "src_end_logits": src_end_logits,
            "dst_start_logits": dst_start_logits,
            "dst_end_logits": dst_end_logits,
        }

model = DualSpanQA(MODEL_NAME).to(DEVICE)

# --------------------------------------------------
# OPTIMIZATION
# --------------------------------------------------

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

# --------------------------------------------------
# TRAINING LOOP
# --------------------------------------------------

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0.0

    for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        batch = {k: v.to(DEVICE) for k, v in batch.items()}
        optimizer.zero_grad()
        out = model(**batch)
        out["loss"].backward()
        optimizer.step()
        train_loss += out["loss"].item()

    model.eval()
    val_loss = 0.0
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(DEVICE) for k, v in batch.items()}
            val_loss += model(**batch)["loss"].item()

    val_loss /= len(val_loader)
    scheduler.step(val_loss)

    print(
        f"Epoch {epoch+1} | "
        f"Train {train_loss / len(train_loader):.4f} | "
        f"Val {val_loss:.4f}"
    )

    if val_loss < best_val:
        best_val = val_loss
        best_state = copy.deepcopy(model.state_dict())
        no_improve = 0
    else:
        no_improve += 1

    if no_improve >= EARLY_STOPPING_PATIENCE:
        print("Early stopping triggered")
        break

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------

model.load_state_dict(best_state)
os.makedirs(OUT_DIR, exist_ok=True)

torch.save(model.state_dict(), os.path.join(OUT_DIR, "pytorch_model.bin"))
tokenizer.save_pretrained(OUT_DIR)

print(f"✅ Model saved → {OUT_DIR}")
