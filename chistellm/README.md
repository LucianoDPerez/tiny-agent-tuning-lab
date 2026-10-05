# TinyLLM — ChisteLLM

A tiny GPT-style LLM (~16M params) trained from scratch in PyTorch to generate
short Spanish jokes given a theme. Built as a learning project to understand
the full LLM pipeline: data prep, BPE tokenizer, transformer architecture,
training loop, and sampling.

## Architecture

Modernized "Llama-enano" (no HuggingFace Trainer, everything explicit):

- RoPE rotary positional embeddings
- RMSNorm
- SwiGLU MLP
- PyTorch SDPA (flash-style attention)
- Weight-tied embeddings
- Context: 256 tokens, vocab 4096

## Files

- `prepare_data.py` — transforms the jokes CSV into `Tema: X / Chiste: ...` docs
- `train_tokenizer.py` — trains a BPE tokenizer (vocab 4096)
- `model.py` — the transformer, written from scratch
- `train.py` — training loop (MPS on Apple Silicon)
- `sample.py` — generate jokes: `python sample.py "wifi"`

## Data

`data/chistes.csv` — ~11.7k Spanish jokes (liopic/chistes-nlp).

## Usage

```bash
python prepare_data.py
python train_tokenizer.py
python train.py
python sample.py "gatos"
```
