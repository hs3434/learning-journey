"""
Transformer Decoder
==================
GPT-style causal Transformer for EEG classification.

Length-agnostic: model accepts any n_times >= kernel at inference.
Training in v1 requires uniform n_times within a batch.
"""
from __future__ import annotations
import numpy as np
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from bci.decoder.base import Decoder


class _TokenEmbedding(nn.Module):
    """Conv1d(n_ch, n_ch, k, s) time-domain → token sequence.

    Input: (B, n_ch, n_times)
    Output: (B, n_tokens, n_ch) where n_tokens = (n_times - k) // s + 1
    """

    def __init__(self, n_channels: int, kernel: int, stride: int):
        super().__init__()
        self.conv = nn.Conv1d(n_channels, n_channels,
                              kernel_size=kernel, stride=stride)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x).transpose(1, 2)


class _CausalMask(nn.Module):
    """Causal attention mask: mask[q, k] = -inf if k > q else 0."""

    def __init__(self, size: int):
        super().__init__()
        mask = torch.triu(torch.full((size, size), float("-inf")), diagonal=1)
        self.register_buffer("mask", mask, persistent=False)

    def forward(self, n: int) -> torch.Tensor:
        if n <= self.mask.shape[0]:
            return self.mask[:n, :n]
        return torch.triu(torch.full((n, n), float("-inf")), diagonal=1)


