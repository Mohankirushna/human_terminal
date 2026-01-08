import torch
import torch.nn as nn
from transformers import AutoModel

class DualSpanQA(nn.Module):
    def __init__(self, model_name: str):
        super().__init__()

        self.encoder = AutoModel.from_pretrained(model_name)
        hidden = self.encoder.config.hidden_size

        # Source span heads
        self.src_start = nn.Linear(hidden, 1)
        self.src_end   = nn.Linear(hidden, 1)

        # Destination span heads
        self.dst_start = nn.Linear(hidden, 1)
        self.dst_end   = nn.Linear(hidden, 1)

    def forward(self, input_ids=None, attention_mask=None):
        # encoder output: (batch, seq_len, hidden)
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        x = outputs.last_hidden_state

        return {
            "src_start_logits": self.src_start(x).squeeze(-1),
            "src_end_logits":   self.src_end(x).squeeze(-1),
            "dst_start_logits": self.dst_start(x).squeeze(-1),
            "dst_end_logits":   self.dst_end(x).squeeze(-1),
        }
