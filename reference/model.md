# The model

*As of 13 November 2026.*

This page explains the two ideas the rest of the guide uses: treating every server two ways at once, and counting risk across everything one agent holds.

## Software and text

Treat every MCP server two ways at once: as software that can have ordinary bugs, and as text that your model reads and may obey. Most guidance covers one or the other. Real incidents need both.

| Layer | Treat the server as | Typical threats | Typical controls |
| --- | --- | --- | --- |
| CIA (confidentiality, integrity, availability) | Software | Command injection, path traversal, SSRF, missing authentication, leaked tokens, malicious packages | Validate inputs, pass arguments as arrays rather than shell strings, OAuth with audience checks, pinned and verified packages, sandboxing |
| FBI (feed, behaviour, impact) | Text the model reads | Tool poisoning, rug pulls, tool shadowing, instructions hidden in tool results, context leaking between users | Treat descriptions and results as data, pin and re-approve tool definitions, limit what one agent holds at once, human approval for changes, log every call |

**Feed** is what the agent reads. **Behaviour** is what it does with it. **Impact** is how far the damage can spread: how many systems (breadth), how much power in each (depth) and for how long (time).

```
            Feed                     Behaviour                 Impact
   ┌───────────────────┐      ┌───────────────────┐    ┌───────────────────┐
   │ tool names,        │      │ which tool the     │    │ scopes, tenants,   │
   │ descriptions,      │ ───▶ │ model calls, and   │──▶ │ upstream APIs,     │
   │ parameters,        │      │ with what          │    │ files, shell,      │
   │ results, resources │      │ arguments          │    │ how long it lasts  │
   └───────────────────┘      └───────────────────┘    └───────────────────┘
      outsiders write              the model               your credentials
      some of this                 decides                 decide
```

Outsiders never talk to the model directly. Their text reaches it through results, and a third-party server's own descriptions are also text the model reads.

## Three questions for every server

1. **Feed: what does it make the model read?** Tool names, descriptions, parameter names and default values, results, resources and prompts all reach the model. For each one, ask who outside your organisation can write it.
2. **Behaviour: what can it make the model do?** Read only, write, send, execute or delete. The answer sets how much approval each call needs.
3. **Impact: what can it reach, and with whose credentials?** Scopes, tenants, upstream APIs, the local file system and shell.

Then ask a fourth question across the agent: **what does this server add up to alongside the others?** Most serious MCP attacks combine two servers that are each harmless alone.

## Composition: count across the agent

Risk lives in the agent, not in any one server. Count across every server an agent holds during one task.

### Two tests

- **Lethal trifecta (data theft).** Simon Willison's [lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/): private data, plus untrusted content, plus a way to send data out. All three in one agent means an attacker who controls the content can steal the data.
- **[Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/) (Meta, October 2025).** In one session, an agent should have at most two of:
  - **[A]** processing untrustworthy inputs;
  - **[B]** access to sensitive systems or private data;
  - **[C]** the ability to change state or communicate externally.

  If a task needs all three, the agent should not run on its own: a person approves, or another reliable check does.

The trifecta is the best test for data theft. It does not cover agents that change or destroy things: an agent that wipes a database needs no attacker and no way out. Because [C] includes changing state, the Rule of Two catches that case too. Meta is explicit that the rule supplements least privilege and other basics. It does not replace them.

### What it looks like

In Invariant Labs' [WhatsApp demonstration](https://invariantlabs.ai/blog/whatsapp-mcp-exploited), a harmless-looking "fact of the day" server had a poisoned tool description. The same agent also held the legitimate WhatsApp server, with the user's messages [B] and the ability to send [C]. The poisoned description [A] steered the WhatsApp tools to send the message history to an attacker. The malicious server never touched WhatsApp itself.

One server can also hold all three. In the [GitHub toxic agent flow](https://invariantlabs.ai/blog/mcp-github-vulnerability), a token that covered public and private repositories let an agent read a malicious public issue [A], read private repositories [B] and open a public pull request [C].

### Scorecard

Fill in one table per agent. A third-party server's tool descriptions count as untrusted input [A]. The example below is hypothetical.

| Server or tool | [A] Reads content outsiders can write | [B] Reaches private data or sensitive systems | [C] Changes state or sends data out |
| --- | --- | --- | --- |
| GitHub server, token for all repos | Yes: public issues and pull requests | Yes: private repositories | Yes: comments, pull requests |
| Internal wiki search | No | Yes | No |
| Slack server, posting enabled | Yes: messages from guests | Yes: private channels | Yes: posts messages |
| **Agent total** | **Yes** | **Yes** | **Yes** |

All three are lit, so redesign before launch. Remove one letter for the whole session:

- Scope the GitHub token to the one repository the task needs.
- Make Slack read-only, or require approval for each post.
- Split the job into two agents, one that reads outsiders' content and one that acts.

The Rule of Two allows an agent to move between configurations within a session, but not to hold all three at once without supervision.

A blank scorecard is in [checklists/01-threat-model.md](../checklists/01-threat-model.md).

## Server categories

Most MCP servers fall into eight broad categories by what they can reach and do. Use the category as a first guess, then confirm it with the scorecard. This classification is this guide's own, not a published taxonomy.

Many of the servers people install run on developers' own machines, with developers' own rights, which is why the local categories matter.

| Category | Examples | Usual letters | Signature threats | Case |
| --- | --- | --- | --- | --- |
| Local system | Files, shell, git, Docker, code runners | [B] [C], often with the developer's own rights | Command injection, path traversal, STDIO launch commands | MCP Inspector; OX Security on STDIO |
| Web access | Fetch, search, browser automation | [A] [C] | Instructions hidden in web pages, SSRF, data leaving through URLs | — |
| SaaS connectors | GitHub, Slack, Jira, email, CRM | Often [A] [B] [C] in one server | Toxic flows, broad OAuth tokens, data crossing between customers | GitHub toxic flow; Asana; postmark-mcp |
| Data stores | Databases, warehouses, vector stores, internal search | [B], sometimes [C] | Over-powered keys, SQL injection, oversharing | Supabase demonstration |
| Cloud and infrastructure | Cloud consoles, Kubernetes, CI/CD, monitoring | [B] [C], with very high Impact | Destructive actions, credential theft, mistakes at scale | — |
| Transactions and the real world | Payments, orders, bookings, customer messaging, devices | [C] with money or physical consequences | Unauthorised actions, account takeover | Obsidian Security OAuth takeover |
| Memory and orchestration | Memory stores, sub-agents, gateways that bundle many servers | Whatever they store or bundle | Context that persists across tasks; one gateway holding every letter | — |
| Utilities | Time, maths, formatting, "fact of the day" | None on their own | A poisoned description steering other servers | WhatsApp demonstration |

The cases are in [case-file.md](case-file.md).

- **Classify tools, not just servers.** One GitHub server can be read-only or able to write, depending on its tools and the token's scope.
- **Tag two more things for every server.** Where it runs (local STDIO or remote HTTP), and who publishes it (the vendor, the community or your own team). A community copy of a SaaS connector, run locally, carries very different risk from the vendor's own remote server.
- **Don't wave utilities through.** They are the servers people install without thinking, and their descriptions still reach the model.

## Nine stages

Every MCP connection passes through nine stages, from the user's point of view: discover and install, configure and launch, authorise, list tools, call, result, compose, update, operate and retire. The [lifecycle pages](../README.md#the-lifecycle) follow the builder's point of view instead, and each one says which of these stages it protects. The framework IDs for each stage are in [frameworks.md](frameworks.md#by-stage).
