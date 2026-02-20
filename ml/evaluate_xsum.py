# evaluate_xsum.py

import torch
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from rouge_score import rouge_scorer
import nltk
import re

# -------------------------
# Setup
# -------------------------

nltk.download("punkt")

scorer = rouge_scorer.RougeScorer(
    ['rouge1', 'rougeL'],
    use_stemmer=True
)

dataset = load_dataset(
    "xsum",
    split="validation[:200]"
)

# -------------------------
# Load Model
# -------------------------

class SentenceClassifier(torch.nn.Module):
    def __init__(self, input_dim=384):
        super().__init__()
        self.model = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 1),
            torch.nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

model = SentenceClassifier()
model.load_state_dict(torch.load("summary_model_xsum.pt", map_location="cpu"))
model.eval()

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# Evaluation
# -------------------------

model_rouge1 = []
model_rougeL = []

lead_rouge1 = []
lead_rougeL = []

print("Starting XSum evaluation...")

for sample in dataset:

    article = sample["document"]
    reference = sample["summary"]

    article = re.sub(r"\[\d+\]", "", article)
    sentences = sent_tokenize(article)

    if len(sentences) < 3:
        continue

    # -------------------------
    # Model Summary
    # -------------------------

    embeddings = embedder.encode(sentences)
    X = torch.tensor(np.array(embeddings), dtype=torch.float32)

    with torch.no_grad():
        scores = model(X).numpy().flatten()

    ranked = sorted(
        zip(sentences, scores),
        key=lambda x: x[1],
        reverse=True
    )

    # Since XSum summary is 1 sentence,
    # extract top 1 sentence
    model_summary = ranked[0][0]

    model_score = scorer.score(reference, model_summary)
    model_rouge1.append(model_score['rouge1'].fmeasure)
    model_rougeL.append(model_score['rougeL'].fmeasure)

    # -------------------------
    # Lead-1 Baseline
    # -------------------------

    lead_summary = sentences[0]
    lead_score = scorer.score(reference, lead_summary)

    lead_rouge1.append(lead_score['rouge1'].fmeasure)
    lead_rougeL.append(lead_score['rougeL'].fmeasure)


print("\nXSum Evaluation complete.\n")

print("MODEL PERFORMANCE")
print("Average ROUGE-1:", np.mean(model_rouge1))
print("Average ROUGE-L:", np.mean(model_rougeL))

print("\nLEAD-1 BASELINE")
print("Average ROUGE-1:", np.mean(lead_rouge1))
print("Average ROUGE-L:", np.mean(lead_rougeL))