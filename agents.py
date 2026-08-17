"""
Agent definitions. Each agent is a distinct role (system prompt) that
reads and updates the shared state. Keeping these separate is what
makes this an orchestration system rather than one big prompt.
"""
import json
from llm_client import call_agent
from state import log_event


# ---------------------------------------------------------------------
# 1. COPYWRITER — drafts (or revises) two campaign variants
# ---------------------------------------------------------------------
COPYWRITER_SYSTEM = """You are a marketing copywriter. Given a campaign brief,
produce TWO distinct short-form ad campaign variants (A and B) for social media.
Each variant should have a different angle/tone (e.g. emotional vs funny vs professional).
Respond ONLY in JSON: {"campaign_a": "...", "campaign_b": "..."}
Keep each variant to 2-3 sentences."""

REVISION_SYSTEM = """You are a marketing copywriter revising ad campaigns based on
focus group feedback. Given the previous campaigns and the critiques received,
produce IMPROVED versions that address the specific complaints.
Respond ONLY in JSON: {"campaign_a": "...", "campaign_b": "..."}"""


def run_copywriter(state: dict) -> dict:
    if state["iteration"] == 0:
        prompt = f"Campaign brief: {state['brief']}"
        raw = call_agent(COPYWRITER_SYSTEM, prompt)
    else:
        feedback_text = "\n".join(
            f"- {f['persona']}: {f['comments']}" for f in state["feedback"]
        )
        prompt = (
            f"Original brief: {state['brief']}\n\n"
            f"Previous Campaign A: {state['campaign_a']}\n"
            f"Previous Campaign B: {state['campaign_b']}\n\n"
            f"Focus group feedback to address:\n{feedback_text}\n\n"
            f"Revise both campaigns to address this feedback."
        )
        raw = call_agent(REVISION_SYSTEM, prompt)

    data = _safe_json(raw, fallback={"campaign_a": raw, "campaign_b": raw})
    state["campaign_a"] = data.get("campaign_a", "")
    state["campaign_b"] = data.get("campaign_b", "")
    state["status"] = "reviewing"
    log_event(state, "Copywriter", "draft" if state["iteration"] == 0 else "revise",
              f"A: {state['campaign_a'][:80]}... | B: {state['campaign_b'][:80]}...")
    return state


# ---------------------------------------------------------------------
# 2 & 3. PERSONA CRITICS — Gen-Z and Professional
# ---------------------------------------------------------------------
GENZ_SYSTEM = """You are a Gen-Z social media user (age 19-24) reviewing two ad
campaigns. Judge them on: authenticity, engagement potential, and whether they'd
actually stop scrolling for it. Be blunt. Respond ONLY in JSON:
{"preferred": "A or B", "score_a": 1-10, "score_b": 1-10, "comments": "1-2 sentences"}"""

PROFESSIONAL_SYSTEM = """You are a marketing professional reviewing two ad campaigns
for brand safety, clarity, and credibility. Respond ONLY in JSON:
{"preferred": "A or B", "score_a": 1-10, "score_b": 1-10, "comments": "1-2 sentences"}"""


def run_persona(state: dict, persona_name: str, system_prompt: str) -> dict:
    prompt = (
        f"Campaign A: {state['campaign_a']}\n"
        f"Campaign B: {state['campaign_b']}\n\n"
        f"Give your honest reaction as this persona."
    )
    raw = call_agent(system_prompt, prompt)
    data = _safe_json(raw, fallback={"preferred": "A", "score_a": 5, "score_b": 5, "comments": raw})

    state["feedback"].append({
        "round": state["iteration"],
        "persona": persona_name,
        "comments": data.get("comments", ""),
        "preferred": data.get("preferred", "A"),
        "score_a": data.get("score_a", 5),
        "score_b": data.get("score_b", 5),
    })
    log_event(state, persona_name, "critique", data.get("comments", ""))
    return state


def run_genz(state: dict) -> dict:
    return run_persona(state, "Gen-Z Persona", GENZ_SYSTEM)


def run_professional(state: dict) -> dict:
    return run_persona(state, "Professional Persona", PROFESSIONAL_SYSTEM)


# ---------------------------------------------------------------------
# 4. CAMPAIGN MANAGER — decides APPROVE or REVISE (dynamic routing)
# ---------------------------------------------------------------------
MANAGER_SYSTEM = """You are the Campaign Manager. You receive scores and comments
from two focus-group personas about Campaign A and B. Decide:
1. Which variant is stronger overall (winner: "A" or "B")
2. Whether the winning variant is good enough to ship, or needs another revision
   round. Approve if average score >= 7. Otherwise request revision.
Respond ONLY in JSON:
{"winner": "A or B", "decision": "APPROVE or REVISE", "reasoning": "1-2 sentences"}"""


def run_manager(state: dict) -> dict:
    current_round_feedback = [f for f in state["feedback"] if f["round"] == state["iteration"]]
    feedback_summary = "\n".join(
        f"- {f['persona']} (prefers {f['preferred']}, scores A={f['score_a']}/B={f['score_b']}): {f['comments']}"
        for f in current_round_feedback
    )
    prompt = (
        f"Campaign A: {state['campaign_a']}\n"
        f"Campaign B: {state['campaign_b']}\n\n"
        f"Focus group feedback this round:\n{feedback_summary}\n\n"
        f"This is revision round {state['iteration']} of {state['max_iterations']} max."
    )
    raw = call_agent(MANAGER_SYSTEM, prompt)
    data = _safe_json(raw, fallback={"winner": "A", "decision": "APPROVE", "reasoning": raw})

    decision = data.get("decision", "APPROVE").upper()
    state["winner"] = data.get("winner", "A")
    state["scores"] = {
        "reasoning": data.get("reasoning", ""),
        "decision": decision
    }
    log_event(state, "Campaign Manager", "decision",
              f"{decision} — winner {state['winner']} — {data.get('reasoning','')}")

    if decision == "REVISE" and state["iteration"] < state["max_iterations"]:
        state["status"] = "revising"
        state["iteration"] += 1
    else:
        state["status"] = "approved"

    return state


# ---------------------------------------------------------------------
def _safe_json(raw: str, fallback: dict) -> dict:
    """Gemini sometimes wraps JSON in ```json fences — strip and parse safely."""
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return fallback
