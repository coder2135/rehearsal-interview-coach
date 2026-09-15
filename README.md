Rehearsal — AI Interview Preparation Coach

Built for TCS–JMIT Tech Day (15 Sept 2026), Radaur.

A practice interview tool for students preparing for internships and placements. Pick a track, answer six questions one at a time, and get short, honest feedback after each answer — then a session summary showing where you're strong and what to work on.

Problem

Students preparing for internships and placements often lack confidence and sufficient interview practice, and struggle to get honest feedback on technical and HR-style answers before the real thing.

Features
Three tracks — Software Engineering, Core Engineering, or Management
One question at a time, with a live progress rail so you always know where you are in the session
AI-generated questions and feedback via the Claude API, tailored to the chosen track and experience level
Works offline too — if there's no API key or no internet, the app falls back to a built-in question bank and scorer, so it's never broken mid-demo
Session summary — every question, your answer, the feedback, and an average score, all on one screen
Tech stack
Backend: Flask, SQLite
Frontend: Vanilla JS, HTML, CSS (no framework)
AI: Claude API (claude-sonnet-5) for question generation and answer feedback
Getting started
bash
pip install -r requirements.txt

# Optional — enables live AI questions/feedback.
# Without this, the app runs fully offline using a built-in question bank.
set ANTHROPIC_API_KEY=your-key-here      # Windows
# export ANTHROPIC_API_KEY=your-key-here # macOS/Linux

python app.py

Then open http://127.0.0.1:5000.

Project structure
interview-coach/
├── app.py              # Flask routes, SQLite storage, Claude API calls
├── question_bank.py     # Offline questions + fallback feedback logic
├── requirements.txt
├── templates/
│   └── index.html       # Single-page app: landing / session / summary
└── static/
    ├── css/style.css
    └── js/app.js
How it works
Pick a track and experience level.
The app generates six interview questions for that track (via Claude, or the offline bank if no API key is set).
Answer each question in a few sentences — feedback comes back with a score out of 10, one strength, and one concrete thing to improve.
After the last question, see a full session summary with your average score.
