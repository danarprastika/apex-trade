# Apex Backend Down Runbook

## Alert Name

`apex_backend_down`

## Severity

Critical

## Triage Steps

1. Check backend pod/container status and restart count.
2. Check backend logs for startup failures, unhandled exceptions, dependency timeouts, and recent deployment markers.
3. Check backend health endpoint availability and response body.
4. Check dependency health for PostgreSQL and Redis.
5. Review recent backend, scheduler, Celery, and infrastructure deployments or configuration changes.
6. Confirm whether the alert is isolated to backend or correlated with database, Redis, queue, or network issues.

## Remediation Steps

1. Restart the backend container if it is unhealthy or stuck.
2. Verify database connection settings, credentials, network reachability, and migration state.
3. Verify Redis connection settings, broker reachability, and authentication state.
4. Roll back the backend deployment if the issue started after a recent release.
5. Re-check the health endpoint and backend logs after remediation.
6. Confirm request traffic, error rate, and latency have returned to normal ranges.

## Escalation Path

Escalate to the on-call engineer if the backend does not recover within 5 minutes or if dependency failures block recovery.

## Related Dashboards

- Agent Health Dashboard
- API Service Dashboard
- Infrastructure Overview Dashboard
- Database Health Dashboard
- Redis Health Dashboard
