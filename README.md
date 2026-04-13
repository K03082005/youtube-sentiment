# YouTube Sentiment Analyzer

A full end-to-end MLOps project that analyzes YouTube comment sentiment in real time using a Chrome Extension, Flask API, and a complete automated pipeline with DVC, MLflow, Docker, and GitHub Actions CI/CD.

---

## What it does

Open any YouTube video, click the extension, and instantly see:

- How many comments are **positive**, **negative**, and **neutral**
- A **video verdict** — Worth Watching, Mixed Reviews, Avoid, etc.
- An **audience mood summary** — a natural language description of how viewers actually feel
- Full comment lists per sentiment category with a scrollable tab view

---

## Project Structure

```
youtube-sentiment/
├── data/
│   ├── raw/                  ← original labelled dataset
│   └── processed/            ← balanced train/test splits
├── src/
│   ├── data_ingestion.py     ← fetches live YouTube comments
│   ├── preprocess.py         ← cleans and balances dataset
│   ├── train.py              ← trains TF-IDF + LinearSVC model
│   └── evaluate.py           ← scores model, saves metrics.json
├── app/
│   ├── app.py                ← Flask API (/analyze endpoint)
│   └── app_ui.py             ← Streamlit dashboard
├── extension/                ← Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── style.css
├── models/                   ← saved model.pkl + vectorizer.pkl
├── tests/
│   └── test_api.py
├── .github/workflows/
│   └── ci.yml                ← GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
├── dvc.yaml                  ← DVC pipeline stages
├── params.yaml               ← all hyperparameters
├── MLproject                 ← MLflow entry points
└── requirements.txt
```

---

## Key Results

| Metric | Before fix | After fix |
|---|---|---|
| Negative F1 score | 0.12 | **0.94** |
| Positive F1 score | 0.94 | 0.88 |
| Macro F1 | 0.55 | **0.90** |
| Overall accuracy | 89% | **90%** |

The core problem in most existing YouTube sentiment projects is class imbalance — negative comments were only 11% of the dataset, so models learn to ignore them. This project fixes that by resampling all three classes to equal size before training, bringing negative recall from near zero to 0.95.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data versioning | DVC |
| Experiment tracking | MLflow |
| Text vectorization | TF-IDF (ngrams 1-3) |
| Classifier | LinearSVC |
| API server | Flask |
| Dashboard | Streamlit |
| Browser integration | Chrome Extension (MV3) |
| Containerization | Docker |
| CI/CD | GitHub Actions |

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/K03082005/youtube-sentiment.git
cd youtube-sentiment
pip install -r requirements.txt
```

### 2. Run the ML pipeline

```bash
python src/preprocess.py
python src/train.py
python src/evaluate.py
```

Or run all stages with DVC:

```bash
dvc repro
```

### 3. Start the Flask API

```bash
python -m app.app
```

API runs on `http://127.0.0.1:5001`

### 4. Load the Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select the `extension/` folder
5. Open any YouTube video and click the extension icon

### 5. Run with Docker

```bash
docker build -t youtube-sentiment .
docker run -p 5001:5001 youtube-sentiment
```

### 6. Run with Docker Compose (API + MLflow together)

```bash
docker-compose up
```

- Flask API → `http://localhost:5001`
- MLflow UI → `http://localhost:5000`

---

## ML Pipeline Details

The pipeline has three stages tracked by DVC:

**preprocess** — reads `data/raw/final_ml_dataset.csv`, cleans text, balances all three classes to 2,419 samples each using resampling, splits into train (5,805 rows) and test (1,452 rows).

**train** — fits TF-IDF vectorizer with unigrams, bigrams, and trigrams, trains LinearSVC with `class_weight=balanced`, logs parameters and model to MLflow, saves `model.pkl` and `vectorizer.pkl`.

**evaluate** — runs model on held-out test set, computes per-class F1 scores, saves `metrics.json`, and fails the pipeline if macro F1 drops below 0.70 — preventing bad models from reaching production.

Changing any value in `params.yaml` and running `dvc repro` will automatically rerun only the affected stages.

---

## CI/CD Pipeline

Every push to `main` triggers GitHub Actions to:

1. Install dependencies
2. Run `preprocess.py` → `train.py` → `evaluate.py`
3. Print `metrics.json` to the build log
4. Build the Docker image

If the model fails the quality gate (macro F1 < 0.70), the pipeline stops and deployment does not proceed.

---

## Chrome Extension Features

- Real-time analysis of any YouTube video in one click
- Pie chart drawn with pure HTML Canvas — no CDN dependencies
- Tab switching between Positive, Negative, Neutral comments without re-fetching
- Spam filtering removes bot-like comments before classification
- Video Verdict system with five levels based on sentiment ratios
- Audience Mood Summary detects emotional signals like nostalgia, humor, and criticism

---

## API Reference

**POST** `/analyze`

Request:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

Response:
```json
{
  "total_comments": 200,
  "analyzed": 187,
  "spam_filtered": 13,
  "positive": 94,
  "negative": 41,
  "neutral": 52,
  "verdict": "Generally Positive",
  "verdict_color": "#86efac",
  "mood_summary": "Most viewers are enjoying this video — many are expressing love for the content, people are finding it funny.",
  "positive_comments": ["..."],
  "negative_comments": ["..."],
  "neutral_comments": ["..."]
}
```

---

## What makes this different

Most YouTube sentiment projects use VADER with no ML, ignore class imbalance, and stop at a Streamlit dashboard. This project:

- Fixes the imbalance problem that causes negative F1 to collapse to 0.12
- Builds a real browser extension for live in-page analysis
- Implements a complete MLOps pipeline with reproducible DVC stages
- Replaces broken content-type detection with an audience mood summary
- Packages everything in Docker with automated CI/CD

---

## Future Work

- Deploy Flask API to AWS EC2 so the extension works from any machine
- Add Evidently AI for data drift detection and automatic retraining
- Add Prometheus and Grafana for API monitoring
- Multilingual support for Hindi-English mixed comments
- Sarcasm detection layer

---

## Author

**Kriti** — [github.com/K03082005](https://github.com/K03082005)
