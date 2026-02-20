# train_model_xsum.py

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from rouge_score import rouge_scorer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import re

# -------------------------
# Setup
# -------------------------

nltk.download("punkt")

dataset = load_dataset(
    "xsum",
    split="train[:5000]"   # start small, scale later
)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

# -------------------------
# Model
# -------------------------

class SentenceClassifier(nn.Module):
    def __init__(self, input_dim=384):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        return self.model(x)

model = SentenceClassifier()

# Class imbalance handling
criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([3.0]))
optimizer = optim.Adam(model.parameters(), lr=0.001)

# -------------------------
# Build Training Data
# -------------------------

X = []
y = []

print("Building XSum training dataset...")

for sample in dataset:

    article = sample["document"]
    summary = sample["summary"]

    article = re.sub(r"\[\d+\]", "", article)
    sentences = sent_tokenize(article)

    if not sentences:
        continue

    sentence_embeddings = embedder.encode(sentences)
    summary_embedding = embedder.encode([summary])[0]

    importance_scores = []

    for index, sentence in enumerate(sentences):

        rouge_score = scorer.score(summary, sentence)['rougeL'].fmeasure

        embedding_score = cosine_similarity(
            [sentence_embeddings[index]],
            [summary_embedding]
        )[0][0]

        position_score = 1 / (1 + index)

        importance = (
            0.4 * rouge_score +
            0.4 * embedding_score +
            0.2 * position_score
        )

        importance_scores.append(importance)

    # Select top 15%
    top_k = max(1, int(len(sentences) * 0.15))
    top_indices = np.argsort(importance_scores)[-top_k:]

    for i, emb in enumerate(sentence_embeddings):
        X.append(emb)
        y.append(1 if i in top_indices else 0)

print("Dataset built.")

X = torch.tensor(np.array(X), dtype=torch.float32)
y = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(1)

print("Training samples:", len(X))

# -------------------------
# Training Loop
# -------------------------

print("Starting training...")

for epoch in range(8):
    optimizer.zero_grad()

    logits = model(X)
    loss = criterion(logits, y)

    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

torch.save(model.state_dict(), "summary_model_xsum.pt")

print("Training complete. Model saved as summary_model_xsum.pt")