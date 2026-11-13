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
