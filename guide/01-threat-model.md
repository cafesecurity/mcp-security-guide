# 1. Threat model

*As of 13 November 2026.* Previous: [0. Decide](00-decide.md) · Next: [2. Design](02-design.md)

What does the server make the model read, what can it make the model do, what can it reach, and what does it add up to next to the other servers an agent will hold? Answer these on one page before you design anything.

## What to do

### Ask the three questions, tool by tool

The [model](../reference/model.md) explains these in full. For each tool, and for the server as a whole:

1. **Feed: what does it make the model read?** Tool names, descriptions, parameter names and defaults, results, resources and prompts. For each, ask: who outside your organisation can write this? An email body, a support ticket, a document shared from outside, a web page, a memo field on an invoice: all of these are written by strangers and will land in the model's context through your results.
2. **Behaviour: what can it make the model do?** Read, write, send, execute or delete. Mark every tool that changes state or sends data anywhere.
3. **Impact: what can it reach, and with whose credentials?** Scopes, tenants, upstream APIs, files, a shell. Think about breadth (how many systems), depth (how much power in each) and time (how long a stolen token stays useful).

### Score it with the letters

Using Meta's [Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/), mark which of the three letters each tool lights:

- **[A]** reads content outsiders can write;
- **[B]** reaches private data or sensitive systems;
- **[C]** changes state or sends data out.

One server that lights all three is a redesign before launch. A server that lights two will meet the third in someone's agent: write down which other servers would complete the set, so the people approving agents know what not to combine it with.

### Write down what you will not defend against

Say plainly what is out of scope (for example: a compromised identity provider, or a user who deliberately leaks their own data). It stops reviewers assuming you covered it.

## What goes wrong

- **One server, all three letters.** In the [GitHub toxic agent flow](https://invariantlabs.ai/blog/mcp-github-vulnerability) demonstration, one token covered public and private repositories, so a single server let an agent read a malicious public issue [A], read private repositories [B] and publish a pull request [C]. Nothing was "hacked": the design allowed it.
- **A master key next to a ticket queue.** In [General Analysis's Supabase demonstration](https://generalanalysis.com/blog/supabase-mcp-blog), a coding agent had the database's `service_role` key, which skips row-level security. A support ticket carried instructions; the agent read them and posted secret tokens back into the ticket. It was a test project, but the shape is common.
- **Two harmless servers.** In Invariant Labs' [WhatsApp demonstration](https://invariantlabs.ai/blog/whatsapp-mcp-exploited), a "fact of the day" server's description steered the legitimate WhatsApp server into sending the user's message history out. Each server alone looked fine.

## The `THREATMODEL.md` template

Commit this file at the root of the server's repository and keep it current. It is short on purpose.

```markdown
# Threat model: <server name>

Owner: <name>          Last reviewed: <date>          Spec version: 2026-07-28

## Brief
<what it is for; who calls it (staff or customers); local or remote;
what it reads; what it changes; what it must never do>

## Tools
| Tool | Reads or acts | [A] outsiders' text | [B] private data | [C] changes or sends | Approval needed |
| ---- | ------------- | ------------------- | ---------------- | -------------------- | --------------- |
|      |               |                     |                  |                      |                 |

## Feed: what outsiders can write
<every field in a result that someone outside can write, and how it is tagged>

## Impact: what it can reach
<upstream systems, scopes, tenants, files, network; whose credentials;
token lifetime>

## Combinations to avoid
<other servers that would complete [A][B][C] alongside this one>

## Top threats and controls
| Threat | Where | Control | Test |
| ------ | ----- | ------- | ---- |

## Out of scope
<what this model does not defend against>
```

The [Ask Trevor example](../examples/ask-trevor/THREATMODEL.md) has a filled-in copy.

## Controls

- Score every tool, not just the server: one read tool and one send tool on the same server are different risks.
- For every field that outsiders can write, decide now how it will be returned: as plain text, tagged with its source, never as instructions.
- Where a tool lights [C], decide who approves each call and how (see [Design](02-design.md#reads-and-writes)).
- Record combinations to avoid, and give that list to whoever approves agents in your organisation.
- Revisit the threat model whenever a tool, scope or upstream system changes (see [Change](07-change.md)).

For a formal exercise, run these steps inside CSA's MAESTRO method; the mapping is in [frameworks](../reference/frameworks.md#csa-maestro).

> ### If a coding agent is doing this
>
> You don't write the threat model by hand, and you don't hand it all to the agent either. With the [`mcp-threat-model`](../skills/mcp-threat-model/SKILL.md) skill, the agent asks you a handful of questions (what it's for, who calls it, what it reads and changes, what it must never do), reads the code, drafts `THREATMODEL.draft.md`, and then asks about what it couldn't see. You answer, correct and reply "approve"; it saves `THREATMODEL.md`.
>
> Coding agents are good at listing and weak at judging, so spend your attention on the Impact column and the "combinations to avoid": agents tend to under-rate how far a token reaches and to miss risks that only appear next to other servers. The threat model is a human-owned document: the agent writes it, but only a person approves it.

## Checklist

- [ ] `THREATMODEL.md` exists, names an owner and a review date, and states the spec version.
- [ ] Every tool is listed with reads or acts, and its [A] [B] [C] letters.
- [ ] Every field that outsiders can write is listed, with how it will be returned.
- [ ] Upstream systems, scopes, tenants and token lifetimes are written down.
- [ ] No single tool, and no single server, lights all three letters without a named approval step.
- [ ] Combinations to avoid are listed and shared with whoever approves agents.
- [ ] Out-of-scope threats are stated.
- [ ] A person, not an agent, has reviewed and approved the threat model.
