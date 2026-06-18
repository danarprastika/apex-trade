# Apex Database Down Runbook

## Alert Name

`apex_postgres_down`

## Severity

Critical

## Triage Steps

1. Check PostgreSQL container status, restart count, and healthcheck state.
2. Check disk space on the PostgreSQL data volume and backup volume.
3. Check active and idle connection count.
4. Check slow query logs and long-running transactions.
5. Check PostgreSQL logs for startup failures, corruption warnings, authentication errors, and resource exhaustion.
6. Check whether backend, Celery, and scheduler are failing because of database dependency loss.

## Remediation Steps

1. Restart PostgreSQL if it is stopped, unhealthy, or stuck during startup.
2. Verify WAL archiving and replication status if archiving or replication is enabled.
3. Fail over to a replica if one exists and primary recovery is not immediate.
4. Restore from backup if data corruption is confirmed.
5. Re-check database health, connection count, and slow query activity after recovery.
6. Confirm dependent services have reconnected successfully.

## Escalation Path

Escalate to the DBA immediately if there is any data loss risk, confirmed corruption, failed backup availability, or unclear recovery path.

## Related Dashboards

- Database Health Dashboard
- Agent Health Dashboard
- Infrastructure Overview Dashboard
- Security and Audit Dashboard
