import pandas as pd
import re
import yaml
import os
from sklearn.model_selection import train_test_split
from sklearn.utils import resample

params    = yaml.safe_load(open("params.yaml"))["preprocess"]
TEST_SIZE = params["test_size"]
TARGET    = params["target_size"]
MIN_LEN   = params["min_text_length"]

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_and_clean():
    df = pd.read_csv("data/raw/final_ml_dataset.csv", header=None)
    df = df[0].str.split(",", expand=True)
    df.columns = ["clean_text", "label", "usefulness_score",
                  "engagement_score", "final_score"]
    df = df.dropna()
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    df["clean_text"] = df["clean_text"].apply(clean_text)
    df = df[df["clean_text"].str.len() > MIN_LEN]
    return df

def balance(df):
    df_pos = df[df["label"] ==  1]
    df_neg = df[df["label"] == -1]
    df_neu = df[df["label"] ==  0]
    n = min(TARGET, len(df_pos), len(df_neu))
    df_pos_bal = resample(df_pos, replace=False, n_samples=n, random_state=42)
    df_neg_up  = resample(df_neg, replace=True,  n_samples=n, random_state=42)
    df_neu_bal = resample(df_neu, replace=False, n_samples=n, random_state=42)
    return pd.concat([df_pos_bal, df_neg_up, df_neu_bal]).sample(frac=1, random_state=42)

if __name__ == "__main__":
    os.makedirs("data/processed", exist_ok=True)
    df = load_and_clean()
    print(f"Loaded: {len(df)} rows")
    print(f"Before balance: {df['label'].value_counts().to_dict()}")
    df = balance(df)
    print(f"After balance:  {df['label'].value_counts().to_dict()}")
    train, test = train_test_split(
        df, test_size=TEST_SIZE, random_state=42, stratify=df["label"]
    )
    train.to_csv("data/processed/train.csv", index=False)
    test.to_csv("data/processed/test.csv",   index=False)
    print(f"Train: {len(train)} | Test: {len(test)}")
    print("Done — data/processed/train.csv and test.csv saved")