# 4. Test

*As of 13 November 2026.* Previous: [3. Build](03-build.md) · Next: [5. Release](05-release.md)

How do you know the controls work? Write tests from the threat model, not from the code, and run the security tests on every build so a regression can't ship.

## What to do

### The minimum test list

Every MCP server should have these, running in CI. The [Ask Trevor example](../examples/ask-trevor/test/) has working versions of the ones marked ✓.

**Authorisation**

- ✓ No token: 401 with a `WWW-Authenticate` header that points to the protected resource metadata.
- ✓ A token for a **different audience**, from your own issuer: 401.
- ✓ A token from a **different issuer**: 401.
- ✓ An **expired** token: 401.
- ✓ A token **without the scope** a tool needs: 403 `insufficient_scope`, naming the scope.
- ✓ A token in the **query string** instead of the header: rejected.
- ✓ The protected resource metadata document lists the right resource and authorisation server.

**Tenant and user isolation**

- ✓ User A asks for User B's document by ID: the same "not found" as a document that doesn't exist (so IDs can't be probed).
- ✓ A search as User A never returns User B's documents, even for a query that matches them.
- Cached results for one user are never served to another (run the same query as two users, back to back).

**Injection through arguments**

- ✓ Over-long strings, wrong types and unknown properties are rejected by the schema.
- Shell metacharacters (`; | & $( )` and backticks) in every string argument reach no shell.
- Path traversal (`../`, absolute paths, symlinks) is refused.
- SQL injection payloads are treated as data.
- URLs pointing at `127.0.0.1`, `169.254.169.254` and private ranges are refused, including via redirects.

**Hostile content in results**

This is the test most servers lack. Put a document in your test data that contains instructions, hidden text and an image link, and check what comes back.

- ✓ Results are tagged with their source, and content written by outsiders is marked external.
- ✓ Hidden text, invisible Unicode and terminal escape codes are stripped.
- Links and images that a client might load automatically are removed or neutralised.

**Transport**

- ✓ A request with a foreign `Origin` header: 403.
- A request whose `Mcp-Name` header doesn't match the tool in the body: 400 `HeaderMismatch`.
- The server is not reachable on any interface other than the one intended.

**Descriptions**

- ✓ The tool list matches the committed snapshot exactly (name, description, schema, annotations). Any change fails the build until the snapshot and changelog are updated together (see [Change](07-change.md)).

**Operations**

- ✓ Rate limits trigger at the configured level.
- ✓ Logs record user, tool, arguments and time, and contain no tokens or document bodies.

### Test with a hostile agent, not just hostile input

Unit tests check your server. Also run the server inside a real agent, with your threat model's "combinations to avoid" connected alongside it, and try to make it leak: plant instructions in a document, then ask an innocent question. You are testing whether your tagging and limits help, and documenting what a client must do on its side.

### Scan and audit

- Run a dependency audit and a secret scanner in CI.
- Run a static analyser that flags shell execution, dynamic code and unparameterised SQL.
- Before release, inspect the server with the official MCP Inspector (a current, patched version, bound to localhost) to see exactly what a client will see.

## What goes wrong

- **No isolation test.** Asana's cross-tenant exposure ran from launch on 1 May to discovery on 4 June 2025. A test that logs in as one tenant and asks for another's data catches this class of bug before launch.
- **Tests that prove the happy path.** A token check tested only with a valid token passes whether or not the audience is checked. Most token bugs survive because nobody tested the wrong token.
- **Demonstrations nobody ran first.** The GitHub, Supabase and WhatsApp demonstrations in the [case file](../reference/case-file.md) were each a short exercise with a planted instruction. Running that exercise yourself is cheaper than reading about it.

## Controls

- The minimum test list in CI, failing the build.
- One hostile-content fixture in your test data, maintained like any other test.
- A hostile-agent exercise before first release and after any change that adds a tool or scope.

> ### If a coding agent is doing this
>
> Have the agent write the security tests **from the threat model and this list, not from the code it just wrote**. Tests written from the implementation tend to confirm what the code does rather than what it should do.
>
> Watch for tests written to pass: assertions loosened until green, a mocked token verifier that accepts everything, or a skipped test. Review the test diff as carefully as the code diff.
>
> A second agent reviewing cold, with only the threat model, the diff and the [`mcp-security-review`](../skills/mcp-security-review/SKILL.md) skill, catches more than the agent that wrote the code.

## Checklist

- [ ] Every authorisation test in the list passes: no token, wrong audience, wrong issuer, expired, missing scope, token in the query string.
- [ ] Tenant and user isolation tests run on every build, including cached results.
- [ ] Injection tests cover shell metacharacters, path traversal, SQL and internal URLs.
- [ ] A hostile-content fixture checks source tagging, stripping of hidden text and removal of auto-loading links.
- [ ] Transport tests cover a foreign `Origin` and a header and body mismatch.
- [ ] A snapshot test fails the build on any change to tool names, descriptions, schemas or annotations.
- [ ] Rate limits and log contents are tested; logs contain no tokens or document bodies.
- [ ] CI runs a dependency audit, a secret scanner and a static analyser.
- [ ] A hostile-agent exercise has been run, and its findings are in the threat model.
- [ ] A person reviewed the test code, not just the results.