class _RotaryPositionalEmbedding(nn.Module):
    """RoPE: rotates Q/K by position-dependent angles.

    Pairs (2i, 2i+1) share angle m * theta_i for i in [0, d/2).
    """

    def __init__(self, d_model: int, max_seq_len: int = 4096,
                 base: float = 10000.0):
        super().__init__()
        if d_model % 2 != 0:
            raise ValueError(f"d_model must be even, got {d_model}")
        self.d_model = d_model
        inv_freq = 1.0 / (base ** (torch.arange(0, d_model, 2).float()
                                  / d_model))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._cached_max = -1
        self._cos: torch.Tensor | None = None
        self._sin: torch.Tensor | None = None

    def _build_cache(self, max_len: int, device, dtype):
        if max_len <= self._cached_max and self._cos is not None:
            return
        t = torch.arange(max_len, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        self._cos = freqs.cos().to(dtype)
        self._sin = freqs.sin().to(dtype)
        self._cached_max = max_len

    def _rotate_half(self, x: torch.Tensor) -> torch.Tensor:
        x1 = x[..., 0::2]
        x2 = x[..., 1::2]
        return torch.stack((-x2, x1), dim=-1).flatten(-2)

    def forward(self, x: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        self._build_cache(int(positions.max().item()) + 1,
                          x.device, x.dtype)
        cos = self._cos[positions].repeat_interleave(2, dim=-1).unsqueeze(0)
        sin = self._sin[positions].repeat_interleave(2, dim=-1).unsqueeze(0)
        return (x * cos) + (self._rotate_half(x) * sin)


class _CausalMHA(nn.Module):
    """Causal multi-head self-attention with RoPE."""

    def __init__(self, d_model: int, n_heads: int, dropout: float,
                 max_seq_len: int):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.attn_drop = nn.Dropout(dropout)
        self.resid_drop = nn.Dropout(dropout)
        self.rope = _RotaryPositionalEmbedding(d_model, max_seq_len)
        self.mask = _CausalMask(max_seq_len)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, _ = x.shape
        Q = self.q_proj(x)
        K = self.k_proj(x)
        V = self.v_proj(x)
        positions = torch.arange(T, device=x.device)
        Q = self.rope(Q, positions)
        K = self.rope(K, positions)
        Q = Q.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        K = K.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        V = V.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        scores = (Q @ K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        scores = scores + self.mask(T)
        attn = torch.softmax(scores, dim=-1)
        attn = self.attn_drop(attn)
        out = (attn @ V).transpose(1, 2).contiguous().view(B, T, self.d_model)
        return self.resid_drop(self.out_proj(out))


class _FeedForward(nn.Module):
    def __init__(self, d_model: int, dropout: float):
        super().__init__()
        self.fc1 = nn.Linear(d_model, 4 * d_model)
        self.fc2 = nn.Linear(4 * d_model, d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.drop(self.fc2(torch.nn.functional.gelu(self.fc1(x))))


class _DecoderBlock(nn.Module):
    """Pre-LN decoder block: MHA + FFN with residuals."""

    def __init__(self, d_model: int, n_heads: int, dropout: float,
                 max_seq_len: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = _CausalMHA(d_model, n_heads, dropout, max_seq_len)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = _FeedForward(d_model, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x


class _EEGTransformer(nn.Module):
    """Token Embedding + N×DecoderBlock + per-position classifier + last slice."""

    def __init__(self, n_channels: int, n_classes: int,
                 d_model: int = 64, n_heads: int = 4, n_layers: int = 3,
                 kernel: int = 20, stride: int = 10,
                 dropout: float = 0.2, max_seq_len: int = 1024):
        super().__init__()
        self.token_embed = _TokenEmbedding(n_channels, kernel, stride)
        self.input_proj = nn.Linear(n_channels, d_model)
        self.blocks = nn.ModuleList([
            _DecoderBlock(d_model, n_heads, dropout, max_seq_len)
            for _ in range(n_layers)
        ])
        self.classifier = nn.Linear(d_model, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.token_embed(x)
        x = self.input_proj(x)
        for block in self.blocks:
            x = block(x)
        return self.classifier(x[:, -1, :])


class TransformerDecoder(Decoder):
    """GPT-style causal Transformer for EEG classification.

    Length-agnostic at inference: accepts any n_times >= kernel.
    Training in v1 requires uniform n_times within a batch.
    """

    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        kernel: int = 20,
        stride: int = 10,
        dropout: float = 0.2,
        epochs: int = 50,
        lr: float = 5e-4,
        weight_decay: float = 1e-4,
        device: str = 'cpu',
    ) -> None:
        if d_model % n_heads != 0:
            raise ValueError(
                f"d_model={d_model} must be divisible by n_heads={n_heads}"
            )
        if kernel <= 0 or stride <= 0:
            raise ValueError(
                f"kernel={kernel} and stride={stride} must be positive"
            )
        if kernel < stride:
            raise ValueError(
                f"kernel={kernel} must be >= stride={stride} (no info loss)"
            )
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.kernel = kernel
        self.stride = stride
        self.dropout = dropout
        self.epochs = epochs
        self.lr = lr
        self.weight_decay = weight_decay
        self.device = device
        self.n_channels: int | None = None
        self.classes_: np.ndarray = np.array([])
        self._n_classes = 0
        self._train_n_tokens: int = 0
        self.model: nn.Module | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'TransformerDecoder':
        if X.shape[0] != len(y):
            raise ValueError(
                f"X.shape[0]={X.shape[0]} != len(y)={len(y)}"
            )
        n_samples, n_channels, n_times = X.shape
        self.n_channels = n_channels
        self._train_n_tokens = (n_times - self.kernel) // self.stride + 1
        classes, y_idx = np.unique(y, return_inverse=True)
        if len(classes) < 2:
            raise ValueError(
                f"Need at least 2 classes, got {len(classes)}"
            )
        self.classes_ = classes
        self._n_classes = len(classes)
        self.model = _EEGTransformer(
            n_channels=n_channels, n_classes=self._n_classes,
            d_model=self.d_model, n_heads=self.n_heads, n_layers=self.n_layers,
            kernel=self.kernel, stride=self.stride, dropout=self.dropout,
        ).to(self.device)
        opt = optim.AdamW(self.model.parameters(), lr=self.lr,
                          weight_decay=self.weight_decay)
        criterion = nn.CrossEntropyLoss()
        Xt = torch.tensor(X, dtype=torch.float32, device=self.device)
        yt = torch.tensor(y_idx, dtype=torch.long, device=self.device)
        self.model.train()
        for _ in range(self.epochs):
            opt.zero_grad()
            loss = criterion(self.model(Xt), yt)
            loss.backward()
            opt.step()
        self.model.eval()
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        idx = np.argmax(probs, axis=1)
        return self.classes_[idx]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Must call fit() before predict_proba()")
        if X.shape[1] != self.n_channels:
            raise ValueError(
                f"n_channels mismatch: expected {self.n_channels}, "
                f"got {X.shape[1]}"
            )
        if X.shape[2] < self.kernel:
            raise ValueError(
                f"X.shape[2]={X.shape[2]} < kernel={self.kernel}; "
                f"need at least 1 token"
            )
        n_tokens = (X.shape[2] - self.kernel) // self.stride + 1
        if n_tokens > self._train_n_tokens:
            import warnings
            warnings.warn(
                f"n_tokens={n_tokens} > train n_tokens={self._train_n_tokens}; "
                f"RoPE position extrapolation; accuracy may degrade",
                stacklevel=2,
            )
        Xt = torch.tensor(X, dtype=torch.float32, device=self.device)
        self.model.eval()
        with torch.no_grad():
            logits = self.model(Xt)
        return torch.softmax(logits, dim=-1).cpu().numpy()

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            'model_state': self.model.state_dict(),
            'config': {
                'd_model': self.d_model,
                'n_heads': self.n_heads,
                'n_layers': self.n_layers,
                'kernel': self.kernel,
                'stride': self.stride,
                'dropout': self.dropout,
                'n_channels': self.n_channels,
                'n_classes': self._n_classes,
                'train_n_tokens': self._train_n_tokens,
            },
            'classes_': self.classes_,
        }
        torch.save(state, path)

    @classmethod
    def load(cls, path: str | Path) -> 'TransformerDecoder':
        state = torch.load(path, map_location='cpu', weights_only=False)
        cfg = state['config']
        obj = cls(
            d_model=cfg['d_model'], n_heads=cfg['n_heads'],
            n_layers=cfg['n_layers'], kernel=cfg['kernel'],
            stride=cfg['stride'], dropout=cfg['dropout'],
        )
        obj.n_channels = cfg['n_channels']
        obj._n_classes = cfg['n_classes']
        obj._train_n_tokens = cfg['train_n_tokens']
        obj.classes_ = state['classes_']
        obj.model = _EEGTransformer(
            n_channels=cfg['n_channels'], n_classes=cfg['n_classes'],
            d_model=cfg['d_model'], n_heads=cfg['n_heads'],
            n_layers=cfg['n_layers'], kernel=cfg['kernel'],
            stride=cfg['stride'], dropout=cfg['dropout'],
        )
        obj.model.load_state_dict(state['model_state'])
        obj.model.eval()
        return obj
