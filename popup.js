let storedData = null;

// ============================================
// WIRE UP TABS (done here, not in HTML onclick)
// This is the real fix — inline onclick passes
// window as `this`, not the button element.
// ============================================
document.getElementById("tab-positive").addEventListener("click", function() { showTab("positive", this); });
document.getElementById("tab-negative").addEventListener("click", function() { showTab("negative", this); });
document.getElementById("tab-neutral" ).addEventListener("click", function() { showTab("neutral",  this); });


// ============================================
// ANALYZE
// ============================================
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const btn = document.getElementById("analyzeBtn");

  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab.url;

  if (!url.includes("youtube.com/watch")) {
    showError("Please open a YouTube video first.");
    return;
  }

  showLoader();
  btn.disabled = true;

  try {
    const response = await fetch("http://127.0.0.1:5001/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!response.ok) throw new Error("Server error " + response.status);

    const data = await response.json();
    if (data.error) { showError(data.error); return; }

    storedData = data;
    renderResults(data);

  } catch (err) {
    showError("Cannot connect. Make sure Flask is running on port 5001.");
    console.error(err);
  } finally {
    btn.disabled = false;
  }
});


// ============================================
// RENDER ALL RESULTS
// ============================================
function renderResults(data) {
  hide("loader");
  hide("errorBox");
  show("results");

  // Metrics
  document.getElementById("posCount").textContent  = data.positive  || 0;
  document.getElementById("negCount").textContent  = data.negative  || 0;
  document.getElementById("neuCount").textContent  = data.neutral   || 0;
  document.getElementById("totalLabel").textContent =
    `${data.analyzed} analyzed · ${data.spam_filtered} spam filtered`;

  // Verdict
  const vBox = document.getElementById("verdictBox");
  vBox.textContent      = data.verdict;
  vBox.style.borderColor = data.verdict_color;
  vBox.style.color       = data.verdict_color;

  // Mood summary
  document.getElementById("moodSummary").textContent =
    data.mood_summary || "Mood analysis unavailable.";

  // Pie chart
  drawPieChart(data.positive || 0, data.negative || 0, data.neutral || 0);

  // Default tab — positive
  showTab("positive", document.getElementById("tab-positive"));
}


// ============================================
// PIE CHART — Pure Canvas
// ============================================
function drawPieChart(pos, neg, neu) {
  const canvas = document.getElementById("pieChart");
  const ctx    = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const total = pos + neg + neu;
  if (total === 0) return;

  const slices = [
    { value: pos, color: "#22c55e" },
    { value: neg, color: "#ef4444" },
    { value: neu, color: "#4f8ef7" }
  ];

  const cx = canvas.width  / 2;
  const cy = canvas.height / 2;
  const r  = 58;
  let start = -Math.PI / 2;

  slices.forEach(s => {
    if (s.value === 0) return;
    const angle = (s.value / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + angle);
    ctx.closePath();
    ctx.fillStyle = s.color;
    ctx.fill();

    const mid = start + angle / 2;
    const pct = Math.round((s.value / total) * 100);
    if (pct > 6) {
      ctx.fillStyle    = "#fff";
      ctx.font         = "bold 10px Arial";
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(pct + "%",
        cx + r * 0.65 * Math.cos(mid),
        cy + r * 0.65 * Math.sin(mid)
      );
    }
    start += angle;
  });

  // Donut hole
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.42, 0, 2 * Math.PI);
  ctx.fillStyle = "#0f0f0f";
  ctx.fill();

  // Center label
  ctx.fillStyle    = "#fff";
  ctx.font         = "bold 12px Arial";
  ctx.textAlign    = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(total, cx, cy - 5);
  ctx.font      = "8px Arial";
  ctx.fillStyle = "#888";
  ctx.fillText("comments", cx, cy + 7);
}


// ============================================
// COMMENT TABS — FIXED
// The root cause of the old bug: inline onclick
// passed `this` as window, not the button.
// Now tabs are wired with addEventListener above
// so `this` is always the correct button element.
// ============================================
function showTab(type, clickedBtn) {
  // Highlight active tab
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  if (clickedBtn) clickedBtn.classList.add("active");

  const container = document.getElementById("commentList");
  container.innerHTML = "";

  if (!storedData) return;

  const keyMap   = {
    positive: "positive_comments",
    negative: "negative_comments",
    neutral:  "neutral_comments"
  };
  const classMap = { positive: "pos", negative: "neg", neutral: "neu" };

  // Always default to [] so we never crash on null/undefined
  const list = Array.isArray(storedData[keyMap[type]])
    ? storedData[keyMap[type]]
    : [];

  if (list.length === 0) {
    container.innerHTML =
      `<div class="no-comments">No ${type} comments found</div>`;
    return;
  }

  list.forEach(c => {
    const div       = document.createElement("div");
    div.className   = "comment-item " + classMap[type];
    div.textContent = c;
    container.appendChild(div);
  });
}


// ============================================
// HELPERS
// ============================================
function showLoader() {
  show("loader");
  hide("errorBox");
  hide("results");
}

function showError(msg) {
  hide("loader");
  const b       = document.getElementById("errorBox");
  b.textContent = msg;
  show("errorBox");
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden");    }