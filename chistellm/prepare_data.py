"""Prepare the jokes dataset into training text.

Each document looks like:

    Tema: wifi
    Chiste: ...

Documents are separated by a blank line. The model will learn to complete
"Tema: X\\nChiste:" at inference time.
"""
import re
import random
import pandas as pd

random.seed(42)

df = pd.read_csv("data/chistes.csv")

docs = []
for _, row in df.iterrows():
    text = str(row["text"]).strip()
    if len(text) < 20 or len(text) > 800:
        continue
    # Use the first keyword as the theme; fall back to category.
    keywords = str(row["keywords"]).split(",")
    theme = keywords[0].strip() if keywords and keywords[0].strip() else str(row["category"])
    # Clean up extra whitespace / newlines inside the joke.
    text = re.sub(r"\s*\n\s*", "\n", text)
    docs.append(f"Tema: {theme}\nChiste: {text}")

random.shuffle(docs)

with open("data/train.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(docs))

print(f"Wrote {len(docs)} documents to data/train.txt")
print(docs[0][:300])
