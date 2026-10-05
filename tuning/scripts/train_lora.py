"""LoRA fine-tune of Spark-X2.5-1.7B with transformers + peft on MPS."""
import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from trl import SFTConfig, SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

import sys
data_file, out_dir, epochs, lr = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
IS_TEXT = data_file.endswith("_text.jsonl")
import os as _os
MODEL_ID = _os.environ.get("SPARK_MODEL_ID", "XHToken/Spark-X2.5-1.7B")
OUT = out_dir

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    dtype=torch.bfloat16,
    trust_remote_code=True,
    attn_implementation="eager",
)
model.config.use_cache = False

lora = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()
model.enable_input_require_grads()

ds = load_dataset("json", data_files=data_file, split="train")

cfg = SFTConfig(
    output_dir=OUT,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=2,
    learning_rate=lr,
    num_train_epochs=epochs,
    logging_steps=5,
    save_strategy="epoch",
    bf16=False,  # MPS is happier without explicit bf16 flag here
    max_length=2560,
    packing=False,
    report_to=[],
    gradient_checkpointing=True,
)

trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tokenizer)
if IS_TEXT:
    # Mask everything except assistant responses: otherwise the model learns
    # to reproduce chat-template boilerplate (e.g. stray </think> tokens).
    from trl import DataCollatorForCompletionOnlyLM
    # Mask everything up to AND including the thinking-close marker: the
    # rendered template emits "<|Bot|></think>" and the model must NOT learn
    # to reproduce template debris (V8 emitted stray </think> tokens).
    trainer.data_collator = DataCollatorForCompletionOnlyLM("<|Bot|></think>", tokenizer=tokenizer)
trainer.train()
trainer.save_model(OUT + "/final")
tokenizer.save_pretrained(OUT + "/final")
print("done ->", OUT + "/final")
