# hcmd/core/rename_model.py
import torch.nn as nn
from transformers import AutoModel, AutoConfig

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
