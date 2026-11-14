# Changelog

## Unreleased

- Skills: `mcp-threat-model`, `mcp-security-review`, `mcp-release-check` (replacing `prompts/`), and `mcp-server-audit` for vetting third-party servers, with a Docker sandbox, fake-credential canaries, a logging network sink and tested fixtures.
- README links the "MCP Security: Zero to Hero" playlist.
- QUICKSTART.md: exact commands and paste-in prompts for adding the rules and skills, building, reviewing, releasing, and auditing someone else's server.
- `bin/mcp-guide`, a standard-library setup script: `init`, `status`, `update` and `remove` add and maintain the rules and skills in a repository (keeping local edits, never updating itself), `doctor` checks prerequisites, and `audit` runs the audit scripts in order, asking before the sandbox, and writes `SUMMARY.md`.
- `mcp-threat-model` 1.1.0: the agent interviews the person, drafts, asks about the gaps, and saves `THREATMODEL.md` on explicit approval. Prompts in the quick start are now one line.
- The audit sandbox saves the full Docker build log when a build fails.

- First public version: nine lifecycle pages, coding-agent guidance, reference pages, checklists and the Ask Trevor example server. Follows the MCP specification of 2026-07-28.
