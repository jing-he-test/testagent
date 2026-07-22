# Product Requirements Document (PRD)

**Title:** Collection Email Drafting Agent  
**Date:** 2026-07-15  
**Owner:** Accounts Receivable Team  
**Solution Category:** n8n Workflow, AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**  
AR teams waste hours manually drafting collection emails that feel generic and fail to reflect each customer's payment history. This solution automates the process — an n8n workflow detects overdue customers in S/4HANA, and an AI agent generates personalized, context-aware collection emails ready for specialist review.

**Business Need:**  
No standard SAP product generates personalized collection emails. AR specialists manually compose messages without a consistent structure or visibility into the customer's full payment context, leading to lower response rates and longer collection cycles.

**Expected Value:**  
- Reduce time spent drafting collection emails per customer
- Increase response-to-collection rate through personalized, relevant messaging
- Ensure AR specialists focus on exception handling rather than manual writing

**Product Objectives:**
1. Automatically detect overdue customers and trigger email drafting
2. Generate personalized collection emails using payment history and open items from S/4HANA
3. Surface drafted emails for AR specialist review before sending

## Requirements

### Must-Have Requirements

**R1: Overdue Customer Detection**
- **User Story**: As an AR specialist, I need overdue customers to be automatically identified so that no outstanding invoice is overlooked.
- **Acceptance Criteria**: Given a scheduled run, when invoices are past due date in S/4HANA, then the workflow identifies the relevant customers and triggers the drafting process.
- **Priority Rank**: 1

**R2: Payment History & Open Item Retrieval**
- **User Story**: As an AI agent, I need to retrieve a customer's payment history and outstanding invoice list from S/4HANA so that I can generate a contextually relevant email.
- **Acceptance Criteria**: Given a customer ID, when the agent queries S/4HANA APIs, then it returns payment history and all open items with amounts, due dates, and aging.
- **Priority Rank**: 2

**R3: Personalized Email Drafting**
- **User Story**: As an AR specialist, I need the agent to draft a collection email personalized to each customer's history so that the message is relevant and more likely to prompt payment.
- **Acceptance Criteria**: Given payment history and open items, when the agent generates an email, then the email references specific invoice numbers, amounts, and tone adjusted to the customer's payment behavior (e.g., first-time vs. chronic late payer).
- **Priority Rank**: 3

**R4: Human Review Before Sending**
- **User Story**: As an AR specialist, I need to review and approve each drafted email before it is sent so that I retain control over all customer communications.
- **Acceptance Criteria**: Given a generated draft, when it is surfaced to the specialist, then they can edit, approve, or discard it before dispatch.
- **Priority Rank**: 4

## Solution Architecture

**Architecture Overview:**  
An n8n workflow runs on a scheduled trigger, queries SAP S/4HANA Accounts Receivable APIs for overdue customers, and for each customer invokes a Python-based AI agent. The agent retrieves full payment context and generates a personalized email draft using an LLM via SAP AI Core. Drafts are returned to the AR specialist for review.

**Key Components:**
- **n8n Workflow**: Scheduled trigger, overdue detection loop, agent invocation, and draft routing
- **AI Agent (Python, A2A)**: Retrieves customer AR context from S/4HANA and generates personalized email draft via LLM
- **SAP S/4HANA**: Source of payment history, open items, and customer master data via OData APIs
- **SAP AI Core (LLM)**: Powers the email drafting step within the agent

**Integration Points:**
- S/4HANA AR APIs (Payment Advice, Open Items): read-only, triggered per overdue customer
- SAP AI Core Generative AI Hub: LLM inference for email drafting

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent exposes extension points for: custom tone/brand guidelines, additional data sources (e.g., CRM notes, dispute history), and output format templates
- Future capabilities such as multi-language drafting or escalation path selection can be added without core rewrites

**Business Step Instrumentation:**
- All business logic steps emit structured logs following the pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- Enables production monitoring, debugging, and business reporting on collection activity

### Automation & Agent Behaviour

**Automation Level:** Hybrid (rule-based workflow + autonomous AI agent for content generation)

**Actions performed without human approval:**
- Detecting overdue invoices on schedule
- Retrieving customer payment history and open items
- Generating email draft

**Actions requiring human review:**
- Sending the collection email to the customer

**Model used:** LLM via SAP Generative AI Hub (SAP AI Core)

**Knowledge & data sources accessed:**
- SAP S/4HANA: payment history, open AR items, customer master
- Prompt context: invoice aging, days overdue, previous communication patterns

**Guardrails & fail-safes:**
- Emails are never sent automatically — human approval is mandatory
- If S/4HANA data retrieval fails, the workflow skips that customer and logs a warning
- If the LLM returns an empty or invalid draft, the specialist is notified to compose manually

## Milestones

### M1: Overdue Detection
- **Description**: The workflow identifies customers with invoices past due date
- **Achieved when**: At least one overdue customer record is retrieved from S/4HANA
- **Log on achievement**: `M1.achieved: overdue customer detection completed, N customers identified`
- **Log on miss**: `M1.missed: no overdue customers found or S/4HANA query failed`

### M2: Payment History Retrieved
- **Description**: The AI agent successfully fetches payment history and open items for a customer
- **Achieved when**: Agent returns structured payment context for the target customer
- **Log on achievement**: `M2.achieved: payment history and open items retrieved for customer {customerId}`
- **Log on miss**: `M2.missed: failed to retrieve AR data for customer {customerId}`

### M3: Email Draft Generated
- **Description**: The agent produces a personalized collection email draft
- **Achieved when**: LLM returns a non-empty, customer-specific email draft
- **Log on achievement**: `M3.achieved: collection email draft generated for customer {customerId}`
- **Log on miss**: `M3.missed: email draft generation failed or returned empty for customer {customerId}`

### M4: Draft Surfaced for Review
- **Description**: The draft is delivered to the AR specialist for review
- **Achieved when**: Draft is available in the specialist's review queue
- **Log on achievement**: `M4.achieved: draft routed to AR specialist for customer {customerId}`
- **Log on miss**: `M4.missed: draft routing failed for customer {customerId}`

### M5: Email Sent
- **Description**: AR specialist approves and sends the collection email
- **Achieved when**: Specialist confirms dispatch of the email
- **Log on achievement**: `M5.achieved: collection email sent to customer {customerId}`
- **Log on miss**: `M5.missed: email was discarded or not sent for customer {customerId}`
