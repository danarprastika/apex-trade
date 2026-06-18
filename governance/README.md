# APEX AI Agent Governance

This directory contains machine-readable governance artifacts for APEX AI agents.

## Files

| File | Purpose |
|---|---|
| `agent-permissions.yaml` | Permission model, agent permissions, denied actions, and permission controls. |
| `agent-boundaries.yaml` | Functional, data, action, and communication boundaries. |
| `approval-workflow.yaml` | Approval tiers, decision flow, checks, escalation, and rejection behavior. |
| `audit-requirements.yaml` | Audit events, required fields, storage, retention, and review requirements. |
| `monitoring-requirements.yaml` | Dashboards, alerts, SLOs, SLIs, and agent-specific metrics. |
| `security-considerations.yaml` | Security controls, threat model, incident response, and trading safety requirements. |

## Scope

The governance artifacts apply to:

- Research Agent
- Market Agent
- Risk Agent
- Portfolio Agent
- Execution Agent

## Usage

These files are intended as source-of-truth policy documents for future APEX agent implementation. They define what must be enforced when the agent runtime, approval service, audit service, monitoring stack, and security controls are implemented.
