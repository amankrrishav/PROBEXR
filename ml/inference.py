import torch
import torch.nn as nn
import numpy as np
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import nltk

nltk.download("punkt")

# --------------------------
# Load Embedder
# --------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# --------------------------
# Load Model Architecture
# --------------------------
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
model.load_state_dict(torch.load("summary_model.pt"))
model.eval()


# --------------------------
# Summarization Function
# --------------------------
def generate_summary(text, top_k=2):
    sentences = sent_tokenize(text)

    if not sentences:
        return "Summary unavailable."

    embeddings = embedder.encode(sentences)
    embeddings = torch.tensor(embeddings, dtype=torch.float32)

    with torch.no_grad():
        scores = model(embeddings).numpy().flatten()

    # Get top scoring sentences
    top_indices = np.argsort(scores)[-top_k:]
    top_indices = sorted(top_indices)  # preserve article order

    selected = [sentences[i] for i in top_indices]

    return " ".join(selected)


# --------------------------
# Quick Test Mode
# --------------------------
if __name__ == "__main__":
    sample_text = """
    Artificial intelligence is transforming industries worldwide.
    Companies use machine learning to automate tasks.
    However, ethical concerns about bias and privacy remain significant.
    Governments must regulate AI responsibly.
    """

    summary = generate_summary(sample_text)
    print("\nSUMMARY:\n")
    print(summary)