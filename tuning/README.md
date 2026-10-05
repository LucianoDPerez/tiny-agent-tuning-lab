# Tuning pipeline (Spark-X2.5 1.7B → 4B, LoRA on Apple Silicon)

LoRA fine-tuning of `XHToken/Spark-X2.5` for agentic coding: senior-dev
discipline (SOLID, KISS/DRY, idempotency, dedup, backpressure, OWASP, Docker)
plus distilled teacher trajectories with real tool calls.

Hardware: MacBook Air M1 16GB, PyTorch MPS (`transformers + peft + trl`).
No QLoRA on MPS — plain bf16 LoRA (r16), completion-only loss.

## Layout

- `scripts/` — `train_lora.py` (LoRA, `SPARK_MODEL_ID` env-selectable),
  `train_continue.py`, `eval.py` (Q&A rubric), `eval_tool.py` (first-tool
  correctness), `rubric.py`, `make_dataset*.py` (Q&A + trajectory builders),
  `make_text_dataset.py` (chat-template rendering), `convert_trace.py`
  (harness traces → SFT turns)
- `data/` — training sets (`train_4b_v3_text.jsonl` is current),
  eval prompts incl. held-out sets
- `docs/` — `BITACORA.md` (full iteration log with numbers),
  `RECETARIO.md` (reusable recipe)

## Current best

- **4B-V3**: 13 Q&A + distilled Intern-S2 (35B) traces (java/go/docker/ts/python),
  2 epochs, LR 5e-5, ctx 2560. Rubric 30/40, tool-eval 6/6, closes grounded
  1–3 file tasks across languages (see `../benchmarks/MATRIX.md`).
- **1.7B-V11**: best small variant for grounded 1-file tasks.

## Reproduce

```bash
export SPARK_MODEL_ID="XHToken/Spark-X2.5-4B"
python scripts/train_lora.py data/train_4b_v3_text.jsonl out/4b-v3 2 5e-5
# merge + GGUF:
python - <<'EOF'
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained("XHToken/Spark-X2.5-4B", dtype=torch.bfloat16, trust_remote_code=True)
model = PeftModel.from_pretrained(base, "out/4b-v3/final").merge_and_unload()
model.save_pretrained("out/4bv3-merged")
EOF
python ~/llama.cpp/convert_hf_to_gguf.py out/4bv3-merged --outfile spark-4bv3.gguf --outtype f16
llama-quantize spark-4bv3.gguf spark-4bv3-Q4_K_M.gguf Q4_K_M
```

Notes: kill `llama-server` (and quit Docker Desktop) before training —
unified RAM is the bottleneck. Pin `transformers==4.57.1`
(`trl==0.19.1`, `peft==0.14.0`); v5 breaks Spark's custom modeling code.
