# All checklists

*Generated from the guide pages by `scripts/build_checklists.py`. Edit the pages, not this file.*

## 0. Decide

From [00-decide.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/00-decide.md).

- [ ] There is a written reason why this is an MCP server rather than an API, a library or the vendor's own server.
- [ ] The brief states where it runs (local or remote), who calls it (staff or customers), what it reads, what it changes, and what it must never do.
- [ ] It has a named owner and an entry in the inventory.
- [ ] Every action (write, send, pay, delete) is listed and justified on its own; the default is read-only.
- [ ] The systems and data behind it are named, with whose credentials it will reach them.
- [ ] The brief is committed as the first section of `THREATMODEL.md`.

## 1. Threat model

From [01-threat-model.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/01-threat-model.md).

- [ ] `THREATMODEL.md` exists, names an owner and a review date, and states the spec version.
- [ ] Every tool is listed with reads or acts, and its [A] [B] [C] letters.
- [ ] Every field that outsiders can write is listed, with how it will be returned.
- [ ] Upstream systems, scopes, tenants and token lifetimes are written down.
- [ ] No single tool, and no single server, lights all three letters without a named approval step.
- [ ] Combinations to avoid are listed and shared with whoever approves agents.
- [ ] Out-of-scope threats are stated.
- [ ] A person, not an agent, has reviewed and approved the threat model.

## 2. Design

From [02-design.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/02-design.md).

- [ ] The identity model is per-user delegated access, or the threat model explains why not.
- [ ] No service account with organisation-wide rights sits behind the server.
- [ ] The server checks every token's audience, issuer, expiry and scopes.
- [ ] The server never forwards a client's token upstream; upstream calls use a separate token.
- [ ] `scopes_supported` is minimal; privileged tools need a step-up scope; no wildcard scopes.
- [ ] For internal servers: only approved clients can get a token. For public servers: per-client consent, showing the client's URL, with a page to disconnect.
- [ ] If the server fronts a third-party API with a static client ID: per-client consent, exact redirect matching and single-use `state` set after consent.
- [ ] Read and acting tools are separate; every acting tool needs a person's approval of the actual action, outside the chat.
- [ ] Acting tools have caps, volume alerts and idempotency keys.
- [ ] Tool descriptions are plain documentation and are frozen in a snapshot file.
- [ ] Results are plain text, tagged by source, capped, and never include secrets or auto-loading links.
- [ ] Tenant and user come from the token and appear in every query and cache key.
- [ ] Any state handles are random, expiring and bound to the user from the token.

## 3. Build

From [03-build.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/03-build.md).

- [ ] No shell anywhere: processes start with argument arrays, `shell: false` and `--` before user input.
- [ ] All SQL is parameterised, with the tenant from the token in every query.
- [ ] File paths are resolved (following symlinks) and confined to an allowed root.
- [ ] Outbound fetches are allow-listed, HTTPS only, with private and link-local ranges blocked on every hop.
- [ ] Every tool has a strict schema: bounded strings, enums where possible, no unknown properties.
- [ ] Token validation checks signature, pinned algorithms, issuer, audience, expiry and scopes on every request.
- [ ] Local HTTP servers bind to 127.0.0.1, validate `Origin` and `Host`, and require a token.
- [ ] Header and body values are checked for consistency (by the SDK or by you).
- [ ] Results are plain text, tagged by source, with no auto-loading links and no secrets.
- [ ] Secrets come from the environment or a vault; logs mask them; development credentials don't work in production.
- [ ] Every dependency was checked to exist and be the real one; versions are pinned; the lockfile is committed; CI runs an audit.
- [ ] Errors returned to clients are generic; details stay in your logs.
- [ ] A person reviewed every line of token handling, process launching, SQL, file and URL code.

## 4. Test

From [04-test.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/04-test.md).

