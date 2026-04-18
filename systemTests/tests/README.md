# System Tests Organization

This folder is organized by functional domain so the full system test suite can scale to 281+ cases.

## Folder layout

- auth: login, password flows, logout, access checks
- gateway: gateway lifecycle and command flows (commissioning, decommissioning, reboot, reset)
- infra: infrastructure smoke checks (NATS, DB, service reachability)
- tenant: tenant lifecycle and impersonation
- user: tenant admin and tenant user management
- sensor: sensor lifecycle and data visualization checks
- api_key: API key lifecycle and validation rules
- alert: alert list/detail checks and inactivity notifications
- audit: audit log list/filter/export checks
- dashboard: dashboard counters, lists and business summaries
- monitoring: Grafana/Prometheus/NATS monitoring validations
- commissioning: commissioning/decommissioning request workflows
- _shared: shared helpers specific to tests package (if needed)
- _templates: template files for new test modules

## Naming conventions

- Keep test file names as `test_<feature>_e2e.py`.
- Prefer one business flow per file.
- Keep shared reusable utilities in `test_support`.

## Suggested growth strategy

1. Start from smoke and critical business paths.
2. Add one test file per TS.json cluster.
3. Keep DB/NATS verification in the same test where behavior is asserted.
4. Add cleanup logic in `finally` blocks for stateful tests.

## Important guardrail

- Implement tests only for features currently exposed by backend router and frontend routes.
- For features present in `test_support/TS.json` but not yet exposed end-to-end, keep them documented as pending and do not add failing tests.

## Current implementation status (Apr 2026)

Implemented or available now:

- auth
- gateway
- infra
- tenant
- user
- sensor
- dashboard

Not implemented end-to-end yet (keep as pending only):

- alert
- api_key
- audit
- commissioning
- monitoring
