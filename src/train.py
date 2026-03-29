"""
save_model.py
Run this to retrain and save the improved model.
It fixes:
  1. Imbalanced dataset (negative was only 11%)
  2. Adds text cleaning (removes numbers, URLs, special chars)
  3. Uses TF-IDF with ngrams (1,2,3) for better understanding
  4. class_weight='balanced' for fair classification
"""
""""
import pandas as pd
import pickle
import re
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from sklearn.metrics import classification_report


# =============================================
# LOAD DATA
# =============================================
df = pd.read_csv("final_ml_dataset.csv", header=None)
df = df[0].str.split(",", expand=True)
df.columns = ["clean_text", "label", "usefulness_score", "engagement_score", "final_score"]

df = df.dropna()
df["label"] = pd.to_numeric(df["label"], errors="coerce")
df = df.dropna(subset=["label"])
df["label"] = df["label"].astype(int)

print("Original distribution:")
print(df["label"].value_counts())


# =============================================
# CLEAN TEXT (VERY IMPORTANT)
# =============================================
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"http\S+", "", text)           # remove URLs
    text = re.sub(r"[^a-zA-Z\s]", " ", text)      # keep only letters
    text = re.sub(r"\s+", " ", text).strip()       # normalize spaces
    return text

df["clean_text"] = df["clean_text"].apply(clean_text)
df = df[df["clean_text"].str.len() > 2]           # drop empty after cleaning


# =============================================
# BALANCE DATASET
# =============================================
df_pos = df[df["label"] == 1]
df_neg = df[df["label"] == -1]
df_neu = df[df["label"] == 0]

target_size = len(df_pos)  # match positive class size

df_neg_up  = resample(df_neg, replace=True,  n_samples=target_size, random_state=42)
df_neu_bal = resample(df_neu, replace=False, n_samples=target_size, random_state=42)

df_balanced = pd.concat([df_pos, df_neg_up, df_neu_bal]).sample(frac=1, random_state=42)

print("\nAfter balancing:")
print(df_balanced["label"].value_counts())


# =============================================
# TFIDF WITH NGRAMS
# =============================================
vectorizer = TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 3),       # understands "not good", "very bad", "love this"
    sublinear_tf=True,         # log scaling reduces dominance of frequent words
    min_df=2,
    strip_accents="unicode",
    analyzer="word"
)

X = df_balanced["clean_text"]
y = df_balanced["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)


# =============================================
# TRAIN SVM
# =============================================
model = LinearSVC(C=1.0, class_weight="balanced", max_iter=2000)
model.fit(X_train_vec, y_train)

preds = model.predict(X_test_vec)

print("\n=== MODEL PERFORMANCE ===")
print(classification_report(y_test, preds, target_names=["Negative", "Neutral", "Positive"]))


# =============================================
# SAVE
# =============================================
pickle.dump(model,      open("model.pkl",      "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("✅ model.pkl and vectorizer.pkl saved successfully!")"""

import pandas as pd
import pickle
import re
import yaml
import os
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report

params = yaml.safe_load(open("params.yaml"))["train"]

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df = pd.read_csv("data/processed/train.csv") if __name__ != "__main__" else None

if __name__ == "__main__":
    df = pd.read_csv("data/processed/train.csv")
    df["clean_text"] = df["clean_text"].fillna("").apply(clean_text)
    df = df[df["clean_text"].str.len() > 2]
    X, y = df["clean_text"], df["label"]

    vectorizer = TfidfVectorizer(
        max_features=params["max_features"],
        ngram_range=tuple(params["ngram_range"]),
        sublinear_tf=True, min_df=2,
        strip_accents="unicode", analyzer="word"
    )
    X_vec = vectorizer.fit_transform(X)

    model = LinearSVC(C=params["C"], class_weight="balanced", max_iter=params["max_iter"])
    model.fit(X_vec, y)

    preds = model.predict(X_vec)
    print(classification_report(y, preds, target_names=["Negative", "Neutral", "Positive"]))

    os.makedirs("models", exist_ok=True)
    pickle.dump(model,      open("models/model.pkl", "wb"))
    pickle.dump(vectorizer, open("models/vectorizer.pkl", "wb"))
    print("Saved to models/")