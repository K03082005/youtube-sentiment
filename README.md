# YouTube Sentiment Analyzer


A full end-to-end MLOps system that analyzes YouTube comment sentiment in real time through a Chrome Extension, Flask API, and an automated machine learning pipeline.

---

## What it does

Open any YouTube video, click the extension, and instantly see:

- How many comments are **positive**, **negative**, and **neutral**
- A **video verdict** — Worth Watching, Mixed Reviews, Avoid, etc.
- An **audience mood summary** — a natural language description of how the audience actually feels, based on detected emotional signals in the comments
- Full comment lists per sentiment category with tab switching

---

## The Problem This Solves

Most existing YouTube sentiment tools either use rule-based VADER with no machine learning, or train models on generic datasets like IMDB or Twitter — which have very different language from YouTube comments.

The deeper issue is **class imbalance**. In a typical YouTube comment dataset, negative comments make up only 10–12% of the data. A model trained on this will learn to ignore negative comments entirely — achieving high overall accuracy while completely failing to detect criticism or controversy.

This project addresses that directly.

---

## Key Results

| Metric | Baseline (imbalanced) | This project |
|---|---|---|
| Negative F1 score | 0.12 | **0.94** |
| Positive F1 score | 0.94 | 0.88 |
| Macro F1 | 0.55 | **0.90** |
| Overall accuracy | 89% | **90%** |

Macro F1 — which treats all classes equally — increased from 0.55 to 0.90 after fixing the imbalance. This is the correct metric for this problem. Overall accuracy staying at ~90% while negative recall jumped from near-zero to 0.95 confirms the fix worked without degrading general performance.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data versioning | DVC | Tracks every version of dataset and model |
| Experiment tracking | MLflow | Logs all training runs with parameters and metrics |
| Text vectorization | TF-IDF (ngrams 1-3) | Converts comment text to numeric features |
| Classifier | LinearSVC | Fast, effective for text classification |
| Imbalance fix | Resampling | Balances all three classes to equal size |
| API server | Flask | Serves predictions over HTTP |
| Dashboard | Streamlit | Visual interface for exploration |
| Browser integration | Chrome Extension MV3 | Live analysis on YouTube pages |
| Containerization | Docker | Reproducible deployment anywhere |
| CI/CD | GitHub Actions | Automated test, train, evaluate, deploy |

---

## Pipeline Architecture

The ML pipeline runs in three stages managed by DVC:

**Stage 1 — Preprocess**
Reads the labelled dataset, cleans text by removing URLs and special characters, resamples all three classes to equal size (2,419 each), and splits into train (5,805 rows) and test (1,452 rows) sets.

**Stage 2 — Train**
Fits a TF-IDF vectorizer with unigram, bigram, and trigram features, trains a LinearSVC classifier with balanced class weights, and logs all parameters and artifacts to MLflow.

**Stage 3 — Evaluate**
Runs the model on the held-out test set, computes per-class precision, recall, and F1, saves results to `metrics.json`, and enforces a quality gate — if macro F1 drops below 0.70 the pipeline fails and deployment is blocked.

All hyperparameters live in `params.yaml`. Changing any value and running `dvc repro` reruns only the affected stages automatically.

---

## CI/CD Flow

Every push to `main` triggers GitHub Actions to run the full pipeline automatically:

```
push to main
    ↓
install dependencies
    ↓
preprocess → train → evaluate
    ↓
check metrics.json — fail if F1 < 0.70
    ↓
build Docker image
    ↓
deployment
```

No manual steps. No silent bad models reaching production.

---

## Chrome Extension Design

Built with Manifest V3. Key decisions:

- **No CDN dependencies** — pie chart drawn with pure HTML Canvas API to avoid Content Security Policy violations
- **In-memory tab state** — comment data stored in a JS variable so switching tabs does not re-fetch from the API
- **Spam filtering** — comments under 3 characters or matching bot patterns are removed before classification
- **Audience Mood Summary** — replaces the unreliable content-type classifier with emotion signal detection across the full comment set

---

## What makes this different from existing work

| Gap in existing projects | How this project addresses it |
|---|---|
| Class imbalance ignored | Resampling brings all classes to equal size |
| Trained on wrong domain | Dataset built from real YouTube comments |
| No real-time browser integration | Chrome Extension analyzes live YouTube pages |
| Content type detection broken | Replaced with audience mood summary |
| No full MLOps pipeline | DVC + MLflow + Docker + CI/CD all integrated |
| No quality gate | Pipeline fails automatically if model degrades |

---

## Project Structure

```
youtube-sentiment/
├── data/
│   ├── raw/                  ← original labelled dataset
│   └── processed/            ← balanced train/test splits (generated)
├── src/
│   ├── data_ingestion.py     ← live comment fetching
│   ├── preprocess.py         ← cleaning and balancing
│   ├── train.py              ← model training
│   └── evaluate.py           ← evaluation and quality gate
├── app/
│   ├── app.py                ← Flask API
│   └── app_ui.py             ← Streamlit dashboard
├── extension/                ← Chrome Extension source
├── models/                   ← trained artifacts
├── tests/                    ← API tests
├── .github/workflows/        ← CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── dvc.yaml
├── params.yaml
└── MLproject
```

---

## Future Work

- Deploy to AWS EC2 so the extension works from any machine, not just localhost
- Add Evidently AI for data drift detection and automatic retraining triggers
- Add Prometheus and Grafana for API latency and error rate monitoring
- Multilingual support for Hindi-English mixed comments common in Indian YouTube
- Sarcasm detection as an additional classification layer

---
