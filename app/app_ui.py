import streamlit as st
import requests
import matplotlib.pyplot as plt
import math

st.set_page_config(page_title="YouTube Analyzer", layout="wide")

st.title("🎬 YouTube Comment Analyzer")

# ======================
# SESSION STATE
# ======================
if "data" not in st.session_state:
    st.session_state.data = None
if "comment_select" not in st.session_state:
    st.session_state.comment_select = "Positive"

# ======================
# INPUT
# ======================
url   = st.text_input("🔗 Enter YouTube URL")
query = st.text_input("🔍 Ask about content (e.g. music, cooking, neet, education)")

# ======================
# ANALYZE BUTTON
# ======================
if st.button("Analyze"):
    if not url:
        st.warning("Please enter a YouTube URL")
    else:
        with st.spinner("Fetching and analyzing comments..."):
            try:
                res = requests.post(
                    "http://127.0.0.1:5001/analyze",
                    json={"url": url, "query": query},
                    timeout=120
                )
                st.session_state.data = res.json()
            except Exception as e:
                st.error(f"Flask not running or error: {e}")
                st.stop()

# ======================
# DATA
# ======================
data = st.session_state.data

if data:
    if "error" in data:
        st.error(data["error"])
        st.stop()

    st.success("✅ Analysis Complete")

    # Safe value helper
    def safe(x):
        try:
            if x is None or math.isnan(float(x)):
                return 0
            return int(x)
        except:
            return 0

    pos = safe(data.get("positive"))
    neg = safe(data.get("negative"))
    neu = safe(data.get("neutral"))

    # ======================
    # METRICS
    # ======================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👍 Positive", pos)
    col2.metric("👎 Negative", neg)
    col3.metric("😐 Neutral",  neu)
    col4.metric("💬 Total",    data.get("total_comments", 0))

    # ======================
    # CONTENT TYPE
    # ======================
    detected = data.get("detected_content_type", "unknown")
    domain_scores = data.get("domain_scores", {})

    st.subheader("🧠 Content Type Detection")
    st.markdown(f"**Detected:** `{detected.upper()}`")

    if domain_scores:
        # Show top 5 domain scores as bar chart
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:6]
        labels  = [d[0].capitalize() for d in sorted_domains]
        values  = [d[1] for d in sorted_domains]

        fig2, ax2 = plt.subplots(figsize=(6, 2.5))
        bars = ax2.barh(labels, values, color="#4f8ef7")
        ax2.set_xlabel("Score")
        ax2.set_title("Domain Relevance")
        ax2.set_xlim(0, max(values) * 1.3 if max(values) > 0 else 1)
        for bar, val in zip(bars, values):
            ax2.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                     f"{val:.2f}", va="center", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig2)

    # ======================
    # QUERY RESULT
    # ======================
    if data.get("query") and data.get("recommendation"):
        st.subheader("🔍 Query Result")
        recommendation = data.get("recommendation", "")
        if "✅" in recommendation:
            st.success(recommendation)
        elif "⚠️" in recommendation:
            st.warning(recommendation)
        else:
            st.error(recommendation)

    # ======================
    # PIE CHART
    # ======================
    st.subheader("📊 Sentiment Distribution")
    values = [pos, neg, neu]
    if sum(values) == 0:
        st.warning("No sentiment data to display")
    else:
        fig, ax = plt.subplots(figsize=(4, 4))
        colors = ["#22c55e", "#ef4444", "#4f8ef7"]
        ax.pie(
            values,
            labels=["Positive", "Negative", "Neutral"],
            autopct="%1.1f%%",
            colors=colors,
            startangle=90
        )
        ax.set_title("Sentiment Breakdown")
        st.pyplot(fig)

    # ======================
    # COMMENTS SECTION
    # ======================
    st.subheader("💬 View Comments")

    option = st.selectbox(
        "Select Type",
        ["Positive", "Negative", "Neutral"],
        index=["Positive", "Negative", "Neutral"].index(st.session_state.comment_select)
    )
    st.session_state.comment_select = option

    if option == "Positive":
        comments = data.get("positive_comments", [])
        st.write(f"Showing {len(comments)} positive comments")
        if not comments:
            st.warning("No positive comments found")
        else:
            for c in comments:
                st.success(c)

    elif option == "Negative":
        comments = data.get("negative_comments", [])
        st.write(f"Showing {len(comments)} negative comments")
        if not comments:
            st.warning("No negative comments found")
        else:
            for c in comments:
                st.error(c)

    else:
        comments = data.get("neutral_comments", [])
        st.write(f"Showing {len(comments)} neutral comments")
        if not comments:
            st.warning("No neutral comments found")
        else:
            for c in comments:
                st.info(c)