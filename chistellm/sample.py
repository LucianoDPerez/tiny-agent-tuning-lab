"""Generate jokes given a theme:  python sample.py "wifi" """
import sys
import torch
from tokenizers import Tokenizer
from model import TinyLLM, BLOCK_SIZE

device = "mps" if torch.backends.mps.is_available() else "cpu"
tokenizer = Tokenizer.from_file("tokenizer.json")
model = TinyLLM().to(device)
model.load_state_dict(torch.load("tinyllm.pt", map_location=device))
model.eval()

theme = sys.argv[1] if len(sys.argv) > 1 else "wifi"
prompt = f"Tema: {theme}\nChiste:"
idx = torch.tensor([tokenizer.encode(prompt).ids], dtype=torch.long, device=device)

max_tokens = 120
temperature = 0.9
top_k = 40

with torch.no_grad():
    for _ in range(max_tokens):
        idx_cond = idx[:, -BLOCK_SIZE:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / temperature
        v, _ = torch.topk(logits, top_k)
        logits[logits < v[:, [-1]]] = -float("inf")
        probs = torch.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
        if tokenizer.decode([next_id.item()]).strip() == "":
            pass

text = tokenizer.decode(idx[0].tolist())
print(text)
