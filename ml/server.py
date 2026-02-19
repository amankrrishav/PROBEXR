# server.py

from fastapi import FastAPI
from pydantic import BaseModel
import torch
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import numpy as np
import nltk

nltk.download("punkt")

app = FastAPI()

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
model.load_state_dict(torch.load("summary_model.pt", map_location="cpu"))
model.eval()

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# Request Schema
# -------------------------

class TextRequest(BaseModel):
    text: str

# -------------------------
# Summary Endpoint
# -------------------------

@app.post("/summarize")
def summarize(request: TextRequest):
    text = request.text

    if not text or len(text.split()) < 30:
        return {"error": "Text too short"}

    sentences = sent_tokenize(text)
    embeddings = embedder.encode(sentences)

    X = torch.tensor(np.array(embeddings), dtype=torch.float32)
    with torch.no_grad():
        scores = model(X).numpy().flatten()

    ranked = sorted(
        zip(sentences, scores),
        key=lambda x: x[1],
        reverse=True
    )

    top_sentences = [s for s, _ in ranked[:2]]

    return {
        "summary": " ".join(top_sentences)
    }