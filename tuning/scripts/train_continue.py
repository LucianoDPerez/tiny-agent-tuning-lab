"""Continue LoRA training from an existing adapter (e.g. V4) on new data (trajectories)."""
import sys
import torch
from datasets import load_dataset
from peft import PeftModel
from trl import SFTConfig, SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

data_file, adapter_dir, out_dir, epochs, lr = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5])
import os as _os
MODEL_ID = _os.environ.get("SPARK_MODEL_ID", "XHToken/Spark-X2.5-1.7B")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(MODEL_ID, dtype=torch.bfloat16, trust_remote_code=True, attn_implementation="eager")
base.config.use_cache = False
model = PeftModel.from_pretrained(base, adapter_dir, is_trainable=True)
model.enable_input_require_grads()
model.print_trainable_parameters()

ds = load_dataset("json", data_files=data_file, split="train")
cfg = SFTConfig(
    output_dir=out_dir,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=2,
    learning_rate=lr,
    num_train_epochs=epochs,
    logging_steps=2,
    save_strategy="epoch",
    bf16=False,
    max_length=4096,
    packing=False,
    report_to=[],
    gradient_checkpointing=True,
)
trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tokenizer)
trainer.train()
trainer.save_model(out_dir + "/final")
print("done ->", out_dir + "/final")
