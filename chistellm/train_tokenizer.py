"""Train a small BPE tokenizer on the jokes corpus."""
from tokenizers import Tokenizer, models, pre_tokenizers, trainers

VOCAB_SIZE = 4096

with open("data/train.txt", "r", encoding="utf-8") as f:
    text = f.read()

tokenizer = Tokenizer(models.BPE())
tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
trainer = trainers.BpeTrainer(
    vocab_size=VOCAB_SIZE,
    special_tokens=["<|endoftext|>"],
    show_progress=True,
)
tokenizer.train_from_iterator([text], trainer=trainer)
tokenizer.save("tokenizer.json")

encoded = tokenizer.encode("Tema: wifi\nChiste: ¿Hola?")
print("vocab size:", tokenizer.get_vocab_size())
print("sample ids:", encoded.ids[:20])
print("decode roundtrip:", tokenizer.decode(encoded.ids))
