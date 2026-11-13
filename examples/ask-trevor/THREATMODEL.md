# Threat model: Ask Trevor (example)

Owner: the guide's maintainers          Last reviewed: 13 November 2026          Spec version: 2026-07-28

This is the filled-in version of the template in [guide/01-threat-model.md](../../guide/01-threat-model.md), for the example server in this folder.

## Brief

A read-only MCP server that lets a company's staff search their internal documents through an approved AI agent. Remote (Streamable HTTP), for staff only, through agents the company has approved. It reads documents the signed-in user is already allowed to read. It changes nothing. It must never return a document the user can't read, never return another tenant's data, never forward the user's token, and never send data anywhere.

## Tools

| Tool | Reads or acts | [A] outsiders' text | [B] private data | [C] changes or sends | Approval needed |
| --- | --- | --- | --- | --- | --- |
| `search_docs` | Reads | Yes: documents written by suppliers and guests | Yes: internal documents | No | No (read-only) |
| `get_doc` | Reads | Yes, as above | Yes | No | No (read-only) |

The server lights [A] and [B]. It must never be combined, in one agent session, with a server that lights [C] without a person approving each outbound action.

## Feed: what outsiders can write

| Field | Who writes it | How it is returned |
| --- | --- | --- |
| Document `title`, `body` | Staff, and outsiders for documents from suppliers or guests | Plain text (`src/text.ts`): no HTML, hidden characters, terminal escapes, links or images; tagged `source: "external"` when the author is outside the organisation |
| `author` | The document platform | As stored (an address) |

Tool names and descriptions are written by the maintainers only, frozen in `tool-definitions.snapshot.json`, and checked on every build.

## Impact: what it can reach

- Upstream: the bundled sample corpus (`src/corpus.ts`). In a real deployment, the document platform, called as the signed-in user so that the platform checks access.
- Credentials: none of its own in this example. A real deployment would exchange the user's token for a separate upstream token (on-behalf-of or token exchange); it never forwards the user's token.
- Tokens accepted: JWTs from one issuer, for this server's URL as audience, with the `docs.read` scope, a `tenant` claim and an expiry. Lifetime is set by the identity provider; the example's test issuer uses five minutes.
- Network: listens on 127.0.0.1 by default. Makes no outbound requests.

## Combinations to avoid

Any server that can send email or messages, post publicly, create links or tickets visible to outsiders, or fetch arbitrary URLs. Together with this server's [A] and [B] that is the lethal trifecta.

## Top threats and controls

| Threat | Where | Control | Test |
| --- | --- | --- | --- |
| Token for another service accepted | `src/auth.ts` | Audience checked by `jwtVerify` and again by the SDK's `expectedResource` | `test/auth.test.ts` |
| Token from another issuer, untrusted key, `none` algorithm, expired | `src/auth.ts` | Issuer, keys and algorithms pinned; `exp` required | `test/auth.test.ts` |
| Token passed in the URL | `src/server.ts` | `requireBearerAuth` reads the `Authorization` header only | `test/auth.test.ts` |
| Reading another user's or tenant's documents | `src/corpus.ts` | Caller from the verified token only; access checked at query time; "not found" for both missing and forbidden | `test/isolation.test.ts` |
| Caller picks their own identity or tenant through arguments | `src/tools.ts` | Strict schemas reject unknown properties | `test/schema.test.ts` |
| Instructions or tracking links hidden in documents | `src/text.ts`, `src/tools.ts` | Plain text, source tags, links and images removed | `test/results.test.ts` |
| A web page talking to the local server (DNS rebinding) | `src/server.ts` | Loopback bind; SDK Host and Origin validation | `test/transport.test.ts` |
| A gateway and the server disagreeing about which tool is called | SDK | Header and body consistency check | `test/transport.test.ts` |
| Bulk extraction | `src/ratelimit.ts`, `src/tools.ts` | Per-user rate limit; at most 25 results; excerpts and bodies capped | `test/ops.test.ts`, `test/schema.test.ts` |
| Silent change to a tool description | `tool-definitions.snapshot.json` | Snapshot check in CI | `test/snapshot.test.ts` |
| Tokens or content in logs | `src/log.ts` | Structured events; arguments masked; no bodies | `test/ops.test.ts` |

## Out of scope

- A compromised identity provider or signing key.
- Over-sharing in the source system: if a document is shared with everyone by mistake, the server will return it. Fix permissions at the source before launch.
- The agent that calls the server. Controlling which agents may get a token is the identity provider's job (see [For security leads](../../reference/for-security-leads.md)).
- Production concerns this example doesn't include: a real identity provider, a shared rate-limit store, TLS termination, persistent log shipping.
