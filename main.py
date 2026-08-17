"""
Entry point. Run: python main.py
Edit BRIEF below or pass one as a command-line arg.
"""
import sys
import json
from orchestrator import run_campaign


def print_summary(state: dict):
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Status: {state['status']}")
    print(f"Winner: Campaign {state['winner']}")
    print(f"Iterations used: {state['iteration']}")
    print(f"\nFinal Campaign A: {state['campaign_a']}")
    print(f"\nFinal Campaign B: {state['campaign_b']}")
    print(f"\nManager reasoning: {state['scores'].get('reasoning', '')}")
    print("\n--- Full audit trail ---")
    for event in state["history"]:
        print(f"  iter {event['iteration']} | {event['agent']:20s} | {event['action']:10s} | {event['detail'][:70]}")


if __name__ == "__main__":
    brief = sys.argv[1] if len(sys.argv) > 1 else (
        "New budget fitness app targeting people aged 18-45, "
        "launching a TikTok/Instagram campaign."
    )
    print(f"Brief: {brief}\n")
    final_state = run_campaign(brief)
    print_summary(final_state)

    # Save full transcript for the Tests/Results section of the submission form
    with open("last_run_transcript.json", "w") as f:
        json.dump(final_state, f, indent=2)
    print("\nFull transcript saved to last_run_transcript.json")
