# CLAUDE.md

This repository is the MCP Security Guide: Markdown pages plus one small example server.

- When working on an MCP server, follow the rules in [AGENTS.md](AGENTS.md).
- When editing the guide itself, follow [CONTRIBUTING.md](CONTRIBUTING.md): every factual claim needs a source in `reference/sources.md`, British English, no attribution of attacks to groups or countries.
- Checklists in `checklists/` are generated. Edit the `## Checklist` section of the guide page, then run `python3 scripts/build_checklists.py`.
- The example server is in `examples/ask-trevor/`. Run `npm ci && npm test` there before proposing changes to it. Its tool-definition snapshot changes only with a version bump and a changelog entry.
