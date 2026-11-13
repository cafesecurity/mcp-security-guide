# 0. Decide

*As of 13 November 2026.* Previous: [README](../README.md) · Next: [1. Threat model](01-threat-model.md)

Should this be an MCP server at all, and if so, what kind? Most of the risk in a server is fixed by four answers you give before writing any code.

## What to decide

### Does it need to be an MCP server?

An MCP server makes your system available to AI agents: the model reads your tool descriptions and results, and decides when to call you. That is the point, and also the risk. Before building one, check the simpler options.

| If… | Then consider… |
| --- | --- |
| The vendor already publishes an official server for the system | Using theirs, from their own source, instead of writing or installing a copy |
| Only your own code will call it, in a fixed sequence | An ordinary API or library. You don't need a model choosing when to call it |
| People want one narrow job done (look up an order, file a ticket) | A single narrow tool, not a server that exposes the whole system |
| The agent only needs to read a few documents | A resource or a search index you already have, behind the same access checks |

The community copy of a vendor's server is the riskiest option of all. postmark-mcp, the first malicious MCP server found in the wild, was an impostor copy of Postmark's official server ([case file](../reference/case-file.md)).

### Four answers that set the shape

1. **Where does it run?** Local (STDIO, launched by the user's client, running with the user's rights) or remote (HTTP, running on your infrastructure, reached over the network). Local servers don't use the spec's OAuth flow; they take credentials from the environment and depend on sandboxing. Remote servers must implement authorisation properly.
2. **Who calls it?** Your own staff, through agents you approve (an internal server like Ask Trevor), or your customers, through agents they choose (a public server like the invoicing example, Quidsworth, in [Design](02-design.md#a-server-for-customers)). With staff you can keep a list of approved agents. With customers you can't, so consent and scopes carry the weight.
3. **Does it only read, or does it act?** Writing, sending, paying and deleting each raise the stakes. A read-only server is far easier to make safe. If it must act, plan from the start to put actions in separate tools, or a separate server, behind a person's approval.
4. **What can it reach?** Name the systems and data behind it, and whose credentials it will use. "Everything in the tenant" is a design problem, not a detail.

### Sort it into a category

Use the eight categories in [the model](../reference/model.md#server-categories) for a first guess at the risk. A local-system server with shell access, a SaaS connector that reads and writes, and a payments server each start with very different defaults.

## What goes wrong

- **Copies of real servers.** postmark-mcp copied Postmark's official code under a plausible name, then added one line that copied every outgoing email to an attacker. About 1,643 downloads before removal.
- **Servers nobody registered.** OWASP lists shadow MCP servers as MCP09: servers that developers start on their own machines or teams deploy without review, which nobody inventories and nobody patches.
- **Feature creep before design.** "Could it also send the follow-up email?" is the request that turns a safe read-only search server into one that holds private data, untrusted content and a way out, all at once.

## Controls

- Write a one-paragraph **brief** before any code: what it is for, who calls it, where it runs, what it reads, what it changes, and what it must never do. Commit it as the first section of `THREATMODEL.md` (template in [Threat model](01-threat-model.md#the-threatmodelmd-template)).
- Give the server a named **owner** from day one, and register it in your organisation's inventory, even as a prototype.
- If the vendor has an official server, use it, or explain in the brief why not.
- Before you install or approve any server you didn't write, audit the exact version with the [`mcp-server-audit`](../skills/mcp-server-audit/SKILL.md) skill: who publishes it, what its descriptions tell the model, what its code does, and, in a Docker sandbox with fake credentials, what it does when run.
- Default to **read-only**. Treat every action as a separate decision with its own justification.
- Default to **remote** for anything used by more than one person, so it runs in one place you control and can switch off, rather than on every developer's laptop.

> ### If a coding agent is doing this
>
> Don't let the agent scaffold a server before these questions are answered. Agents will happily generate a full read-write server with every tool they can think of, because that looks helpful.
>
> Instead, write the brief yourself (it takes ten minutes) and give it to the agent as the task. Tell it the server is read-only, or which actions are allowed, and that anything beyond the brief needs your approval. The rules in [`AGENTS.md`](../AGENTS.md) include this.

## Checklist

- [ ] There is a written reason why this is an MCP server rather than an API, a library or the vendor's own server.
- [ ] The brief states where it runs (local or remote), who calls it (staff or customers), what it reads, what it changes, and what it must never do.
- [ ] It has a named owner and an entry in the inventory.
- [ ] Every action (write, send, pay, delete) is listed and justified on its own; the default is read-only.
- [ ] The systems and data behind it are named, with whose credentials it will reach them.
- [ ] The brief is committed as the first section of `THREATMODEL.md`.
