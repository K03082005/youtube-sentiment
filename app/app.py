from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import os
import sys
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from data_ingestion import get_comments

app = Flask(__name__)
CORS(app)

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model      = pickle.load(open(os.path.join(BASE, "models", "model.pkl"),      "rb"))
vectorizer = pickle.load(open(os.path.join(BASE, "models", "vectorizer.pkl"), "rb"))

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

SPAM_PATTERNS = [
    r'^\s*first\s*$', r'^\s*nice\s*$', r'^\s*good\s*$',
    r'^\s*ok\s*$',    r'^\s*lol\s*$',  r'^\s*\d+\s*$',
    r'^\s*[a-zA-Z]\s*$',
]

def is_spam(comment):
    text = comment.strip().lower()
    if len(text) < 3:
        return True
    for pattern in SPAM_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False

def get_verdict(positive, negative, neutral, total):
    if total == 0:
        return "Unknown", "#888"
    pos_pct = positive / total
    neg_pct = negative / total
    if pos_pct >= 0.5 and neg_pct < 0.15:
        return "Worth Watching", "#22c55e"
    elif pos_pct >= 0.35 and neg_pct < 0.25:
        return "Generally Positive", "#86efac"
    elif neg_pct >= 0.4:
        return "Avoid", "#ef4444"
    elif neg_pct >= 0.25:
        return "Mixed Reviews", "#f97316"
    else:
        return "Neutral Reception", "#4f8ef7"

EMOTIONS = {
    "love it":    ["love", "loved", "amazing", "awesome", "perfect", "best", "goat", "fire", "banger"],
    "nostalgic":  ["childhood", "nostalgia", "memories", "miss", "remember", "throwback"],
    "grateful":   ["thank", "thanks", "helped", "helpful", "saved", "appreciate", "grateful"],
    "funny":      ["lol", "haha", "hilarious", "funny", "laughing", "bruh"],
    "impressed":  ["wow", "incredible", "insane", "unbelievable", "shocked", "genius"],
    "critical":   ["waste", "bad", "worst", "terrible", "boring", "disappointing", "trash"],
    "requesting": ["part 2", "more", "next", "please", "upload", "waiting", "need more"],
    "emotional":  ["cry", "crying", "tears", "beautiful", "touched", "emotional", "heart"],
}

def generate_mood_summary(pos_list, neg_list, neu_list, positive, negative, neutral, total):
    if total == 0:
        return "Not enough comments to analyze audience mood."
    pos_pct = positive / total
    neg_pct = negative / total
    neu_pct = neutral  / total
    all_text = " ".join(pos_list + neg_list + neu_list).lower()
    detected = [e for e, kws in EMOTIONS.items() if sum(1 for kw in kws if kw in all_text) >= 2]
    if pos_pct >= 0.6:
        opening = "Viewers are overwhelmingly positive"
    elif pos_pct >= 0.45:
        opening = "Most viewers are enjoying this video"
    elif pos_pct >= 0.3 and neg_pct < 0.2:
        opening = "The audience is mostly appreciative"
    elif neg_pct >= 0.4:
        opening = "Viewers are largely critical of this video"
    elif neg_pct >= 0.25:
        opening = "The audience has mixed feelings"
    elif neu_pct >= 0.5:
        opening = "Viewers are mostly neutral"
    else:
        opening = "The audience response is mixed"
    parts = []
    if "love it"    in detected: parts.append("many are expressing love for the content")
    if "nostalgic"  in detected: parts.append("nostalgia is a strong theme")
    if "grateful"   in detected: parts.append("several found it genuinely helpful")
    if "funny"      in detected: parts.append("people are finding it funny")
    if "impressed"  in detected: parts.append("viewers seem impressed")
    if "emotional"  in detected: parts.append("some are emotionally moved")
    if "requesting" in detected: parts.append("many are asking for more content")
    if "critical"   in detected: parts.append("some viewers are disappointed")
    summary = f"{opening} — {', '.join(parts[:3])}." if parts else f"{opening}."
    if "requesting" in detected and pos_pct >= 0.4:
        summary += " The audience clearly wants more."
    elif neg_pct >= 0.3 and "critical" in detected:
        summary += " Consider checking negative comments for specific concerns."
    return summary

@app.route("/")
def home():
    return "YouTube Analyzer API Running"

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        url  = data.get("url", "")
        if not url:
            return jsonify({"error": "No URL provided"})
        raw_comments = get_comments(url, max_comments=200)
        comments     = list(dict.fromkeys(raw_comments))
        total        = len(comments)
        if total == 0:
            return jsonify({"error": "No comments found"})
        positive = negative = neutral = spam_count = 0
        pos_list, neg_list, neu_list = [], [], []
        for comment in comments:
            if is_spam(comment):
                spam_count += 1
                continue
            cleaned = clean_text(comment)
            if not cleaned or len(cleaned) < 3:
                continue
            pred = model.predict(vectorizer.transform([cleaned]))[0]
            if pred == 1:
                positive += 1
                pos_list.append(comment)
            elif pred == -1:
                negative += 1
                neg_list.append(comment)
            else:
                neutral += 1
                neu_list.append(comment)
        analyzed_total = positive + negative + neutral
        verdict, verdict_color = get_verdict(positive, negative, neutral, analyzed_total)
        mood_summary = generate_mood_summary(
            pos_list, neg_list, neu_list,
            positive, negative, neutral, analyzed_total
        )
        return jsonify({
            "total_comments":    total,
            "analyzed":          analyzed_total,
            "spam_filtered":     spam_count,
            "positive":          positive,
            "negative":          negative,
            "neutral":           neutral,
            "positive_comments": pos_list,
            "negative_comments": neg_list,
            "neutral_comments":  neu_list,
            "verdict":           verdict,
            "verdict_color":     verdict_color,
            "mood_summary":      mood_summary,
        })
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
