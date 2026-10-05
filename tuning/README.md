# Spark-X2.5-1.7B Fine-tune

Fine-tune of XHToken/Spark-X2.5-1.7B with Lucho's coding conventions
(clean architecture, SOLID, KISS/DRY, idempotency, dedup, OWASP, Docker).

Target: concise, direct answers; no overthinking loops.

## Why MLX

- On Apple Silicon, `mlx-lm` + QLoRA is the fast path (bitsandbytes/peft does
  NOT give you QLoRA on MPS — it barely runs).
- 1.7B model QLoRA on M1 Air 16GB: feasible, ~1-2h for a small curated set.

## Layout

- `data/train.jsonl` — curated prompt/response pairs
- `scripts/train.sh` — mlx-lm lora command
- `scripts/export_gguf.sh` — convert fine-tuned model to GGUF for llama.cpp

## Steps

1. Curate dataset (see `data/`)
2. `mlx_lm.lora` training
3. Fuse adapters → export to llama.cpp GGUF
4. Quantize Q4_K_M, test on M1 Air
