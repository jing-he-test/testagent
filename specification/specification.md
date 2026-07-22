# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [ ] Create asset directories: `mkdir -p assets/collection-email-agent/ assets/n8n/`
- [ ] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for every asset
- [ ] Validate all `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [ ] Execute specification/collection-email-agent/specification.md (all items)
- [ ] Execute specification/n8n/specification.md (all items)
- [ ] Cross-implementation compatibility check: verify the n8n workflow `AGENT_BASE_URL` placeholder aligns with the agent's A2A endpoint (`/.well-known/agent.json` and `/invoke`); verify the agent's `invoke` endpoint accepts the queries used in the n8n workflow; fix any mismatches before proceeding
