"""
Offline fallback content.
Used when ANTHROPIC_API_KEY is not set, or if a live API call fails —
so a hackathon demo never breaks because of network/API issues.
"""

DOMAINS = {
    "software": {
        "label": "Software Engineering",
        "questions": [
            "Walk me through a project you're proud of. What was your specific contribution?",
            "How would you explain the difference between a process and a thread to a non-technical interviewer?",
            "Describe a time you had a bug you couldn't solve for hours. What finally worked?",
            "How do you decide between using an array and a linked list for a given problem?",
            "Tell me about a time you disagreed with a teammate's technical decision. What did you do?",
            "Where do you see yourself using data structures and algorithms in real-world software, beyond interviews?",
        ],
    },
    "core": {
        "label": "Core Engineering",
        "questions": [
            "Describe a hands-on project or lab where you applied a core engineering concept practically.",
            "How do you approach a problem when the theory you learned doesn't quite match what you observe?",
            "Tell me about a time you worked in a team to meet a tight deadline on a technical task.",
            "What's a core engineering principle from your coursework that you find genuinely interesting, and why?",
            "How would you explain a concept from your field to someone with no technical background?",
            "Describe a situation where attention to detail mattered a lot in your work.",
        ],
    },
    "management": {
        "label": "Management",
        "questions": [
            "Tell me about a time you led a group project. What was the hardest part?",
            "How do you prioritize tasks when everything feels urgent?",
            "Describe a conflict within a team you were part of, and how it was resolved.",
            "What does good leadership look like to you, based on someone you've observed?",
            "Tell me about a decision you made that didn't work out. What did you learn?",
            "How do you stay organized when managing multiple commitments at once?",
        ],
    },
}


def get_fallback_questions(domain_key: str, count: int = 6):
    domain = DOMAINS.get(domain_key, DOMAINS["software"])
    qs = domain["questions"][:count]
    return qs


def get_fallback_feedback(answer_text: str):
    """A simple heuristic scorer used only if the API is unavailable."""
    length = len(answer_text.strip())
    word_count = len(answer_text.split())

    if word_count < 15:
        score = 4
        feedback = (
            "Your answer is quite brief. Interviewers usually want to hear a short "
            "story with context, action, and outcome — try expanding with a specific example."
        )
        strength = "Concise and to the point."
        improve = "Add a concrete example or specific detail to make it memorable."
    elif word_count < 40:
        score = 6
        feedback = (
            "Decent answer with some detail. Adding one specific example or number "
            "would make it more convincing to an interviewer."
        )
        strength = "Clear structure, easy to follow."
        improve = "Include a specific example, metric, or outcome."
    else:
        score = 8
        feedback = (
            "Solid, detailed answer. Make sure every part of it directly answers "
            "the question asked, and keep an eye on staying concise under time pressure."
        )
        strength = "Good depth and specific detail."
        improve = "Trim anything that doesn't directly serve the answer."

    return {"score": score, "feedback": feedback, "strength": strength, "improve": improve}
