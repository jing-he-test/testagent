# Simple Greeting Agent

Simple Greeting Agent

## Business challenge

Build a simple AI-powered greeting agent that welcomes users and engages in basic conversational interactions.

## Key Milestones

1. **User Initiates Conversation** – User sends an initial message to the agent
2. **Agent Greets User** – Agent responds with a personalized greeting
3. **Conversation Continues** – Agent handles follow-up messages in a friendly, conversational manner
4. **Session Ends** – Agent wraps up the conversation gracefully

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash (Manage Customers and Channels)

### Process Hierarchy

```
Lead to Cash
└── Manage Customers and Channels (generic)
    └── Manage customers (generic)
        └── Manage customer experience
    └── Manage and operate sales channels (generic)
        └── Operate omnichannel customer platforms
```

### Summary

A greeting agent maps to the "Manage Customers" sub-process under Lead to Cash, enabling a basic customer experience touchpoint via conversational AI.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ---- | ------------------- |
| Conversational greeting capability | No standard SAP product covers this directly | — | — | — | Yes | Custom AI agent required |
| User interaction handling | SAP Customer Data Platform (Customer Journey Orchestration) | — | — | — | Partial | Custom agent is the right approach for simplicity |

### Key findings
- No standard SAP product provides a simple out-of-the-box greeting agent
- A lightweight custom AI agent is the most appropriate approach
- SAP AI Core (via SAP BTP) provides the LLM runtime for the agent
- The agent follows the A2A (Agent-to-Agent) protocol for interoperability
- Minimal scope: greet, converse, respond — no backend data integration required

## Recommendations

### Simple Greeting AI Agent

#### Executive Summary

A lightweight Python-based AI agent that greets and chats with users.

#### Recommended Solution

A pro-code Python AI agent deployed on SAP BTP, using SAP AI Core as the LLM backend. The agent handles user greetings, responds in a friendly tone, and supports basic back-and-forth conversation. No external SAP system integration is required.

#### Recommended solution category

AI Agent

#### Intent fit
95%