- [ ] Every authorisation test in the list passes: no token, wrong audience, wrong issuer, expired, missing scope, token in the query string.
- [ ] Tenant and user isolation tests run on every build, including cached results.
- [ ] Injection tests cover shell metacharacters, path traversal, SQL and internal URLs.
- [ ] A hostile-content fixture checks source tagging, stripping of hidden text and removal of auto-loading links.
- [ ] Transport tests cover a foreign `Origin` and a header and body mismatch.
- [ ] A snapshot test fails the build on any change to tool names, descriptions, schemas or annotations.
- [ ] Rate limits and log contents are tested; logs contain no tokens or document bodies.
- [ ] CI runs a dependency audit, a secret scanner and a static analyser.
- [ ] A hostile-agent exercise has been run, and its findings are in the threat model.
- [ ] A person reviewed the test code, not just the results.

## 5. Release

From [05-release.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/05-release.md).

- [ ] The server's registry name is verified against a domain or GitHub organisation you control.
- [ ] Packages are published under the organisation's namespace, not a personal account.
- [ ] Your website and docs link to the exact registry name and server address.
- [ ] Publishing uses trusted publishing with provenance; there is no long-lived publishing token.
- [ ] The release job needs a named person's approval, never runs from pull requests, and pins actions to commit SHAs.
- [ ] Every maintainer account has two-factor authentication.
- [ ] The tool-definition snapshot's hash is published with each release.
- [ ] Any change to a tool's name, description, schema or annotations bumps the version and is explained in the release notes.
- [ ] The lockfile is shipped and key dependency versions are listed.
- [ ] No coding agent has access to publishing credentials or the release environment.

## 6. Deploy and operate

From [06-deploy-operate.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/06-deploy-operate.md).

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

## 7. Change

From [07-change.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/07-change.md).

- [ ] The change-classification table (or your version of it) is in the contribution guide.
- [ ] The snapshot test fails the build on any change to tool names, descriptions, schemas or annotations.
- [ ] Every client-visible change bumps the version and is described in words in the release notes.
- [ ] New tools, new scopes and new upstream access update the threat model and need a person's approval.
- [ ] The server sends `notifications/tools/list_changed` when its tools change.
- [ ] The tool-definition hash is published with each release.
- [ ] Dependency upgrades are read by a person before they reach production.
- [ ] The server is migrated to the 2026-07-28 spec, or has a dated plan to be.

## 8. Incident and retire

From [08-incident-retire.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/08-incident-retire.md).

- [ ] A runbook covers contain, assess, tell, and fix and return, with named owners.
- [ ] The runbook has been rehearsed at least once.
- [ ] Tokens issued for the server can be revoked in bulk, and the server's own credentials can be rotated quickly.
- [ ] Logs are good enough to say which users, tenants, clients and tools were involved.
- [ ] Contacts for legal, data protection and the registry or package host are in the runbook.
- [ ] Retirement steps cover deprecation, allow-lists, OAuth clients, tokens, upstream credentials, DNS, data and name reservation.
- [ ] Coding-agent sessions and tokens are in the revocation list.

## Using a coding agent safely

From [coding-agents.md](https://github.com/cafesecurity/mcp-security-guide/blob/main/guide/coding-agents.md).

- [ ] `AGENTS.md` (or a pointer to it) is in the repository.
- [ ] The agent runs in a sandbox with only the project folder and a restricted network.
- [ ] No production credentials, publishing tokens or cloud admin roles are reachable from the agent's environment.
- [ ] `.env` and credential files are outside the agent's reach or ignored by its tooling.
- [ ] The agent's own MCP servers are reviewed; cloned repositories can't add or start servers without approval.
- [ ] Every new dependency suggested by the agent is checked by a person.
- [ ] Human-owned decisions are made by a person, and the pull request says so.
- [ ] Diffs touching tokens, processes, SQL, files, URLs, network or tool definitions are read by a person.
- [ ] Test changes are reviewed; no security test was loosened, skipped or mocked away.
- [ ] The agent's tokens and sessions are in the incident revocation list.
