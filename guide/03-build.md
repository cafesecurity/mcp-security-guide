# 3. Build

*As of 13 November 2026.* Previous: [2. Design](02-design.md) · Next: [4. Test](04-test.md)

How to write the server without the classic bugs. Most rules here are ordinary secure coding; what's different is that every argument may have been written by a model that read a stranger's text, and every string you return will be read by a model too.

Snippets are TypeScript and illustrative. The [Ask Trevor example](../examples/ask-trevor/) shows the same rules in working, tested code.

## What to do

### 1. Nothing from outside goes near a shell

Tool arguments, results from upstream systems, URLs from metadata and configuration values can all carry text an attacker wrote. None of it should ever be parsed by a shell.

```ts
import { execFile } from "node:child_process";

// never: the shell reads this string
exec(`grep -rn ${pattern} ${ROOT}`);

// instead: an argument array, no shell, and "--" so input can't pose as an option
execFile("grep", ["-rn", "--", pattern, ROOT], { shell: false });
```

- Never use `exec`, `shell: true`, `eval`, `new Function` or template strings that become commands.
- Never build a server's launch command (its STDIO `command` and `args`) from anything a user, a web page or a model can write.

### 2. Parameterised queries

```ts
// never
db.query(`SELECT * FROM tickets WHERE id = '${ticketId}'`);
// instead
db.query("SELECT * FROM tickets WHERE id = $1 AND tenant_id = $2", [ticketId, tenantFromToken]);
```

### 3. Confine file paths

```ts
import { realpath } from "node:fs/promises";
import path from "node:path";

const target = await realpath(path.resolve(ROOT, userPath)); // follows symlinks
const rel = path.relative(ROOT, target);
if (rel.startsWith("..") || path.isAbsolute(rel)) throw new Error("outside the allowed folder");
```

### 4. Fetch only allowed destinations

If a tool fetches URLs, allow-list the hosts, require HTTPS, and block private, loopback and link-local addresses (including `169.254.169.254`, the cloud metadata service). Use a tested library or an egress proxy rather than hand-written IP parsing, which attackers defeat with octal, hex and IPv4-mapped IPv6 tricks. Re-check each redirect hop. The same applies to any URL your server fetches from OAuth metadata.

### 5. Strict input schemas

Validate every argument against the tool's schema on the server, even if the client validated it too.

```ts
const SearchDocsInput = z.object({
  query: z.string().min(1).max(200),
  limit: z.number().int().min(1).max(25).default(10),
}).strict();
```

Bound every string's length, use enums where you can, and reject unknown properties.

### 6. Validate every token, the whole token

```ts
import { createRemoteJWKSet, jwtVerify } from "jose";

const jwks = createRemoteJWKSet(new URL(`${ISSUER}/.well-known/jwks.json`));

const { payload } = await jwtVerify(token, jwks, {
  issuer: ISSUER,
  audience: "https://mcp.example.com/mcp", // the line people forget
  algorithms: ["RS256"],
});
```

- Check signature, issuer, audience, expiry and scopes on every request. Return 401 with a `WWW-Authenticate` header for an invalid or expired token, and 403 `insufficient_scope` for missing scopes.
- Pin the accepted algorithms. Never accept `none`.
- Take the user and tenant from the verified claims, never from arguments.
- Don't forward the token anywhere (see [Design](02-design.md#which-tokens-does-the-server-accept)).

### 7. Localhost is not a wall

A browser on the developer's machine can reach a local server. A malicious web page can use DNS rebinding to make its requests look local.

- Bind local HTTP servers to `127.0.0.1`, not `0.0.0.0`.
- Validate the `Origin` header and return 403 for unknown origins; the spec requires it. Check `Host` too.
- Require a token even on your own machine, or use STDIO.
- Keep your SDK current: several official SDKs shipped with DNS-rebinding protection off for local servers and have since fixed it.

In the official TypeScript SDK, `createMcpExpressApp()` from `@modelcontextprotocol/express` binds to `127.0.0.1` by default and adds host-header validation. See [`src/server.ts`](../examples/ask-trevor/src/server.ts) in the example.

### 8. Check that headers match the body

