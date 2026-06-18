# Apex Risk Limit Breach Runbook

## Alert Name

`apex_risk_limit_breach` (to be added to alert rules)

## Severity

Critical

## Triage Steps

1. Check risk events in the database and correlate them with policy version and approval tier.
2. Identify affected user, agent, strategy, instrument, venue, and order intent.
3. Check current market conditions, volatility, liquidity, and data freshness.
4. Check whether the breach was blocked before execution or detected post-trade.
5. Check audit logs for approval state, risk decision, manual override, and correlation ID.
6. Confirm whether the breach affects multiple users, strategies, or instruments.

## Remediation Steps

1. Review the affected risk profile, limit policy, and recent policy changes.
2. Halt the affected trading strategy or agent workflow until the breach is resolved.
3. Notify the risk team with affected users, instruments, notional value, and mitigation status.
4. Check audit logs for completeness, tamper evidence, and required governance fields.
5. Reconcile open orders, positions, and portfolio exposure against approved constraints.
6. Re-enable the workflow only after risk approval and documented remediation.

## Escalation Path

Escalate to the risk committee if the breach involves more than 100k notional, affects multiple users or instruments, or indicates control failure.

## Related Dashboards

- Risk Exposure Dashboard
- Decision Pipeline Dashboard
- Execution Quality Dashboard
- Security and Audit Dashboard
- Agent Health Dashboard
