"""Small left-padded temporal model; no future samples or padded-tail pooling."""
import torch
from torch import nn
from torch.nn import functional as F


class CausalConv(nn.Conv1d):
    def forward(self, x):
        return super().forward(F.pad(x, (self.dilation[0] * (self.kernel_size[0] - 1), 0)))


class TinyTCN(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(CausalConv(16, 24, 3), nn.ReLU(),
                                     CausalConv(24, 24, 3, dilation=2), nn.ReLU(),
                                     CausalConv(24, 24, 3, dilation=4), nn.ReLU())
        self.head = nn.Linear(24, 8)

    def forward(self, x, lengths):
        if x.ndim != 3 or x.shape[1] != 16 or lengths.shape != (x.shape[0],):
            raise ValueError("Expected batch/channel/time inputs and one length per trial")
        if torch.any(lengths < 1) or torch.any(lengths > x.shape[2]):
            raise ValueError("Invalid sequence lengths")
        encoded = self.encoder(x)
        last = encoded[torch.arange(x.shape[0], device=x.device), :, lengths - 1]
        return self.head(last)
