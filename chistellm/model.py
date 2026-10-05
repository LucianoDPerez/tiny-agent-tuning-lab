"""Tiny GPT-style model (~10M params), modernized:
- RoPE rotary positional embeddings (Llama-style)
- RMSNorm instead of LayerNorm
- SwiGLU MLP instead of GELU MLP
- PyTorch SDPA (flash-style fused attention)
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

# ---- Config ----
VOCAB_SIZE = 4096
N_LAYERS = 6
N_HEADS = 6
N_EMBD = 384
BLOCK_SIZE = 256          # context length
DROPOUT = 0.2


class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = x.float().pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return (x * norm.to(x.dtype)) * self.weight


def precompute_rope(dim, block_size, theta=10000.0):
    inv_freq = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
    t = torch.arange(block_size).float()
    freqs = torch.outer(t, inv_freq)                    # (T, dim/2)
    return freqs.cos(), freqs.sin()


def apply_rope(x, cos, sin):
    # x: (B, n_heads, T, head_dim)
    x1, x2 = x.chunk(2, dim=-1)
    cos = cos[None, None, : x.shape[2], :]
    sin = sin[None, None, : x.shape[2], :]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


class Attention(nn.Module):
    def __init__(self):
        super().__init__()
        self.n_heads = N_HEADS
        self.head_dim = N_EMBD // N_HEADS
        self.qkv = nn.Linear(N_EMBD, 3 * N_EMBD, bias=False)
        self.proj = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.dropout = DROPOUT

    def forward(self, x, cos, sin):
        B, T, C = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
        y = F.scaled_dot_product_attention(
            q, k, v, is_causal=True,
            dropout_p=self.dropout if self.training else 0.0,
        )
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y)


class SwiGLU(nn.Module):
    def __init__(self):
        super().__init__()
        hidden = 4 * N_EMBD
        self.w1 = nn.Linear(N_EMBD, hidden, bias=False)
        self.w2 = nn.Linear(hidden, N_EMBD, bias=False)
        self.w3 = nn.Linear(N_EMBD, hidden, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1 = RMSNorm(N_EMBD)
        self.attn = Attention()
        self.norm2 = RMSNorm(N_EMBD)
        self.mlp = SwiGLU()
        self.drop = nn.Dropout(DROPOUT)

    def forward(self, x, cos, sin):
        x = x + self.drop(self.attn(self.norm1(x), cos, sin))
        x = x + self.drop(self.mlp(self.norm2(x)))
        return x


class TinyLLM(nn.Module):
    def __init__(self):
        super().__init__()
        self.tok_emb = nn.Embedding(VOCAB_SIZE, N_EMBD)
        self.dropout = nn.Dropout(DROPOUT)
        self.blocks = nn.ModuleList(Block() for _ in range(N_LAYERS))
        self.norm_f = RMSNorm(N_EMBD)
        self.head = nn.Linear(N_EMBD, VOCAB_SIZE, bias=False)
        self.head.weight = self.tok_emb.weight  # weight tying
        cos, sin = precompute_rope(N_EMBD // N_HEADS, BLOCK_SIZE)
        self.register_buffer("rope_cos", cos)
        self.register_buffer("rope_sin", sin)
        self.apply(self._init)

    def _init(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, std=0.02)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, std=0.02)

    def forward(self, idx, targets=None):
        x = self.dropout(self.tok_emb(idx))
        for block in self.blocks:
            x = block(x, self.rope_cos, self.rope_sin)
        logits = self.head(self.norm_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, VOCAB_SIZE), targets.view(-1))
        return logits, loss

    def num_params(self):
        return sum(p.numel() for p in self.parameters())


if __name__ == "__main__":
    model = TinyLLM()
    print(f"params: {model.num_params()/1e6:.2f}M")
    idx = torch.randint(0, VOCAB_SIZE, (2, 16))
    logits, loss = model(idx, idx)
    print("logits:", logits.shape, "loss:", loss.item())
