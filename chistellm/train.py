"""Train the tiny LLM on the jokes corpus."""
import time
import torch
from tokenizers import Tokenizer
from model import TinyLLM, VOCAB_SIZE, BLOCK_SIZE

BATCH_SIZE = 16
MAX_ITERS = 1500
LR = 1e-4
EVAL_EVERY = 500
SAVE_PATH = "tinyllm.pt"

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("device:", device)

tokenizer = Tokenizer.from_file("tokenizer.json")
with open("data/train.txt", "r", encoding="utf-8") as f:
    data = torch.tensor(tokenizer.encode(f.read()).ids, dtype=torch.long)
print("tokens:", len(data))

n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]


def get_batch(split):
    src = train_data if split == "train" else val_data
    ix = torch.randint(len(src) - BLOCK_SIZE, (BATCH_SIZE,))
    x = torch.stack([src[i : i + BLOCK_SIZE] for i in ix])
    y = torch.stack([src[i + 1 : i + BLOCK_SIZE + 1] for i in ix])
    return x.to(device), y.to(device)


model = TinyLLM().to(device)
print(f"params: {model.num_params()/1e6:.2f}M")
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.1)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_ITERS)

t0 = time.time()
for it in range(MAX_ITERS):
    if it % EVAL_EVERY == 0 or it == MAX_ITERS - 1:
        model.eval()
        with torch.no_grad():
            x, y = get_batch("val")
            _, val_loss = model(x, y)
        model.train()
        print(f"iter {it:5d} | val loss {val_loss.item():.4f} | {time.time()-t0:.0f}s")

    x, y = get_batch("train")
    _, loss = model(x, y)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
    scheduler.step()

torch.save(model.state_dict(), SAVE_PATH)
print(f"saved to {SAVE_PATH} in {time.time()-t0:.0f}s")
