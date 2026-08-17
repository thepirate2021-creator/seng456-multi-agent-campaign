"""
The orchestrator. This is NOT a fixed pipeline (A -> B -> C -> D).
It reads state["status"] after every agent call and decides which
agent should act next. This is the 'dynamic routing' requirement.
"""
from agents import run_copywriter, run_genz, run_professional, run_elderly, run_manager
from state import new_state


def route(state: dict) -> str:
    """Given current state, decide the next agent to run. Returns an agent name."""
    status = state["status"]

    if status == "drafting":
        return "copywriter"
    elif status == "revising":
        return "copywriter"       # send rejected work back to the writer
    elif status == "reviewing":
        # All three personas must have given feedback for this round before the
        # Manager runs. This is the dynamic part: router checks CURRENT
        # state (how many critiques exist this round) not a fixed order.
        this_round_feedback = [f for f in state["feedback"] if f["round"] == state["iteration"]]
        personas_done = {f["persona"] for f in this_round_feedback}

        if "Gen-Z Persona" not in personas_done:
            return "genz"
        elif "Professional Persona" not in personas_done:
            return "professional"
        elif "Elderly Customer Persona" not in personas_done:
            return "elderly"
        else:
            return "manager"
    elif status == "approved":
        return "DONE"
    else:
        raise ValueError(f"Unknown state status: {status}")


AGENT_FUNCS = {
    "copywriter": run_copywriter,
    "genz": run_genz,
    "professional": run_professional,
    "elderly": run_elderly,
    "manager": run_manager,
}


def run_campaign(brief: str, verbose: bool = True) -> dict:
    """Entry point: runs the full multi-agent orchestration for one brief."""
    state = new_state(brief)

    while True:
        next_agent = route(state)
        if next_agent == "DONE":
            break

        if verbose:
            print(f"[iter {state['iteration']}] -> routing to: {next_agent}")

        state = AGENT_FUNCS[next_agent](state)

        if verbose and next_agent == "manager":
            print(f"    Manager decision: {state['scores']['decision']} "
                  f"(winner: {state['winner']})")

    return state
