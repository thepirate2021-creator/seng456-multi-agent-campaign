"""
Shared state object passed between all agents.
This is the 'state management' piece required by the course.
"""

def new_state(brief: str) -> dict:
    return {
        "brief": brief,
        "campaign_a": None,
        "campaign_b": None,
        "feedback": [],          # list of {round, persona, comments}
        "scores": {},            # {"A": float, "B": float}
        "iteration": 0,
        "max_iterations": 2,
        "status": "drafting",    # drafting -> reviewing -> revising -> approved
        "winner": None,
        "history": []            # full audit trail of every agent action
    }


def log_event(state: dict, agent: str, action: str, detail: str):
    """Append an event to the audit trail (used in Tests/Results section)."""
    state["history"].append({
        "iteration": state["iteration"],
        "agent": agent,
        "action": action,
        "detail": detail
    })
