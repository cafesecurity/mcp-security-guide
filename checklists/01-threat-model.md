# Checklist: 1. Threat model

*Generated from [01-threat-model.md](../guide/01-threat-model.md). Edit the page, not this file.*

- [ ] `THREATMODEL.md` exists, names an owner and a review date, and states the spec version.
- [ ] Every tool is listed with reads or acts, and its [A] [B] [C] letters.
- [ ] Every field that outsiders can write is listed, with how it will be returned.
- [ ] Upstream systems, scopes, tenants and token lifetimes are written down.
- [ ] No single tool, and no single server, lights all three letters without a named approval step.
- [ ] Combinations to avoid are listed and shared with whoever approves agents.
- [ ] Out-of-scope threats are stated.
- [ ] A person, not an agent, has reviewed and approved the threat model.

## Scorecard (one per agent that will hold this server)

| Server or tool | [A] Reads content outsiders can write | [B] Reaches private data or sensitive systems | [C] Changes state or sends data out |
| --- | --- | --- | --- |
| | | | |
| | | | |
| **Agent total** | | | |

All three lit: redesign, split the agent, or require a person's approval. See [the model](../reference/model.md#scorecard).
