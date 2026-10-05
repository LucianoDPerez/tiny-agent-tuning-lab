"""Convert harness stream-event traces into Spark SFT messages.

Input: AGENT_LUCHO_TRACE_PATH jsonl with stream_events:
  ("text", str) | ("call", {name, args, id}) | ("result", {tool_call_id, content})
Output: {"messages": [...]} with assistant tool_calls + tool roles, ready for
make_text_dataset.py rendering.
"""
import json
import sys

SYSTEM = (
    "Sos un dev senior / arquitecto de software. Antes de actuar, analizás: "
    "qué archivos y dependencias tocas, qué contratos rompes, qué patrones aplican "
    "(SOLID, DRY, KISS, idempotencia, deduplicación, backpressure, OWASP Top 10). "
    "Respondés directo al punto, sin divagar ni dar mil vueltas."
)


def tc(name, args, _id=None):
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {"_raw": args}
    d = {"type": "function", "function": {"name": name, "arguments": args if isinstance(args, dict) else {"_raw": str(args)}}}
    return d


def convert(trace_path, out_path, min_calls=2):
    n = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for line in open(trace_path, encoding="utf-8"):
            t = json.loads(line)
            evs = t.get("stream_events", [])
            if not evs:
                continue
            calls = [e for e in evs if e["kind"] == "call"]
            if len(calls) < min_calls:
                continue
            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": t.get("user_input", "")},
            ]
            cur_text: list[str] = []
            cur_calls: list[dict] = []

            def flush_assistant():
                if cur_text or cur_calls:
                    m = {"role": "assistant", "content": "".join(cur_text)}
                    if cur_calls:
                        m["tool_calls"] = list(cur_calls)
                    messages.append(m)
                    cur_text.clear()
                    cur_calls.clear()

            for e in evs:
                k, p = e["kind"], e["payload"]
                if k == "text":
                    cur_text.append(p if isinstance(p, str) else str(p))
                elif k == "call":
                    cur_calls.append(tc(p.get("name"), p.get("args", {}), p.get("id")))
                elif k == "result":
                    flush_assistant()
                    content = p.get("content", "") if isinstance(p, dict) else str(p)
                    messages.append({"role": "tool", "content": str(content)[:3000]})
            flush_assistant()
            out.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            n += 1
    print(f"converted {n} turns -> {out_path}")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
