📘 ReadPulse — Neural Hybrid Summarizer

ReadPulse is a hybrid neural extractive summarization system that combines:
	•	Sentence embeddings
	•	A trained neural classifier
	•	Structural ranking heuristics
	•	Redundancy filtering
	•	A React frontend interface

It produces adaptive summaries along with reading time and difficulty analysis.

⸻

🚀 Project Overview

ReadPulse consists of:

🖥 Frontend (React + Vite)
	•	Paste text or URL
	•	Calculates reading time
	•	Computes difficulty score (Flesch-Kincaid based)
	•	Calls ML backend for summary
	•	Displays adaptive summary

🧠 ML Backend (FastAPI + PyTorch)
	•	Sentence embedding via all-MiniLM-L6-v2
	•	Custom trained neural classifier (summary_model.pt)
	•	Advanced ranking logic:
	•	Neural semantic scoring
	•	Positional bias
	•	Length normalization
	•	Redundancy filtering
	•	Dynamic summary length

⸻

🏗 Architecture
User Input (Text / URL)
        ↓
React Frontend
        ↓
POST /summarize
        ↓
FastAPI ML Server
        ↓
Sentence Embeddings
        ↓
Neural Classifier
        ↓
Advanced Ranking Engine
        ↓
Filtered Summary Output

🧠 Model Design

Training Data
	•	Dataset: CNN/DailyMail
	•	Sentences labeled via semantic similarity to highlights
	•	Neural classifier trained using binary classification

Model Architecture
Linear(384 → 128)
ReLU
Linear(128 → 1)
Sigmoid

Inference Pipeline
	1.	Clean text (remove citations, normalize whitespace)
	2.	Sentence tokenization
	3.	Sentence embeddings
	4.	Neural scoring
	5.	Structural scoring:
	•	Position bias
	•	Length penalty
	6.	Redundancy filtering (cosine similarity threshold)
	7.	Dynamic top-k selection

⸻

📂 Project Structure
readpulse/
│
├── src/                  # React frontend
│   ├── App.jsx
│   ├── utils/
│   │   ├── readingTime.js
│   │   ├── difficulty.js
│   │   ├── summarizer.js
│   │   └── fetchFromUrl.js
│   └── components/
│       └── DifficultyBar.jsx
│
├── ml/
│   ├── server.py
│   ├── train.py
│   ├── summary_model.pt
│
├── ml_env/               # Python virtual environment

🔍 Current Capabilities
	•	Adaptive extractive summarization
	•	Redundancy-aware selection
	•	Position-aware ranking
	•	Length-aware scoring
	•	Dynamic summary size
	•	Reading time estimation
	•	Difficulty scoring

⸻

📈 Current Limitations
	•	Extractive only (no compression/paraphrasing)
	•	No fine-tuned abstractive model
	•	No reinforcement training
	•	Limited dataset subset used during training

⸻

🔮 Planned Improvements
	•	Redundancy-aware reweight tuning
	•	Paragraph-level ranking
	•	Hybrid compression layer
	•	Optional abstractive fine-tuning
	•	Model evaluation metrics (ROUGE)

⸻

🧠 Why This Is Different

Unlike simple frequency-based summarizers, ReadPulse:
	•	Uses semantic embeddings
	•	Trains a neural classifier
	•	Combines ML with structural heuristics
	•	Separates inference from training cleanly

It is a hybrid neural ranking engine.
*************************************