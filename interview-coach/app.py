import os
import json
import sqlite3
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, g

from question_bank import DOMAINS, get_fallback_questions, get_fallback_feedback

DB_PATH = os.path.join(os.path.dirname(__file__), "interview.db")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-5"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            level TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            idx INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );

        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            score INTEGER,
            feedback TEXT,
            strength TEXT,
            improve TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Claude API helpers (graceful fallback if no key / call fails)
# ---------------------------------------------------------------------------

def _extract_json(text):
    """Pull a JSON object/array out of a model response, tolerating code fences."""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise


def call_claude(prompt: str):
    """Returns raw text response from Claude, or None if unavailable."""
    if not API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=API_KEY)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in response.content if block.type == "text"]
        return "\n".join(parts)
    except Exception as exc:  # noqa: BLE001 - any API/network failure -> fallback
        print(f"[warn] Claude API call failed, using fallback. Reason: {exc}")
        return None


def generate_questions(domain_key: str, level: str, count: int = 6):
    domain_label = DOMAINS.get(domain_key, DOMAINS["software"])["label"]
    prompt = f"""You are an experienced technical interviewer preparing a student for a {level}
level interview in the domain: {domain_label}.

Generate exactly {count} realistic interview questions this student is likely to be asked.
Mix behavioral and domain-relevant questions. Keep each question a single sentence.

Respond with ONLY a JSON array of {count} strings, no preamble, no markdown fences.
Example format: ["Question 1?", "Question 2?"]"""

    raw = call_claude(prompt)
    if raw:
        try:
            questions = _extract_json(raw)
            if isinstance(questions, list) and len(questions) >= 1:
                return [str(q) for q in questions[:count]]
        except (json.JSONDecodeError, ValueError):
            pass

    return get_fallback_questions(domain_key, count)


def generate_feedback(question_text: str, answer_text: str):
    prompt = f"""You are a warm but honest interview coach reviewing a student's practice answer.

Question: {question_text}
Student's answer: {answer_text}

Evaluate the answer. Respond with ONLY a JSON object in this exact shape, no markdown fences:
{{
  "score": <integer 1-10>,
  "feedback": "<2-3 sentences of direct, constructive feedback>",
  "strength": "<one short sentence naming what worked>",
  "improve": "<one short sentence naming the single most useful improvement>"
}}"""

    raw = call_claude(prompt)
    if raw:
        try:
            data = _extract_json(raw)
            if isinstance(data, dict) and "score" in data:
                data["score"] = int(data["score"])
                return data
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return get_fallback_feedback(answer_text)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", domains=DOMAINS)


@app.route("/api/session/start", methods=["POST"])
def start_session():
    data = request.get_json(force=True)
    domain_key = data.get("domain", "software")
    level = data.get("level", "Entry-level")

    if domain_key not in DOMAINS:
        return jsonify({"error": "Unknown domain"}), 400

    questions = generate_questions(domain_key, level)

    db = get_db()
    cur = db.execute(
        "INSERT INTO sessions (domain, level, created_at) VALUES (?, ?, ?)",
        (domain_key, level, datetime.now(timezone.utc).isoformat()),
    )
    session_id = cur.lastrowid

    q_rows = []
    for i, q_text in enumerate(questions):
        qcur = db.execute(
            "INSERT INTO questions (session_id, idx, question_text) VALUES (?, ?, ?)",
            (session_id, i, q_text),
        )
        q_rows.append({"id": qcur.lastrowid, "idx": i, "text": q_text})
    db.commit()

    return jsonify(
        {
            "session_id": session_id,
            "domain_label": DOMAINS[domain_key]["label"],
            "level": level,
            "questions": q_rows,
            "total": len(q_rows),
            "live_ai": bool(API_KEY),
        }
    )


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    data = request.get_json(force=True)
    question_id = data.get("question_id")
    answer_text = (data.get("answer_text") or "").strip()

    if not question_id or not answer_text:
        return jsonify({"error": "question_id and answer_text are required"}), 400

    db = get_db()
    q_row = db.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    if q_row is None:
        return jsonify({"error": "Question not found"}), 404

    result = generate_feedback(q_row["question_text"], answer_text)

    db.execute(
        """INSERT INTO answers (question_id, answer_text, score, feedback, strength, improve, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            question_id,
            answer_text,
            result.get("score"),
            result.get("feedback"),
            result.get("strength"),
            result.get("improve"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()

    return jsonify(result)


@app.route("/api/session/<int:session_id>/summary")
def session_summary(session_id):
    db = get_db()
    session_row = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if session_row is None:
        return jsonify({"error": "Session not found"}), 404

    rows = db.execute(
        """SELECT q.idx, q.question_text, a.answer_text, a.score, a.feedback, a.strength, a.improve
           FROM questions q
           LEFT JOIN answers a ON a.question_id = q.id
           WHERE q.session_id = ?
           ORDER BY q.idx ASC""",
        (session_id,),
    ).fetchall()

    items = [dict(r) for r in rows]
    scored = [i["score"] for i in items if i["score"] is not None]
    avg_score = round(sum(scored) / len(scored), 1) if scored else None

    return jsonify(
        {
            "domain_label": DOMAINS.get(session_row["domain"], {}).get("label", session_row["domain"]),
            "level": session_row["level"],
            "average_score": avg_score,
            "answered": len(scored),
            "total": len(items),
            "items": items,
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
