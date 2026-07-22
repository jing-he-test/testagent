# Collection Email Drafting Agent

Personalized collection email drafting agent based on payment history and outstanding items.

## Business challenge

Accounts receivable teams spend significant time manually drafting collection emails for overdue customers. These emails often lack personalization and do not reflect the customer's specific payment history, outstanding invoice details, or relationship context — reducing their effectiveness and increasing collection cycle times.

## Key Milestones

1. **Overdue Detection** — Outstanding invoices past due date are identified for a customer
2. **Payment History Retrieval** — Customer's payment history and open items are fetched from S/4HANA
3. **Email Draft Generated** — AI agent produces a personalized collection email based on context
4. **Email Reviewed & Sent** — AR specialist reviews the draft and sends it to the customer
5. **Response / Payment Tracked** — Customer response or payment is recorded, closing the loop

## Business Architecture (RBA)

### End-to-End Process

Finance – Invoice to Cash (generic)

### Process Hierarchy

```
Finance (E2E)
└── Invoice to Cash (generic)
    └── Process accounts receivables and collect payment (BPS-366)
        └── Manage and process collections
        └── Process accounts receivable (AR)
        └── Manage receivables financing
```

### Summary

Drafting personalized collection emails maps to the "Invoice to Cash" E2E under Finance, specifically the "Process accounts receivables and collect payment" sub-process (BPS-366) covering collections management and AR processing.

## Fit Gap Analysis

| Requirement | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes |
|---|---|---|---|---|---|---|
| Retrieve outstanding invoices / open items | SAP S/4HANA Collections Management, Open Item Management | `sap.s4:apiResource:CE_PAYMENTADVICE_0001:v1` | — | — | No | OData API available; no MCP server found |
| Retrieve customer payment history | SAP S/4HANA Customer Payment Collaboration | — | — | — | Partial | Available via S/4HANA AR APIs |
| Personalized email drafting based on context | None | — | — | — | Yes | Requires AI agent with LLM reasoning |
| Trigger email drafting for overdue customers | SAP S/4HANA Collections Management | — | — | — | Partial | Needs workflow trigger on overdue threshold |

### Key findings

- SAP S/4HANA (Cloud Public/Private) covers collections management and open item management natively (BPS-366)
- No standard SAP product generates personalized, context-aware collection emails — this is a clear AI gap
- Payment Advice and Accounts Receivable OData APIs are available in S/4HANA for data retrieval
- No MCP servers found for the identified APIs; agent will call APIs directly or via CAP middleware
- An n8n workflow handles the scheduled trigger and orchestration; an AI agent handles personalized drafting
- The AR specialist retains control via a review step before any email is sent

## Recommendations

### Personalized Collection Email Drafting with AI Agent + n8n Workflow

#### Executive Summary

n8n workflow triggers overdue detection; AI agent drafts emails from S/4HANA data.

#### Recommended Solution

An n8n workflow runs on a schedule to detect overdue customers in SAP S/4HANA via the Accounts Receivable APIs. For each overdue customer, it invokes a Python-based AI agent that retrieves the customer's full payment history and outstanding invoice details, then uses an LLM to draft a personalized, context-aware collection email. The draft is surfaced to the AR specialist for review before sending. The solution is deployed on SAP BTP.

#### Recommended solution category

n8n Workflow, AI Agent

#### Intent fit
92%