Under the 2026-07-28 Streamable HTTP transport, requests carry `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` headers that mirror the body. Servers MUST reject a mismatch with 400 and error `-32020`. Otherwise a gateway can route or rate-limit on one tool name while your server runs another. Check that your SDK does this; if it doesn't, do it yourself.

### 9. Return results as data

```ts
return {
  content: [{
    type: "text",
    text: JSON.stringify({
      source: doc.externalAuthor ? "external" : "internal",
      title: plainText(doc.title),
      excerpt: plainText(doc.body).slice(0, 2000),
    }),
  }],
};
```

`plainText` removes HTML, invisible and bidirectional-control Unicode, and terminal escape codes. Don't return links or images a client might load automatically. Never return secrets.

### 10. Secrets

- Load secrets from the environment or a vault at start-up. Never commit them, and never put them in tool descriptions, results, error messages or logs.
- Mask tokens and keys in logs. Log the token's subject and ID, not the token.
- Give each environment its own credentials. Development credentials must not work in production.

### 11. Dependencies

- Before adding a package, check it exists, that the publisher is who you expect, and that the name isn't a near-miss of a popular one.
- Pin exact versions and commit the lockfile. Install with `npm ci` (or your ecosystem's equivalent) in CI.
- Run a dependency audit in CI and keep the SDK up to date.

### 12. Errors

Return short, generic errors to the client. Keep stack traces, SQL and upstream responses in your own logs.

## What goes wrong

- **mcp-remote, CVE-2025-6514 (CVSS 9.6).** A malicious server's OAuth authorisation URL was passed unsanitised to code that opened a browser. On Windows that meant full command execution ([JFrog](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/)).
- **MCP Inspector, CVE-2025-49596 (CVSS 9.4).** The official debugging tool had no authentication and listened on all interfaces, so a malicious website could run commands on a developer's machine. Fixed in 0.14.1 ([Oligo](https://www.oligo.security/blog/critical-rce-vulnerability-in-anthropic-mcp-inspector-cve-2025-49596)).
- **STDIO launch commands.** In April 2026 OX Security showed that the official SDKs run a local server's launch command from configuration without sanitising it. Anthropic called this expected behaviour and said sanitising is the developer's job. Whoever is right about the protocol, the job lands on you.
- **One added line.** postmark-mcp 1.0.16 added a single line that blind-copied every email to an attacker. Nobody reviewed the upgrade.

## Controls

The twelve rules above. The ones that have caused the most damage so far: no shell, audience check, localhost binding with Origin checks, and pinned dependencies.

> ### If a coding agent is doing this
>
> Put the rules in [`AGENTS.md`](../AGENTS.md) at the root of the repository so the agent reads them every session.
>
> Then **review by hand**, every time: token validation, anything that starts a process, builds SQL, touches file paths or fetches a URL, and every tool description. These are the places where a plausible-looking shortcut becomes a CVE.
>
> **Check every new dependency yourself.** Coding agents sometimes suggest packages that don't exist, or names close to real ones; attackers register those names. Confirm the package, its publisher and its download history before it goes in, and make sure the agent pinned the exact version.
>
> Don't let the agent "fix" a failing auth test by loosening the check. A failing audience test is the test working.

## Checklist

- [ ] No shell anywhere: processes start with argument arrays, `shell: false` and `--` before user input.
- [ ] All SQL is parameterised, with the tenant from the token in every query.
- [ ] File paths are resolved (following symlinks) and confined to an allowed root.
- [ ] Outbound fetches are allow-listed, HTTPS only, with private and link-local ranges blocked on every hop.
- [ ] Every tool has a strict schema: bounded strings, enums where possible, no unknown properties.
- [ ] Token validation checks signature, pinned algorithms, issuer, audience, expiry and scopes on every request.
- [ ] Local HTTP servers bind to 127.0.0.1, validate `Origin` and `Host`, and require a token.
- [ ] Header and body values are checked for consistency (by the SDK or by you).
- [ ] Results are plain text, tagged by source, with no auto-loading links and no secrets.
- [ ] Secrets come from the environment or a vault; logs mask them; development credentials don't work in production.
- [ ] Every dependency was checked to exist and be the real one; versions are pinned; the lockfile is committed; CI runs an audit.
- [ ] Errors returned to clients are generic; details stay in your logs.
- [ ] A person reviewed every line of token handling, process launching, SQL, file and URL code.
