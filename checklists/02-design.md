# Checklist: 2. Design

*Generated from [02-design.md](../guide/02-design.md). Edit the page, not this file.*

- [ ] The identity model is per-user delegated access, or the threat model explains why not.
- [ ] No service account with organisation-wide rights sits behind the server.
- [ ] The server checks every token's audience, issuer, expiry and scopes.
- [ ] The server never forwards a client's token upstream; upstream calls use a separate token.
- [ ] `scopes_supported` is minimal; privileged tools need a step-up scope; no wildcard scopes.
- [ ] For internal servers: only approved clients can get a token. For public servers: per-client consent, showing the client's URL, with a page to disconnect.
- [ ] If the server fronts a third-party API with a static client ID: per-client consent, exact redirect matching and single-use `state` set after consent.
- [ ] Read and acting tools are separate; every acting tool needs a person's approval of the actual action, outside the chat.
- [ ] Acting tools have caps, volume alerts and idempotency keys.
- [ ] Tool descriptions are plain documentation and are frozen in a snapshot file.
- [ ] Results are plain text, tagged by source, capped, and never include secrets or auto-loading links.
- [ ] Tenant and user come from the token and appear in every query and cache key.
- [ ] Any state handles are random, expiring and bound to the user from the token.
