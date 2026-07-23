# Specification: greeting-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/greeting-agent/` using skill `sap-agent-bootstrap`
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## Agent Behaviour

- [x] Implement system prompt in `app/agent.py` (`@prompt_section`) that:
  - Instructs the agent to greet users warmly and by name if provided
  - Instructs the agent to maintain a friendly, conversational tone
  - Instructs the agent to recognize farewell intents and close conversations gracefully
  - Instructs the agent to respond only to greetings and basic conversational messages (no out-of-scope topics)
  - Instructs the agent NEVER to hallucinate or fabricate information
- [x] Implement the `stream()` method to handle:
  - **REQ-01** – Detect first user message and respond with a personalized greeting
  - **REQ-02** – Handle follow-up conversational messages with friendly, coherent responses
  - **REQ-03** – Detect farewell intent and respond with a polite closing message
- [x] Extract all business logic into a plain async helper `_run_agent()` and instrument it

## Business Step Instrumentation

- [x] Instrument milestone M1 (User Initiates Conversation)
- [x] Instrument milestone M2 (Agent Greets User)
- [x] Instrument milestone M3 (Conversation Continues)
- [x] Instrument milestone M4 (Session Ends)
- [x] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

## Cleanup

- [x] Delete the template runtime skill: `rm -rf assets/greeting-agent/app/skills/template-skill/`

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit tests in `assets/greeting-agent/tests/`:
  - `test_greeting.py` — tests that the agent responds with a greeting on first message
  - `test_conversation.py` — tests that the agent handles follow-up messages
  - `test_farewell.py` — tests that the agent closes the conversation gracefully
- [x] Write one integration test in `assets/greeting-agent/tests/test_integration.py`
- [x] Run `pytest` from `assets/greeting-agent/` — 36 passed, 96% coverage
- [x] Verify decorator count returns 3 ✓
- [x] `test_report.json` exists in `assets/greeting-agent/`
