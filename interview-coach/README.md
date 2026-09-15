# Rehearsal — AI Interview Preparation Coach

A practice interview tool: pick a track, answer six questions one at a time,
and get short, honest feedback after each answer, then a session summary.

Built with Flask + SQLite + vanilla JS. The question generation and feedback
are powered by the Claude API — **but the app also works with zero setup and
no internet**, using a built-in offline question bank and a simple heuristic
feedback scorer. That means your hackathon demo can never break because of
a flaky connection or a missing key: add the API key for the "real AI" demo,
or skip it and the app quietly falls back.

## 1. Install dependencies

Open Command Prompt in this folder and run:

```
pip install -r requirements.txt
```

## 2. (Optional but recommended) Add your Claude API key

This turns on live AI-generated questions and feedback instead of the
offline fallback. Get a key from https://console.anthropic.com, then in
Command Prompt:

```
set ANTHROPIC_API_KEY=your-key-here
```

Skip this step entirely and the app still works — it'll just use the
built-in question bank and a simpler feedback scorer instead of Claude.

## 3. Run the app

```
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## How it's built

- `app.py` — Flask routes, SQLite storage, Claude API calls with fallback
- `question_bank.py` — offline questions + fallback feedback logic
- `templates/index.html` — single-page app (landing / session / summary)
- `static/css/style.css` — all styling
- `static/js/app.js` — page logic, talks to the Flask API

## Database

A SQLite file `interview.db` is created automatically on first run, storing
every session, question, answer, and score — useful if you want to add a
"past sessions" history view later.

## For your hackathon pitch

Worth calling out to judges:
- **Works with or without live AI** — a genuine reliability feature, not
  just a fallback for demo safety
- **Domain-aware**: questions adapt to Software Engineering / Core
  Engineering / Management tracks and experience level
- **Actionable feedback**, not just a score — a strength and one concrete
  thing to improve, every time
