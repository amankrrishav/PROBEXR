import torch
import torch.nn as nn
import torch.optim as optim
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datasets import load_dataset
from nltk.tokenize import sent_tokenize
import nltk
import numpy as np

# ----------------------------------
# Setup
# ----------------------------------

nltk.download("punkt")

# Small subset for faster training (increase later)
dataset = load_dataset("cnn_dailymail", "3.0.0", split="train[:2000]")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------------
# Neural Network Model
# ----------------------------------

class SentenceClassifier(nn.Module):
    def __init__(self, input_dim=384):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

model = SentenceClassifier()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# ----------------------------------
# Build Training Data (Human-Aligned)
# ----------------------------------

X = []
y = []

print("Building training dataset...")

for sample in dataset:
    article = sample["article"]
    summary = sample["highlights"]

    article_sentences = sent_tokenize(article)
    summary_sentences = sent_tokenize(summary)

    if not article_sentences or not summary_sentences:
        continue

    # Embed sentences
    article_embeddings = embedder.encode(article_sentences)
    summary_embeddings = embedder.encode(summary_sentences)

    labels = np.zeros(len(article_sentences))

    # For each summary sentence,
    # find most similar article sentence
    for summary_emb in summary_embeddings:
        sims = cosine_similarity(
            article_embeddings,
            summary_emb.reshape(1, -1)
        ).flatten()

        best_index = np.argmax(sims)
        labels[best_index] = 1

    # Store embeddings + labels
    for emb, label in zip(article_embeddings, labels):
        X.append(emb)
        y.append(label)

print("Dataset built.")

# Convert to tensors
X = torch.tensor(np.array(X), dtype=torch.float32)
y = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(1)

print("Training samples:", len(X))

# ----------------------------------
# Training Loop
# ----------------------------------

print("Starting training...")

for epoch in range(5):
    optimizer.zero_grad()

    outputs = model(X)
    loss = criterion(outputs, y)

    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

# ----------------------------------
# Save Model
# ----------------------------------

torch.save(model.state_dict(), "summary_model.pt")

print("Training complete. Model saved as summary_model.pt")