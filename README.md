# MCP Security Guide for Developers

How to build a Model Context Protocol (MCP) server that won't become someone's case study, from the decision to build one to the day you switch it off. Written for developers who do much of the work with a coding agent.

*As of 14 November 2026. Follows the MCP specification of [2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28). Read the [disclaimer](#disclaimer).*

**In a hurry? Start with the [developer quick start](QUICKSTART.md):** one command (`mcp-guide init`) adds the rules, skills and agent guardrails to your repository, then one-line prompts for your coding agent; `mcp-guide audit` vets someone else's server, and runs nothing risky unless you accept that risk by name.

## Why a server needs more than ordinary app security

An MCP server is two things at once:

- **Software**, which can have ordinary bugs: command injection, missing authentication, leaked tokens.
- **Text the model reads.** Tool names, descriptions and results all land in the model's context, and the model may obey them.

Most real incidents so far needed both views to explain. This guide uses one model throughout, **Feed, Behaviour, Impact**: what the server makes the model read, what it lets the model do, and what it can reach. See [the model](reference/model.md).

## The lifecycle

Each page says what to decide or do, what has gone wrong in real cases, the controls, what to watch for if a coding agent is doing the work, and a checklist.

| # | Phase | The question it answers |
| --- | --- | --- |
| 0 | [Decide](guide/00-decide.md) | Should this be a server at all, and what kind? |
| 1 | [Threat model](guide/01-threat-model.md) | What does it feed the model, let it do, and reach? |
| 2 | [Design](guide/02-design.md) | Whose identity, which scopes, which tools? |
| 3 | [Build](guide/03-build.md) | How do I write it without the classic bugs? |
| 4 | [Test](guide/04-test.md) | How do I know the controls work? |
| 5 | [Release](guide/05-release.md) | How do I publish it so nobody can impersonate it? |
| 6 | [Deploy and operate](guide/06-deploy-operate.md) | Where does it run, and how will I notice trouble? |
| 7 | [Change](guide/07-change.md) | What changes need clients to approve again? |
| 8 | [Incident and retire](guide/08-incident-retire.md) | What do I do on a bad day, and at the end? |

Plus [using a coding agent safely](guide/coding-agents.md): the agent itself is part of your attack surface.

## Using this guide with a coding agent

The [quick start](QUICKSTART.md) has the commands and prompts. In short:

1. Run `mcp-guide init` (the [setup script](bin/mcp-guide)) in your repository. It adds [`AGENTS.md`](AGENTS.md) (the guide's rules as short instructions an agent can follow) and the [skills](skills/): threat modelling, security review of a change, a pre-release check, and an audit for third-party servers (with an optional Docker sandbox).
2. Ask the agent for a threat model before any code. It interviews you, drafts it from your answers and the code, and saves it when you approve. You don't fill in a template.
3. Keep the decisions marked **human-owned** for a person: the identity model, scopes, token validation, anything that changes what a tool says or does, and publishing. `init` adds permission rules so Claude Code has to ask you at those points, `mcp-guide protect` adds code owners for the security files, and `mcp-guide snapshot check` fails the build when a tool's definition changes ([how the layers fit](guide/coding-agents.md#5-keep-people-on-the-decisions-that-matter)).

## Vetting someone else's server

Most people install MCP servers rather than build them. Before you install or approve one, run `mcp-guide audit` (or the [`mcp-server-audit`](skills/mcp-server-audit/SKILL.md) skill) on the exact version: it checks the publisher, scans the code and tool descriptions, checks a remote server's sign-in, and can run the server in a locked-down Docker sandbox with fake credentials to see what it really does.

## Reference

- [The model](reference/model.md): Feed, Behaviour, Impact; the Rule of Two; the scorecard.
- [Spec checklist](reference/spec-checklist.md): what the 2026-07-28 specification requires.
- [Frameworks](reference/frameworks.md): OWASP, MITRE ATLAS, CSA MAESTRO, NIST, mapped to the lifecycle.
- [Case file](reference/case-file.md): real incidents and demonstrations, and what's commonly misreported.
- [For security leads](reference/for-security-leads.md): one page for whoever has to approve the server.
- [Sources](reference/sources.md): every factual claim and where it was checked.
- [Checklists](checklists/): one per phase, and [all of them on one page](checklists/all-in-one.md).

## Example server

[`examples/ask-trevor/`](examples/ask-trevor/) is a small, read-only search server written in TypeScript on the official SDK. It shows the build rules in working code, with 54 tests covering authorisation, tenant isolation, hostile content, transport checks and tool-definition changes. It is a teaching example, not a product, and its test token issuer is never for production.

## Videos

This guide accompanies the video series **[MCP Security: Zero to Hero](https://www.youtube.com/playlist?list=PLcnu2ikEBShY)** on YouTube.

For the agents your staff run, see the free [AI Agent Check](https://cafesecurity.github.io/ai-tools/agent-check/).

## Contributing

Corrections are especially welcome. Every claim should trace to a source in [sources](reference/sources.md). See [CONTRIBUTING](CONTRIBUTING.md); report a security problem in the example server through [SECURITY](SECURITY.md).

## Disclaimer

This guide is general information, not professional advice. It is accurate to the best of our knowledge on the date above, but specifications, products and attacks change quickly, and following it does not guarantee that a server is secure. You are responsible for the security of what you build and deploy. Check the linked sources before relying on any detail.

## Licence

Text: [CC BY 4.0](LICENSE). Code, `AGENTS.md`, `CLAUDE.md` and skills: [MIT](LICENSE-CODE).
