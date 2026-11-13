# Ask Trevor: example server

A small, read-only MCP search server that shows the [MCP Security Guide](../../README.md)'s build rules in working, tested code.

> **This is a teaching example, not a product.** It serves a bundled, made-up set of documents and ships with a throwaway **test token issuer that must never be used in production**. To run it for real you need your own identity provider, your own document source and the production concerns listed under [What's not included](#whats-not-included).

*Built on the official TypeScript SDK (`@modelcontextprotocol/server` 2.4.0, `@modelcontextprotocol/express` 2.0.2, `@modelcontextprotocol/node` 2.1.2) for the MCP specification of 2026-07-28. Node 22.12 or later. As of 13 November 2026.*

## What it does

Two tools, both read-only:

| Tool | Does |
| --- | --- |
| `search_docs` | Searches the documents the signed-in user may read. Up to 25 results, each with a plain-text excerpt and its source (`internal` or `external`). |
| `get_doc` | Returns one document the user may read, or `not_found`. |

The sample documents (`src/corpus.ts`) belong to two tenants, have per-document access lists, and include one hostile document from an outside supplier with hidden instructions, invisible characters, a terminal escape and a tracking image.

## Where each rule lives

| Rule (guide page) | Code | Test |
| --- | --- | --- |
| Check every token: signature, pinned algorithms, issuer, audience, expiry, scope ([3. Build §6](../../guide/03-build.md#6-validate-every-token-the-whole-token)) | `src/auth.ts` `jwtVerifier`; `src/server.ts` `requireBearerAuth` | `test/auth.test.ts` |
| Never pass tokens through ([2. Design](../../guide/02-design.md#which-tokens-does-the-server-accept)) | `src/auth.ts` (the token is never used beyond verification) | — |
| User and tenant from the token only ([2. Design](../../guide/02-design.md#tenants-and-state)) | `src/auth.ts` `callerFrom`; `src/tools.ts` `buildServer` | `test/isolation.test.ts` |
| Access checked at query time; same answer for missing and forbidden | `src/corpus.ts` `canRead`, `memoryStore` | `test/isolation.test.ts` |
| Strict input schemas ([3. Build §5](../../guide/03-build.md#5-strict-input-schemas)) | `src/tools.ts` `SearchDocsInput`, `GetDocInput` | `test/schema.test.ts` |
| Results as plain text, tagged by source, no links or images ([3. Build §9](../../guide/03-build.md#9-return-results-as-data)) | `src/text.ts` `plainText`; `src/tools.ts` | `test/results.test.ts` |
| Descriptions as plain documentation ([2. Design](../../guide/02-design.md#tool-descriptions)) | `src/tools.ts` | `test/snapshot.test.ts` |
| Localhost is not a wall: loopback bind, Host and Origin checks ([3. Build §7](../../guide/03-build.md#7-localhost-is-not-a-wall)) | `src/server.ts` `createApp` (`createMcpExpressApp`) | `test/transport.test.ts` |
| Headers must match the body ([3. Build §8](../../guide/03-build.md#8-check-that-headers-match-the-body)) | SDK (`createMcpHandler`) | `test/transport.test.ts` |
| Stateless: no sessions, no GET stream (spec 2026-07-28) | `src/server.ts` | `test/transport.test.ts` |
| Rate limit and result caps ([6. Deploy and operate](../../guide/06-deploy-operate.md#rate-limits-and-caps)) | `src/ratelimit.ts`; `src/tools.ts` | `test/ops.test.ts` |
| Logs record who did what, not what they saw ([6. Deploy and operate](../../guide/06-deploy-operate.md#logs)) | `src/log.ts`; `src/tools.ts` `record` | `test/ops.test.ts` |
| Tool definitions frozen and checked ([7. Change](../../guide/07-change.md)) | `tool-definitions.snapshot.json`; `scripts/check-tool-snapshot.ts` | `test/snapshot.test.ts` |

The threat model for this server is in [THREATMODEL.md](THREATMODEL.md).

## Run the tests

```bash
npm ci
npm test              # 50 tests: auth, isolation, schemas, hostile content, transport, snapshot, operations
npm run typecheck
npm run snapshot:check
```

## Try it locally

```bash
npm run dev
```

This starts the server on `http://127.0.0.1:3333/mcp` with the **test issuer** and prints a one-hour token for three sample users (alice, priya, dana). Use one as a bearer token in an MCP client that speaks the 2026-07-28 protocol, or with the official MCP Inspector (a current, patched version).

## Run it against a real identity provider

`src/main.ts` takes all configuration from the environment and has no defaults for anything security-relevant:

| Variable | Meaning |
| --- | --- |
| `MCP_RESOURCE_URL` | This server's canonical URI, e.g. `https://trevor.example.com/mcp`. Tokens must carry it as their audience. |
| `OAUTH_ISSUER` | Your identity provider's issuer identifier |
| `OAUTH_JWKS_URL` | Its signing keys |
| `OAUTH_AUTHORIZE_URL`, `OAUTH_TOKEN_URL` | Its endpoints, advertised to clients |
| `HOST`, `PORT` | Bind address (default `127.0.0.1:3333`) |
| `ALLOWED_HOSTS` | Comma-separated hostnames; required if `HOST` is not loopback |

Your identity provider must issue JWT access tokens for the resource with `sub`, `tenant`, `groups`, `scope` (including `docs.read`), `exp` and, ideally, `jti` and `client_id`. Configure it to issue tokens only to the agents you have approved.

```bash
npm ci && npm run build
MCP_RESOURCE_URL=... OAUTH_ISSUER=... OAUTH_JWKS_URL=... OAUTH_AUTHORIZE_URL=... OAUTH_TOKEN_URL=... npm start
```

## What's not included

- A real document source. Replace `memoryStore` with calls to your system of record, made as the signed-in user with a token obtained by exchange, never by forwarding the user's token.
- Write tools. Actions belong in a separate server with a person's approval of each action (see [2. Design](../../guide/02-design.md#reads-and-writes)).
- TLS, a gateway, a shared rate-limit store, log shipping, alerting and a kill switch (see [6. Deploy and operate](../../guide/06-deploy-operate.md)).
- A customer-facing design. See the Quidsworth section in [2. Design](../../guide/02-design.md#a-server-for-customers).

## Changing a tool

1. Get a person's approval for the new wording or schema.
2. Change `src/tools.ts`.
3. `npm run snapshot:update`, then bump the version in `package.json` and `src/tools.ts`, and describe the change in `CHANGELOG.md`.
4. Note the new snapshot hash in the release notes.

## Licence

MIT, see [LICENSE-CODE](../../LICENSE-CODE).
