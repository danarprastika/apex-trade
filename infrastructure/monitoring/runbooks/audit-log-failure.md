# Apex Audit Log Failure Runbook

## Alert Name

`apex_audit_log_failure` (to be added to alert rules)

## Severity

High

## Triage Steps

1. Check database disk space and storage volume health.
2. Check database connectivity, connection pool state, and query latency.
3. Check audit log write latency, failed writes, and recent error spikes.
4. Check audit table size, index health, and archival state.
5. Check whether state-changing agent actions are still occurring while audit writes are failing.
6. Check Security and Audit Dashboard for missing events, redaction failures, or compliance gaps.

## Remediation Steps

1. Restart the database if needed and safe, after confirming the failure is database-level.
2. Check audit table size and archive old audit logs according to retention policy.
3. Resolve disk, connection, or latency issues before resuming normal write volume.
4. Pause state-changing agent actions if audit logging cannot be restored promptly.
5. Backfill or reconcile missing audit events from trusted application logs when available.
6. Verify audit completeness, searchability, and redaction after recovery.

## Escalation Path

Escalate to the security team immediately for compliance risk, missing audit events, suspected tampering, or prolonged audit write failure.

## Related Dashboards

- Security and Audit Dashboard
- Database Health Dashboard
- Agent Health Dashboard
- Decision Pipeline Dashboard
