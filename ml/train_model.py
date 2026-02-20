import torch
import torch.nn as nn
import torch.optim as optim
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
from nltk.tokenize import sent_tokenize
from rouge_score import rouge_scorer
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
# Build Training Data (ROUGE-Aligned)
# ----------------------------------

X = []
y = []

print("Building training dataset with ROUGE labeling...")

scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

for sample in dataset:
    article = sample["article"]
    summary = sample["highlights"]

    article_sentences = sent_tokenize(article)

    if not article_sentences:
        continue

    sentence_scores = []

    # Compute ROUGE-L score between each sentence and full summary
    for sentence in article_sentences:
        rouge_score_value = scorer.score(summary, sentence)['rougeL'].fmeasure
        sentence_scores.append(rouge_score_value)

    # Select top 20% highest scoring sentences as positive
    top_n = max(1, int(len(article_sentences) * 0.2))
    top_indices = np.argsort(sentence_scores)[-top_n:]

    # Embed and label
    for i, sentence in enumerate(article_sentences):
        emb = embedder.encode([sentence])[0]
        X.append(emb)
        y.append(1 if i in top_indices else 0)

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