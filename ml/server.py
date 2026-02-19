# server.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import numpy as np
import nltk
import re


# -------------------------
# NLTK Setup (safe)
# -------------------------

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


# -------------------------
# App Setup
# -------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
model.load_state_dict(torch.load("summary_model.pt", map_location="cpu"))
model.eval()

embedder = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------
# Request Schema
# -------------------------

class TextRequest(BaseModel):
    text: str


# -------------------------
# Health Check
# -------------------------

@app.get("/")
def health():
    return {"status": "ML summarizer running"}


# -------------------------
# Summary Endpoint
# -------------------------

@app.post("/summarize")
def summarize(request: TextRequest):
    text = request.text.strip()

    if not text or len(text.split()) < 30:
        raise HTTPException(status_code=400, detail="Text too short")

    # -------------------------
    # Preprocessing Clean Layer
    # -------------------------

    # Remove citation brackets like [1], [3][4]
    text = re.sub(r"\[\d+\]", "", text)

    # Remove multiple spaces / line breaks
    text = re.sub(r"\s+", " ", text)

    # -------------------------
    # Sentence Tokenization
    # -------------------------

    sentences = sent_tokenize(text)

    if len(sentences) == 0:
        raise HTTPException(status_code=400, detail="No valid sentences found")

    # -------------------------
    # Embedding + Inference
    # -------------------------

    embeddings = embedder.encode(sentences)

    X = torch.tensor(np.array(embeddings), dtype=torch.float32)

    with torch.no_grad():
        scores = model(X).numpy().flatten()

    # -------------------------
    # Ranking
    # -------------------------

    ranked = sorted(
        zip(sentences, scores),
        key=lambda x: x[1],
        reverse=True
    )

    # Select top 2 sentences (safe)
    top_k = min(2, len(ranked))
    top_sentences = [s.strip() for s, _ in ranked[:top_k]]

    return {
        "summary": " ".join(top_sentences)
    }