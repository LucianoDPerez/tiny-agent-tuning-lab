"""Tool-use eval: does the model emit the right first tool call with the exact repo path?"""
import json
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path, out_path = sys.argv[1], sys.argv[2]

TOOLS = [
    {"type": "function", "function": {"name": "search_code", "description": "Search regex in repo", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}, "required": ["path", "pattern"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_str": {"type": "string"}, "new_str": {"type": "string"}}, "required": ["path", "old_str", "new_str"]}}},
    {"type": "function", "function": {"name": "run_build", "description": "Run build", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "git_status", "description": "Git status", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
]

CASES = [
    ("En el repo /Users/luchop/PROYECTOS IA/TurnoSmart, encontrá la card del dashboard y hacela clickeable a /app/clientes.", "search_code", "/Users/luchop/PROYECTOS IA/TurnoSmart"),
    ("En el repo /Users/luchop/PROYECTOS IA/TurnoSmart, buscá dónde se usa 'Servicios activos'.", "search_code", "/Users/luchop/PROYECTOS IA/TurnoSmart"),
    ("En el repo /Users/luchop/PROYECTOS IA/TurnoSmart, decime el estado git antes de proponer cambios.", "git_status", "/Users/luchop/PROYECTOS IA/TurnoSmart"),
]

SYSTEM = "Sos un dev senior / arquitecto de software. Respondés directo al punto, sin divagar ni dar mil vueltas."

if "final" in model_path or "checkpoint" in model_path or "v" in model_path.split("/")[-2]:
    from peft import PeftModel
    import os as _os
    base_id = _os.environ.get("SPARK_MODEL_ID", "XHToken/Spark-X2.5-1.7B")
    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(base_id, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager")
    import os
    ap = model_path if os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, "adapter_config.json")) else None
    if ap:
        model = PeftModel.from_pretrained(base, ap).to("mps").eval()
    else:
        model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager").to("mps").eval()
else:
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager").to("mps").eval()

score = 0
results = []
for task, want_tool, want_path in CASES:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    prompt = tokenizer.apply_chat_template(messages, tools=TOOLS, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("mps")
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=200, do_sample=False, temperature=None, top_p=None)
    text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
    ok_tool = f"<tool_call>{want_tool}" in text
    ok_path = want_path in text
    bad_path = "PROYECTOS-IA" in text or "Users-luchop" in text
    s = (1 if ok_tool else 0) + (1 if ok_path and not bad_path else 0)
    score += s
    results.append({"task": task, "want": want_tool, "ok_tool": ok_tool, "ok_path": ok_path and not bad_path, "gen": text[:400]})
    print(f"[{'OK' if s==2 else '--'}] want={want_tool} tool={ok_tool} path={ok_path and not bad_path}\n{text[:300]}\n")

print(f"TOOL SCORE: {score}/{len(CASES)*2}")
with open(out_path, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
