import pandas as pd
import pickle
import json
import yaml
from sklearn.metrics import classification_report, f1_score

params = yaml.safe_load(open("params.yaml"))["evaluate"]
MIN_F1 = params["min_f1_threshold"]

if __name__ == "__main__":
    df = pd.read_csv("data/processed/test.csv")
    X, y = df["clean_text"].fillna(""), df["label"]

    model      = pickle.load(open("models/model.pkl", "rb"))
    vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))

    preds    = model.predict(vectorizer.transform(X))
    macro_f1 = f1_score(y, preds, average="macro")
    report   = classification_report(y, preds, target_names=["Negative", "Neutral", "Positive"], output_dict=True)

    metrics = {
        "macro_f1":    round(macro_f1, 4),
        "positive_f1": round(report["Positive"]["f1-score"], 4),
        "negative_f1": round(report["Negative"]["f1-score"], 4),
        "neutral_f1":  round(report["Neutral"]["f1-score"],  4),
        "accuracy":    round(report["accuracy"], 4),
    }
    json.dump(metrics, open("metrics.json", "w"), indent=2)

    print(classification_report(y, preds, target_names=["Negative", "Neutral", "Positive"]))
    print(f"macro_f1: {macro_f1:.4f}")
    if macro_f1 < MIN_F1:
        print("FAILED")
        exit(1)
    print("PASSED")