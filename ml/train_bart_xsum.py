# train_bart_xsum.py

from datasets import load_dataset
from transformers import (
    BartTokenizer,
    BartForConditionalGeneration,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq
)
import torch

# -------------------------
# Load Dataset
# -------------------------

dataset = load_dataset("xsum")

# Small subset for CPU testing
train_dataset = dataset["train"].select(range(2000))
val_dataset = dataset["validation"].select(range(500))

# -------------------------
# Load Model & Tokenizer
# -------------------------

model_name = "facebook/bart-base"

tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)

# -------------------------
# Tokenization
# -------------------------

def preprocess_function(examples):
    inputs = examples["document"]
    targets = examples["summary"]

    model_inputs = tokenizer(
        inputs,
        max_length=512,
        truncation=True,
        padding="max_length"
    )

    labels = tokenizer(
        targets,
        max_length=64,
        truncation=True,
        padding="max_length"
    )

    # Replace padding token id's in labels with -100
    # so they are ignored in loss computation
    labels_ids = labels["input_ids"]
    labels_ids = [
        [(token if token != tokenizer.pad_token_id else -100) for token in label]
        for label in labels_ids
    ]

    model_inputs["labels"] = labels_ids
    return model_inputs

train_dataset = train_dataset.map(
    preprocess_function,
    batched=True,
    remove_columns=train_dataset.column_names
)

val_dataset = val_dataset.map(
    preprocess_function,
    batched=True,
    remove_columns=val_dataset.column_names
)

# -------------------------
# Data Collator
# -------------------------

data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model
)

# -------------------------
# Training Setup
# -------------------------

training_args = TrainingArguments(
    output_dir="./bart_xsum",
    eval_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=2,
    weight_decay=0.01,
    save_total_limit=1,
    logging_steps=100,
    fp16=False  # important for CPU
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=data_collator
)

# -------------------------
# Train
# -------------------------

trainer.train()

# -------------------------
# Save Model
# -------------------------

trainer.save_model("./bart_xsum_model")
tokenizer.save_pretrained("./bart_xsum_model")