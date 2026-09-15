(() => {
  const state = {
    sessionId: null,
    questions: [],
    currentIdx: 0,
    domainLabel: "",
  };

  const views = {
    landing: document.getElementById("view-landing"),
    session: document.getElementById("view-session"),
    summary: document.getElementById("view-summary"),
  };

  function showView(name) {
    Object.values(views).forEach((v) => v.classList.remove("is-active"));
    views[name].classList.add("is-active");
  }

  // ---- Landing -> start session -------------------------------------
  const setupForm = document.getElementById("setup-form");
  const startBtn = document.getElementById("start-btn");

  setupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const domain = setupForm.querySelector('input[name="domain"]:checked').value;
    const level = setupForm.querySelector('input[name="level"]:checked').value;

    startBtn.disabled = true;
    startBtn.textContent = "Preparing questions…";

    try {
      const res = await fetch("/api/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain, level }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to start session");

      state.sessionId = data.session_id;
      state.questions = data.questions;
      state.currentIdx = 0;
      state.domainLabel = data.domain_label;

      document.getElementById("live-ai-hint").textContent = data.live_ai
        ? ""
        : "Running in offline practice mode.";

      buildRail();
      renderQuestion();
      showView("session");
    } catch (err) {
      alert(err.message || "Something went wrong starting the session.");
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = "Begin session";
    }
  });

  // ---- Session rail ----------------------------------------------------
  function buildRail() {
    document.getElementById("rail-domain").textContent = state.domainLabel;
    const list = document.getElementById("rail-list");
    list.innerHTML = "";
    state.questions.forEach((q, i) => {
      const li = document.createElement("li");
      li.textContent = `Question ${i + 1}`;
      li.dataset.idx = i;
      list.appendChild(li);
    });
    updateRail();
  }

  function updateRail() {
    const items = document.querySelectorAll("#rail-list li");
    items.forEach((li) => {
      const idx = Number(li.dataset.idx);
      li.classList.toggle("is-current", idx === state.currentIdx);
      li.classList.toggle("is-done", idx < state.currentIdx);
    });
  }

  // ---- Question / answer flow ------------------------------------------
  const questionCount = document.getElementById("question-count");
  const questionText = document.getElementById("question-text");
  const answerInput = document.getElementById("answer-input");
  const submitBtn = document.getElementById("submit-answer-btn");
  const feedbackPanel = document.getElementById("feedback-panel");
  const nextBtn = document.getElementById("next-question-btn");

  function renderQuestion() {
    const q = state.questions[state.currentIdx];
    questionCount.textContent = `Question ${state.currentIdx + 1} of ${state.questions.length}`;
    questionText.textContent = q.text;
    answerInput.value = "";
    answerInput.disabled = false;
    feedbackPanel.hidden = true;
    nextBtn.hidden = true;
    submitBtn.hidden = false;
    submitBtn.disabled = false;
    submitBtn.textContent = "Get feedback";
    updateRail();
    answerInput.focus();
  }

  submitBtn.addEventListener("click", async () => {
    const answerText = answerInput.value.trim();
    if (!answerText) {
      answerInput.focus();
      return;
    }

    const q = state.questions[state.currentIdx];
    submitBtn.disabled = true;
    submitBtn.textContent = "Reviewing your answer…";

    try {
      const res = await fetch("/api/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: q.id, answer_text: answerText }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to get feedback");

      document.getElementById("feedback-score").textContent = data.score ?? "—";
      document.getElementById("feedback-text").textContent = data.feedback || "";
      document.getElementById("feedback-strength").textContent = data.strength
        ? `✓ ${data.strength}`
        : "";
      document.getElementById("feedback-improve").textContent = data.improve
        ? `↝ ${data.improve}`
        : "";

      feedbackPanel.hidden = false;
      submitBtn.hidden = true;
      answerInput.disabled = true;

      const isLast = state.currentIdx === state.questions.length - 1;
      nextBtn.hidden = false;
      nextBtn.textContent = isLast ? "See summary →" : "Next question →";
    } catch (err) {
      alert(err.message || "Something went wrong getting feedback.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Get feedback";
    }
  });

  nextBtn.addEventListener("click", async () => {
    const isLast = state.currentIdx === state.questions.length - 1;
    if (isLast) {
      await renderSummary();
      showView("summary");
    } else {
      state.currentIdx += 1;
      renderQuestion();
    }
  });

  // ---- Summary -----------------------------------------------------
  async function renderSummary() {
    const res = await fetch(`/api/session/${state.sessionId}/summary`);
    const data = await res.json();

    document.getElementById("summary-avg").textContent =
      data.average_score !== null ? data.average_score : "—";

    const list = document.getElementById("summary-list");
    list.innerHTML = "";
    data.items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "summary-item";
      li.innerHTML = `
        <div class="summary-item-q">
          <h3>${escapeHtml(item.question_text)}</h3>
          <span class="summary-item-score">${item.score ?? "—"}/10</span>
        </div>
        <p class="summary-item-answer">${escapeHtml(item.answer_text || "")}</p>
        <p class="summary-item-feedback">${escapeHtml(item.feedback || "")}</p>
      `;
      list.appendChild(li);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  document.getElementById("restart-btn").addEventListener("click", () => {
    state.sessionId = null;
    state.questions = [];
    state.currentIdx = 0;
    showView("landing");
  });
})();
