# 5. Release

*As of 13 November 2026.* Previous: [4. Test](04-test.md) · Next: [6. Deploy and operate](06-deploy-operate.md)

How do you publish the server so that nobody can impersonate it, nobody can publish a version in your name, and users can tell when it changes?

An internal server may not need publishing at all: give approved agents its address and nobody else. Its build pipeline still matters, because a stolen key or a tampered dependency reaches an internal server just as easily.

## What goes wrong

So far, four things:

1. **Someone pretends to be you.** postmark-mcp copied Postmark's official server under a name that looked official. UpGuard has since found [misspelled MCP server names](https://www.upguard.com/blog/typosquatting-in-the-mcp-ecosystem) in real developers' configuration files. Lookalikes work because people type names from memory.
2. **Someone steals your publishing key.** In September 2025 the Shai-Hulud worm stole npm tokens from developers' machines and build systems and used them to publish poisoned versions of the victims' other packages. GitHub [revoked all classic npm tokens](https://github.blog/changelog/2025-12-09-npm-classic-tokens-revoked-session-based-auth-and-cli-token-management-now-available/) on 9 December 2025; trusted publishing, launched that July, lets a build system publish without a stored token. Then in May 2026, attackers published malicious TanStack versions through the project's own trusted pipeline without stealing an npm token: they extracted a short-lived OIDC token from the release runner ([TanStack's postmortem](https://tanstack.com/blog/npm-supply-chain-compromise-postmortem)). The pipeline needs guarding too.
3. **The shop doesn't check the goods.** In April 2026, OX Security reported that 9 of 11 MCP marketplaces it tried accepted a harmless proof-of-concept malicious server. A listing tells you a server exists, not that it's safe.
4. **You change your own descriptions.** Every edit to a tool description is an edit to every user's prompt. If it isn't reviewed and announced, it looks exactly like a rug pull.

MITRE ATLAS lists this family as AML.T0104, Publish Poisoned AI Agent Tool.

## What to do

### Claim your name

The [official MCP Registry](https://modelcontextprotocol.io/registry/about) gives servers names built from a domain or GitHub namespace you control, written back to front, and checks that you own it: by a DNS record, an HTTP file, or by logging in to the GitHub organisation.

```bash
# prove you own example.com, then publish under it
mcp-publisher login dns --domain example.com --private-key-file key.pem
mcp-publisher publish
```

```json
// server.json: the name, the hosted server, and the local package
{ "name": "com.example/invoices",
  "remotes":  [{ "type": "streamable-http", "url": "https://mcp.example.com/mcp" }],
  "packages": [{ "registryType": "npm", "identifier": "@example/mcp" }] }
```

```json
// package.json: tells the registry this package is yours
{ "name": "@example/mcp", "mcpName": "com.example/invoices" }
```

The registry checks that the package really is yours. It doesn't review your code, so this proves identity, not safety. Then link to that exact name and address from your website, documentation and product settings, so users copy it rather than type it.

Publish packages under your organisation's own namespace (`@example/...`), never a personal account.

### Publish without long-lived keys

Use trusted publishing from your build system, so there is no long-lived token to steal, and you get a provenance record saying which source and which build produced each version.

```yaml
permissions:
  id-token: write        # trusted publishing: no NPM_TOKEN secret
  contents: read
jobs:
  publish:
    environment: release # a named person approves each release
    steps:
      - uses: actions/checkout@<full commit SHA>   # pinned, not a tag
      - run: npm ci
      - run: npm test
      - run: npm publish # provenance is added automatically
```

Then guard the pipeline:

- A release environment that needs a named person to approve each run.
- No publishing from pull requests or forks.
- Third-party actions pinned to full commit SHAs.
- Two-factor authentication on every maintainer account.
- Release jobs that only build and publish: no caches shared with untrusted jobs.

### Treat a description change like an API change

- Keep tool definitions in a committed snapshot (see [Test](04-test.md)) and publish its hash with each release.
- Bump the version whenever a tool's name, description, schema or annotations change.
- Say what changed, in words, in the release notes, so people who pinned the old definition know why their client is asking again.

### Pin what you depend on

Ship a lockfile, and publish the exact versions of the SDK and key dependencies in the release notes, so users can check what they're running.

## Controls

- Registry name verified against your own domain or GitHub organisation; links from your own site.
- Trusted publishing with provenance; a guarded release environment; pinned actions; two-factor on every maintainer.
- Tool definitions frozen, hashed and announced on change.

> ### If a coding agent is doing this
>
> Agents will happily publish if they can. **Keep publishing credentials out of the agent's reach**: no registry tokens in the environment the agent runs in, no permission to push tags, and no access to the release environment.
>
> A person tags each release and approves the release job. The agent can prepare the release with [`prompts/pre-release.md`](../prompts/pre-release.md), which produces a checklist and a draft of the release notes for a person to confirm.

## Checklist

- [ ] The server's registry name is verified against a domain or GitHub organisation you control.
- [ ] Packages are published under the organisation's namespace, not a personal account.
- [ ] Your website and docs link to the exact registry name and server address.
- [ ] Publishing uses trusted publishing with provenance; there is no long-lived publishing token.
- [ ] The release job needs a named person's approval, never runs from pull requests, and pins actions to commit SHAs.
- [ ] Every maintainer account has two-factor authentication.
- [ ] The tool-definition snapshot's hash is published with each release.
- [ ] Any change to a tool's name, description, schema or annotations bumps the version and is explained in the release notes.
- [ ] The lockfile is shipped and key dependency versions are listed.
- [ ] No coding agent has access to publishing credentials or the release environment.
