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

Copy [`AGENTS.md`](../AGENTS.md) into the repository (or reference it from `CLAUDE.md` or your agent's equivalent). It lists the decisions the agent must hand back to a person, and the build rules from this guide. Install the [skills](../skills/README.md) as well, so the agent can draft the threat model, review changes and check releases the same way every time.

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
- Before adding a third-party server to the agent, audit it with the [`mcp-server-audit`](../skills/mcp-server-audit/SKILL.md) skill.

### 5. Keep people on the decisions that matter

The human-owned decisions are listed at the top of [`AGENTS.md`](../AGENTS.md): identity model, token validation, scopes, tool definitions, new acting tools, upstream access, network exposure, publishing. The agent can draft; a person decides.

A rule the agent is asked to follow is weaker than one something enforces. `mcp-guide` sets up three layers, weakest first:

| Layer | Set up by | What it does | What it doesn't |
| --- | --- | --- | --- |
| Instructions | `mcp-guide init` | `AGENTS.md` and the skills tell the agent when to stop and ask | Nothing stops an agent that forgets, or is talked out of it by text it read |
| Agent permissions (Claude Code) | `mcp-guide init` | Rules in `.claude/settings.json`: the agent must get your OK (even in modes that otherwise approve edits and commands) before it saves `THREATMODEL.md`, edits the rules or the tool snapshot, publishes or tags, or runs an audit; and it can't read `.env` | These cover the agent's own file and shell tools. A determined or confused agent can reach a file another way (a script, say), and anyone who can edit the repository can remove the rules |
| Repository review | `mcp-guide protect --owner @you`, plus branch protection that you turn on | Changes to the threat model, the rules, the tool snapshot and the agent's own instructions need a named person's review before they merge | Only as strong as the branch protection and the reviewer's attention |

Two checks make changes to these visible: `mcp-guide snapshot check` fails a build when anything a tool tells the model has changed, and `mcp-guide status --strict` fails it when the installed rules, skills or guardrails have been edited or removed. For other agents, set the equivalent in their own permission settings; `init` says when it has installed instructions only.

### 6. Review with a second pair of eyes

- Read every diff that touches tokens, processes, SQL, files, URLs, network configuration or tool definitions.
- Check every new dependency yourself.
- For larger changes, have a separate agent session review the diff cold, with the [`mcp-security-review`](../skills/mcp-security-review/SKILL.md) skill and only the threat model for context.
- Read the test diff as carefully as the code diff.

### 7. Include the agent in incidents

If something goes wrong, revoke the tokens and sessions the agent used, and check its configuration and history (see [Incident and retire](08-incident-retire.md#if-a-coding-agent-is-doing-this)).

## The skills

The [`skills/`](../skills/) folder holds four [Agent Skills](https://agentskills.io/): folders with a `SKILL.md` that most coding agents load when the task matches. Install them with `bin/mcp-guide init` (see the [quick start](../QUICKSTART.md)) or by hand ([skills/README.md](../skills/README.md)).

| Skill | Use it | Produces | Who decides |
| --- | --- | --- | --- |
| [`mcp-threat-model`](../skills/mcp-threat-model/SKILL.md) | Before building; when tools, scopes or upstream systems change | `THREATMODEL.md`, after asking you questions | A person answers, corrects and approves it |
| [`mcp-security-review`](../skills/mcp-security-review/SKILL.md) | On each change, ideally in a fresh session | Findings with file, line and failure scenario | A person decides what to fix |
| [`mcp-release-check`](../skills/mcp-release-check/SKILL.md) | Before tagging a release | `RELEASE-CHECK.md` and draft release notes | A person tags the release |
| [`mcp-server-audit`](../skills/mcp-server-audit/SKILL.md) | Before installing or approving someone else's server | An audit report with a recommendation | A person signs it off |

## Checklist

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
