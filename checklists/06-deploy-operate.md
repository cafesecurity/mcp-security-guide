# Checklist: 6. Deploy and operate

*Generated from [06-deploy-operate.md](../guide/06-deploy-operate.md). Edit the page, not this file.*

- [ ] Only the MCP endpoint and protected resource metadata are reachable from outside; admin and debug endpoints are internal.
- [ ] Outbound traffic is restricted to named upstream systems.
- [ ] The server runs as non-root, in a container or sandbox.
- [ ] Local HTTP servers bind to 127.0.0.1, validate `Origin` and require a token; STDIO is preferred.
- [ ] Secrets come from a vault; credentials are short-lived and separate per environment; development credentials fail in production.
- [ ] Rate limits, result caps and lower limits for bulk-shaped calls are in place.
- [ ] Every tool call is logged with the fields above, with sensitive values masked, and sent to the SIEM.
- [ ] Alerts exist for volume spikes, probing, unknown clients and tool-list changes, and someone receives them.
- [ ] The kill switch can block a client, user or tool, revoke all tokens and take the server offline, and has been rehearsed.
- [ ] The internet-facing surface is scanned on a schedule.
- [ ] No production credentials are reachable from where a coding agent runs.
