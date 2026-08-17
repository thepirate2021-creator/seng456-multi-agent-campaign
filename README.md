# Multi-Agent Campaign Generator and Focus Group

This SENG 456 project uses multiple LLM agents to create, evaluate, revise, and approve advertising campaigns. The system demonstrates shared state management, dynamic agent routing, and an iterative feedback loop.

## Agents

- **Copywriter:** Creates two campaign variants and revises them when requested.
- **Gen-Z Persona:** Evaluates both campaigns from a younger audience's perspective.
- **Professional Persona:** Evaluates clarity, credibility, usefulness, and brand safety.
- **Campaign Manager:** Compares the persona feedback, selects a winner, and returns either `APPROVE` or `REVISE`.

## Workflow

1. The user supplies a campaign brief.
2. The Copywriter produces Campaign A and Campaign B.
3. Both personas independently evaluate the campaigns.
4. The Campaign Manager selects the stronger campaign.
5. If the decision is `REVISE`, feedback is routed back to the Copywriter.
6. The revised campaigns are evaluated again until approval or the iteration limit is reached.
7. A full audit trail is written to `last_run_transcript.json`.

## Project Files

- `main.py` — command-line entry point
- `orchestrator.py` — routing and feedback-loop control
- `agents.py` — agent prompts and responsibilities
- `state.py` — shared campaign state and audit trail
- `llm_client.py` — Gemini API client and retry handling
- `requirements.txt` — Python dependencies

## Installation

1. Create and activate a virtual environment on Windows:

   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install the dependencies:

   ```cmd
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project folder:

   ```text
   GEMINI_API_KEY=your_api_key_here
   ```

   The `.env` file is excluded from Git and must never be committed.

## Execution

Run the default campaign brief:

```cmd
python main.py
```

Run a custom brief:

```cmd
python main.py "Luxury skincare line for professionals aged 35-55, launching a premium email and Instagram campaign."
```

## Tests

- **Test 1 — Direct approval:** A suitable campaign is generated and approved during the first evaluation.
- **Test 2 — Revision loop:** The Manager returns `REVISE`, the Copywriter updates both campaigns using the feedback, and the Manager later returns `APPROVE`.
- **Test 3 — Different audience:** A different product and audience are used to demonstrate adaptive campaign generation and persona preferences.

## Technical Challenge

Gemini free-tier requests can return `429 RESOURCE_EXHAUSTED` or `503 UNAVAILABLE`. The API wrapper handles temporary failures with bounded backoff and gives a clear error when the daily quota is exhausted. This prevents uncontrolled retries and makes failures easier to diagnose.

## Security

API keys, virtual environments, Python cache files, and generated transcripts are excluded through `.gitignore`.
