# server.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
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

    text = re.sub(r"\[\d+\]", "", text)  # remove citations like [1]
    text = re.sub(r"\s+", " ", text)     # normalize whitespace

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
    # Advanced Ranking System
    # -------------------------

    scored_sentences = []

    for index, (sentence, model_score) in enumerate(zip(sentences, scores)):

        # Positional bias
        position_bias = 0.15 * (1 / (1 + index))

        # Length normalization penalty
        length_penalty = len(sentence.split()) / 40

        final_score = (
            0.75 * model_score +
            0.3 * position_bias -
            0.05 * length_penalty
        )

        scored_sentences.append((sentence, final_score))

    ranked = sorted(
        scored_sentences,
        key=lambda x: x[1],
        reverse=True
    )

    # -------------------------
    # Redundancy Filtering + Dynamic Top-K
    # -------------------------

    selected = []
    selected_embeddings = []

    for sentence, score in ranked:

        if len(selected) == 0:
            selected.append(sentence)
            selected_embeddings.append(embedder.encode([sentence])[0])
            continue

        current_emb = embedder.encode([sentence])[0]

        similarities = cosine_similarity(
            [current_emb],
            selected_embeddings
        )[0]

        # Skip if too similar
        if max(similarities) > 0.75:
            continue

        selected.append(sentence)
        selected_embeddings.append(current_emb)

        # Dynamic stopping logic
        if len(sentences) < 6 and len(selected) == 1:
            break
        elif len(sentences) < 15 and len(selected) == 2:
            break
        elif len(selected) == 3:
            break

    return {
        "summary": " ".join(selected)
    }