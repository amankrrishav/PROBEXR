from datasets import load_dataset
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_cnn_sample(split="train", sample_size=100):
    dataset = load_dataset("cnn_dailymail", "3.0.0", split=split)
    return dataset.select(range(sample_size))


def label_sentences(article, summary):
    sentences = sent_tokenize(article)
    
    vectorizer = TfidfVectorizer().fit(sentences + [summary])
    sentence_vectors = vectorizer.transform(sentences)
    summary_vector = vectorizer.transform([summary])

    similarities = cosine_similarity(sentence_vectors, summary_vector).flatten()

    labels = [1 if i == similarities.argmax() else 0 for i in range(len(sentences))]

    return list(zip(sentences, labels))


if __name__ == "__main__":
    dataset = load_cnn_sample(sample_size=5)

    for item in dataset:
        article = item["article"]
        summary = item["highlights"]

        labeled = label_sentences(article, summary)

        print("\nARTICLE SAMPLE\n")
        for sentence, label in labeled[:5]:
            print(f"{label} :: {sentence}")