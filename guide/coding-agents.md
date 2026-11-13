# Using a coding agent safely

*As of 13 November 2026.* Previous: [8. Incident and retire](08-incident-retire.md) · Back to the [README](../README.md)

If a coding agent writes much of your MCP server, the agent is part of your attack surface. It reads untrusted text, runs commands, installs packages and holds credentials, which is everything this guide warns about in an MCP server. This page covers the agent itself and how to set it up.

## What goes wrong

### Packages that don't exist

Code-generating models sometimes recommend packages that don't exist. A study presented at USENIX Security 2025 (Spracklen and others) generated 576,000 code samples from 16 models and found that 19.7% of the packages they recommended didn't exist, and that many of the invented names came back every time the same prompt was repeated ([summary by CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa/)). Attackers register predictable invented names ("slopsquatting"). The models studied are now older, but the habit hasn't gone away, and an agent that installs packages itself removes the moment a person would have noticed.

### Untrusted text in the agent's context

A coding agent reads issues, pull requests, documentation, test fixtures, web pages and tool results. Any of these can carry instructions. The Supabase demonstration in the [case file](../reference/case-file.md) was a developer's coding agent reading a support ticket through an MCP server; the GitHub toxic-flow demonstration was an agent reading a public issue. When you build an MCP server with an agent, the agent may also be connected to your test data, which you may have deliberately filled with hostile content (see [Test](04-test.md#the-minimum-test-list)).

### Configuration that runs code

Agents and editors read configuration from the project folder, and some of it starts processes. In Claude Code, CVE-2025-59536 let a cloned repository's settings start MCP servers and run commands before the user's trust prompt, and CVE-2026-21852 let a repository setting redirect API traffic and send the user's API key out. Both were fixed before Check Point published ([write-up](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)). The lesson applies to every agent: a project's agent configuration is code.

### Secrets within reach

An agent can read whatever the user it runs as can read: `.env` files, cloud credentials in the home directory, SSH keys, tokens in shell history. Anything it reads can end up in its context, in a log, in a commit, or in a request to somewhere else.

### Over-broad defaults

Asked for a working server, agents reach for the shortest path: bind to `0.0.0.0`, allow every CORS origin, request every scope, use an admin key "for now", disable the check that's getting in the way.

### Tests written to pass

An agent told to make the build green may loosen an assertion, mock the token verifier or skip a test, and say the job is done.

## How to set it up

### 1. Give it the rules

Copy [`AGENTS.md`](../AGENTS.md) into the repository (or reference it from `CLAUDE.md` or your agent's equivalent). It lists the decisions the agent must hand back to a person, and the build rules from this guide.

### 2. Sandbox it

- Run the agent in a container, dev container or the agent's own sandbox mode, with only the project folder mounted.
- Restrict its network to the package registry, your source host and the documentation it needs. Block cloud metadata addresses.
- Keep command approval on for anything that installs packages, changes the network, or touches files outside the project.

### 3. Keep credentials out

- No production credentials on the machine or in the container the agent uses. Give it a separate development environment with its own test identity provider and test data. The [Ask Trevor example](../examples/ask-trevor/) runs entirely on a local test issuer for this reason.
- No publishing tokens, no cloud admin roles, no access to the release environment.
- Keep `.env` files and credential files out of the mounted folder, or tell the agent's tooling to ignore them.

### 4. Control its own MCP servers

- Review which MCP servers your coding agent itself has loaded. Each one adds Feed, Behaviour and Impact to the agent that is writing your code.
- Don't let a cloned repository's configuration add or start servers. Use your agent's trust prompt, and in organisations use managed settings (for example Claude Code's managed MCP configuration, or GitHub Copilot's enterprise MCP allow-lists; see [For security leads](../reference/for-security-leads.md#controlling-the-agents-staff-connect)).
- Treat MCP configuration files in pull requests like code: review them.

### 5. Keep people on the decisions that matter

The human-owned decisions are listed at the top of [`AGENTS.md`](../AGENTS.md): identity model, token validation, scopes, tool definitions, new acting tools, upstream access, network exposure, publishing. The agent can draft; a person decides.

### 6. Review with a second pair of eyes

- Read every diff that touches tokens, processes, SQL, files, URLs, network configuration or tool definitions.
- Check every new dependency yourself.
- For larger changes, have a separate agent session review the diff cold, with [`prompts/security-review.md`](../prompts/security-review.md) and only the threat model for context.
- Read the test diff as carefully as the code diff.

### 7. Include the agent in incidents

If something goes wrong, revoke the tokens and sessions the agent used, and check its configuration and history (see [Incident and retire](08-incident-retire.md#if-a-coding-agent-is-doing-this)).

## The prompts

| Prompt | Produces | Who approves |
| --- | --- | --- |
| [`threat-model.md`](../prompts/threat-model.md) | `THREATMODEL.draft.md` from the brief and the code | A person edits and adopts it |
| [`security-review.md`](../prompts/security-review.md) | Findings with file, line and failure scenario | A person decides what to fix |
| [`pre-release.md`](../prompts/pre-release.md) | `RELEASE-CHECK.md` and draft release notes | A person tags the release |

## Checklist

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
