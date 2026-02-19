from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk

nltk.download('punkt')

from nltk.tokenize import sent_tokenize

# -------------------------
# Load CNN/DailyMail
# -------------------------

dataset = load_dataset("cnn_dailymail", "3.0.0", split="train[:1000]")

model = SentenceTransformer("all-MiniLM-L6-v2")

def label_with_embeddings(article, summary):
    sentences = sent_tokenize(article)
    if not sentences:
        return []

    sentence_embeddings = model.encode(sentences)
    summary_embedding = model.encode([summary])[0]

    similarities = cosine_similarity(
        sentence_embeddings,
        summary_embedding.reshape(1, -1)
    ).flatten()

    labeled = []

    for sent, score in zip(sentences, similarities):
        label = 1 if score > 0.5 else 0
        labeled.append((sent, float(score), label))

    return labeled


# -------------------------
# Test on few samples
# -------------------------

for sample in dataset.select(range(3)):
    article = sample["article"]
    summary = sample["highlights"]

    labeled = label_with_embeddings(article, summary)

    print("\nARTICLE SAMPLE\n")
    for sent, score, label in labeled[:5]:
        print(f"{label} ({score:.3f}) :: {sent}")