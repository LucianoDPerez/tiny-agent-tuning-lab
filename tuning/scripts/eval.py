"""Run eval prompts against a model (base or fine-tuned) and dump outputs."""
import json
import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = sys.argv[1]           # e.g. XHToken/Spark-X2.5-1.7B or out/spark-lora/final
out_path = sys.argv[2]             # e.g. eval_base.jsonl

if os.path.isdir(os.path.join(model_path, "adapter_config.json")) or model_path.endswith("/final"):
    from peft import PeftModel
    base_id = __import__("os").environ.get("SPARK_MODEL_ID", "XHToken/Spark-X2.5-1.7B")
    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(base_id, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager")
    model = PeftModel.from_pretrained(base, model_path).to("mps").eval()
else:
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager").to("mps").eval()

SYSTEM = (
    "Sos un dev senior / arquitecto de software. Antes de actuar, analizás: "
    "qué archivos y dependencias tocas, qué contratos rompes, qué patrones aplican "
    "(SOLID, DRY, KISS, idempotencia, deduplicación, backpressure, OWASP Top 10). "
    "Respondés directo al punto, sin divagar ni dar mil vueltas."
)
results = []
with open(os.environ.get("EVAL_PROMPTS", "data/eval_prompts.jsonl"), encoding="utf-8") as f:
    for line in f:
        messages = json.loads(line)["messages"]
        messages[0]["content"] = SYSTEM
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to("mps")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=300, do_sample=False, temperature=None, top_p=None)
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        results.append({"prompt": messages[-1]["content"], "response": text})
        print(f"\n### {messages[-1]['content']}\n{text}\n")

with open(out_path, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("wrote", out_path)
