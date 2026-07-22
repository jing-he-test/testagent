# Specification: collection-email-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md`
- [ ] Bootstrap agent code in `assets/collection-email-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/collection-email-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## SAP API Integration

> The API discovery timed out during spec generation. The agent uses S/4HANA OData APIs for AR data retrieval. Since no MCP servers were found for these APIs, the `mcp-translation-file` skill must be used to generate them.

- [ ] Download the API spec for **Payment Advice** (ORD ID: `sap.s4:apiResource:CE_PAYMENTADVICE_0001:v1`) using `sap_knowledge_graph_api_schema_download` and save to `specification/collection-email-agent/api-specs/payment-advice.edmx`
- [ ] Download the API spec for **Payment Advice (A2X)** (ORD ID: `sap.s4:apiResource:API_PAYMENT_ADVICE_SRV:v1`) using `sap_knowledge_graph_api_schema_download` and save to `specification/collection-email-agent/api-specs/payment-advice-a2x.edmx`
- [ ] Invoke the `mcp-translation-file` skill on the downloaded specs to generate `translation.json` files under `specification/collection-email-agent/api-specs/`
- [ ] Invoke `setup-solution` to register MCP server assets for the generated translation files
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from `mcp_tools.py` — NEVER use direct HTTP clients (`requests`, `httpx`, OData clients)

## Agent Implementation

- [ ] Create `assets/collection-email-agent/app/agent.py` with the following capabilities:
  - Tool: **get_customer_open_items** — retrieves all open AR items (invoice number, amount, due date, days overdue) for a given customer ID using MCP tools
  - Tool: **get_customer_payment_history** — retrieves past payment records for a given customer ID (payment dates, amounts, delays) using MCP tools
  - Tool: **draft_collection_email** — takes customer ID, open items, and payment history; calls LLM via SAP AI Core to generate a personalized collection email draft. Tone must adapt to payment behavior: first-time late payer (polite reminder) vs. chronic late payer (firm escalation)
  - Tool: **get_overdue_customers** — returns a list of customers with invoices past due date from S/4HANA using MCP tools

- [ ] System prompt must:
  - Instruct agent to never hallucinate invoice data or customer information
  - Set `top` to a maximum of 100 on every MCP tool call that accepts pagination
  - Guide the agent to produce professional, factual, brand-appropriate collection email drafts
  - Instruct the agent to include specific invoice numbers, amounts, and due dates in the draft
  - Instruct the agent that all emails are drafts for human review — never mark them as final or ready-to-send

- [ ] Delete the template runtime skill: `rm -rf assets/collection-email-agent/app/skills/template-skill/`

## Business Step Instrumentation (Milestones)

Implement structured logging and OpenTelemetry spans for all 5 milestones from the PRD. Extract all business logic from `stream()` into a plain async helper `_run_agent()` — never wrap `yield` inside `with tracer.start_as_current_span(...)`.

- [ ] **M1 — Overdue Detection**:
  - Log on achievement: `M1.achieved: overdue customer detection completed, N customers identified`
  - Log on miss: `M1.missed: no overdue customers found or S/4HANA query failed`
  - OTel span: `m1_overdue_detection`
- [ ] **M2 — Payment History Retrieved**:
  - Log on achievement: `M2.achieved: payment history and open items retrieved for customer {customerId}`
  - Log on miss: `M2.missed: failed to retrieve AR data for customer {customerId}`
  - OTel span: `m2_payment_history_retrieval`
- [ ] **M3 — Email Draft Generated**:
  - Log on achievement: `M3.achieved: collection email draft generated for customer {customerId}`
  - Log on miss: `M3.missed: email draft generation failed or returned empty for customer {customerId}`
  - OTel span: `m3_email_draft_generation`
- [ ] **M4 — Draft Surfaced for Review**:
  - Log on achievement: `M4.achieved: draft routed to AR specialist for customer {customerId}`
  - Log on miss: `M4.missed: draft routing failed for customer {customerId}`
  - OTel span: `m4_draft_review_routing`
- [ ] **M5 — Email Sent**:
  - Log on achievement: `M5.achieved: collection email sent to customer {customerId}`
  - Log on miss: `M5.missed: email was discarded or not sent for customer {customerId}`
  - OTel span: `m5_email_sent`

- [ ] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

## MCP Mock & Testing

- [ ] Invoke `mcp-mock-config` skill to generate `mcp-mock.json` after MCP server assets are registered
- [ ] `conftest.py` only sets `IBD_TESTING=true`
- [ ] Write unit tests in `assets/collection-email-agent/tests/`:
  - `test_get_customer_open_items.py` — mocks MCP, asserts correct AR items returned
  - `test_get_customer_payment_history.py` — mocks MCP, asserts payment records returned
  - `test_draft_collection_email.py` — mocks LLM and MCP, asserts draft contains invoice numbers and customer-appropriate tone
  - `test_get_overdue_customers.py` — mocks MCP, asserts overdue customer list returned
- [ ] Write one integration test `test_integration.py` — end-to-end agent flow with real LLM, mocked MCP
- [ ] Run `pytest` from `assets/collection-email-agent/` (no args)
- [ ] Verify coverage ≥ 70%; add tests if below threshold
- [ ] Verify `assets/collection-email-agent/app/agent.py` has exactly 3 decorated functions (`@agent_model`, `@agent_config`, `@prompt_section`)
- [ ] Run `pytest` again (no args) to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/collection-email-agent/`

## Validation

- [ ] `grep -r "M[0-9]\.achieved" assets/collection-email-agent/app/` — must return results
- [ ] `grep -r "sap_cloud_sdk.agent_decorators" assets/collection-email-agent/app/` — must return results
- [ ] `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/collection-email-agent/app/agent.py` — must return 3
- [ ] `ls assets/collection-email-agent/test_report.json` — must exist
