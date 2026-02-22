"""
Legacy / experimental: hybrid extractive + BART summarizer.
Not used by the main server. Requires PyTorch, sentence-transformers, transformers, nltk.
Run from backend/ with: python -m archive.summarizer (and summary_model.pt in cwd if needed).
"""
import torch
import numpy as np
import re
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from transformers import BartTokenizer, BartForConditionalGeneration

# -------------------------
# Load Extractive Model
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

extractive_model = SentenceClassifier()
extractive_model.load_state_dict(
    torch.load("summary_model.pt", map_location="cpu")
)
extractive_model.eval()

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# Load PRETRAINED bart-large-cnn
# -------------------------

model_name = "facebook/bart-large-cnn"

tokenizer = BartTokenizer.from_pretrained(model_name)
bart_model = BartForConditionalGeneration.from_pretrained(model_name)
bart_model.eval()

# -------------------------
# Test Paragraph
# -------------------------

text = """
The government unveiled a new climate policy aiming to cut national carbon emissions by 40% by 2035. The proposal includes subsidies for renewable energy projects, higher taxes on fossil fuel producers, and stricter efficiency standards for vehicles. Analysts estimate the plan could cost $120 billion over the next decade. Environmental groups welcomed the move but warned that implementation timelines remain unclear. Industry representatives criticized the tax increases, arguing they could hurt domestic manufacturing. The administration said the reforms are necessary to meet international climate commitments and avoid long-term economic damage.
"""

# -------------------------
# CLEAN
# -------------------------

text = re.sub(r"\[\d+\]", "", text)
text = re.sub(r"\s+", " ", text)

sentences = sent_tokenize(text)

# -------------------------
# Extractive Ranking
# -------------------------

embeddings = embedder.encode(sentences)
X = torch.tensor(np.array(embeddings), dtype=torch.float32)

with torch.no_grad():
    scores = extractive_model(X).numpy().flatten()

ranked = sorted(zip(sentences, scores), key=lambda x: x[1], reverse=True)

# Select top 4 instead of 5 (cleaner draft)
top_sentences = [s for s, _ in ranked[:4]]
top_sentences = sorted(top_sentences, key=lambda s: sentences.index(s))

extractive_summary = " ".join(top_sentences)

print("\n--- EXTRACTIVE DRAFT ---\n")
print(extractive_summary)

# -------------------------
# Generative Rewrite (Production-Level)
# -------------------------

inputs = tokenizer(
    extractive_summary,
    return_tensors="pt",
    max_length=512,
    truncation=True
)

with torch.no_grad():
    summary_ids = bart_model.generate(
        inputs["input_ids"],
        max_length=300,
        min_length=120,
        num_beams=5,
        no_repeat_ngram_size=3,
        repetition_penalty=1.2,
        length_penalty=1.2,
        early_stopping=True
    )

final_summary = tokenizer.decode(
    summary_ids[0],
    skip_special_tokens=True,
    clean_up_tokenization_spaces=True
)

print("\n--- FINAL HYBRID SUMMARY (PRODUCTION CONFIG) ---\n")
print(final_summary)
