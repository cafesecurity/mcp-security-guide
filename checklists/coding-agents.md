# Checklist: Using a coding agent safely

*Generated from [coding-agents.md](../guide/coding-agents.md). Edit the page, not this file.*

- [ ] `AGENTS.md` (or a pointer to it) is in the repository.
- [ ] The agent runs in a sandbox with only the project folder and a restricted network.
- [ ] No production credentials, publishing tokens or cloud admin roles are reachable from the agent's environment.
- [ ] `.env` and credential files are outside the agent's reach or ignored by its tooling.
- [ ] The agent's own MCP servers are reviewed; cloned repositories can't add or start servers without approval.
- [ ] Every new dependency suggested by the agent is checked by a person.
- [ ] Human-owned decisions are made by a person, and the pull request says so.
- [ ] Something enforces that, beyond instructions: the agent's permission rules, and code owners with branch protection for the threat model, the rules and the tool snapshot.
- [ ] Diffs touching tokens, processes, SQL, files, URLs, network or tool definitions are read by a person.
- [ ] Test changes are reviewed; no security test was loosened, skipped or mocked away.
- [ ] The agent's tokens and sessions are in the incident revocation list.
