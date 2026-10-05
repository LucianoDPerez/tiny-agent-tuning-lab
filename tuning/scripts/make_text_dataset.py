"""Render message datasets to plain text via Spark chat template (bypasses arrow nested-type issue)."""
import json
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("XHToken/Spark-X2.5-1.7B", trust_remote_code=True)

TOOLS = [
    {"type": "function", "function": {"name": "search_code", "description": "Search regex in repo", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_str": {"type": "string"}, "new_str": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "run_build", "description": "Run build", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "git_status", "description": "Git status", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
]

import sys
out = sys.argv[1]
ins = sys.argv[2:]
n = 0
with open(out, "w", encoding="utf-8") as f:
    for path in ins:
        has_tools = "traj" in path
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            # normalize: drop empty tool_calls (template renders same without them)
            for m in d["messages"]:
                if not m.get("tool_calls"):
                    m.pop("tool_calls", None)
            text = tok.apply_chat_template(d["messages"], tools=TOOLS if has_tools else None, tokenize=False, add_generation_prompt=False)
            f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
            n += 1
print(f"wrote {n} -> {out}")
