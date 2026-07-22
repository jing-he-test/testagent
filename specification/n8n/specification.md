# Specification: n8n

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-n8n-workflow.md](../guidelines-n8n-workflow.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md`

## Workflow: Collection Email Orchestration

Build a single n8n workflow file `assets/n8n/workflows/collection-email-orchestration.n8n.json` using the `n8n-workflow` skill. The workflow orchestrates overdue customer detection and delegates personalized email drafting to the AI agent.

### Workflow Steps

- [ ] **Schedule Trigger** — runs daily (e.g. 08:00 AM); configurable cron expression
- [ ] **Fetch Overdue Customers** — HTTP Request node calls the collection-email-agent at `{{AGENT_BASE_URL}}/invoke` with the query `"List all customers with overdue invoices"`. Returns a list of overdue customer IDs and invoice summaries.
- [ ] **Split in Batches** — splits overdue customer list, processing one customer at a time to avoid overloading the agent
- [ ] **Draft Collection Email (per customer)** — for each customer: HTTP Request node calls `{{AGENT_BASE_URL}}/invoke` with the query `"Draft a personalized collection email for customer {customerId}"`. Returns the email draft.
- [ ] **Route Draft for Review** — routes the draft to the AR specialist. Use an email node or webhook node to surface the draft for human review. The specialist receives: customer name, customer ID, total overdue amount, draft email text, and an action link to approve or discard.
- [ ] **Error Handler** — if the agent call fails for a customer, log a warning and continue processing the next customer (do not stop the entire batch)

### Configuration

- [ ] Agent base URL must be set via a workflow variable `AGENT_BASE_URL` (e.g. `https://agent.company.com`)
- [ ] Notification recipient email address configurable via workflow variable `AR_SPECIALIST_EMAIL`
- [ ] Schedule cron expression configurable via workflow variable or parameter

### Constraints

- [ ] No credential blocks in workflow JSON — authentication is assigned manually in n8n UI after import
- [ ] `connections` reference nodes by `name`, not `id`
- [ ] Workflow JSON must be well-formed and valid

## Write & Validate

- [ ] Write `assets/n8n/workflows/collection-email-orchestration.n8n.json` using the `n8n-workflow` skill
- [ ] Validate all workflow JSON files are well-formed
- [ ] Ensure `connections` reference nodes by `name`
