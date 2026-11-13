# Spec checklist (MCP 2026-07-28)

*As of 13 November 2026. Checked against the specification pages linked below on that date.*

This page lists what the current MCP specification requires for authorisation and security, in plain words, with the requirement level the spec uses. It is a checklist, not a replacement: when you implement a row, read the linked section.

The rows come from three pages:

- [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) (part of the specification)
- [Authorization Security Considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations) (part of the specification)
- [Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) (a companion document in the docs, not the specification itself, but written with MUST and SHOULD language)

**Who it applies to.** Authorisation is optional in MCP. When used, it is written for HTTP transports. Servers on the STDIO transport SHOULD NOT follow it and should take credentials from the environment instead, so local servers rely on the controls in [Deploy and operate](../guide/06-deploy-operate.md) and the "Local server" rows below.

**Abbreviations.** AS is the authorisation server. PRM is Protected Resource Metadata (RFC 9728). CIMD is Client ID Metadata Documents.

## 1. Discovery and registration

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 1.1 | HTTP implementations that support authorisation follow this spec. STDIO implementations do not, and take credentials from the environment. | Implementations | SHOULD / SHOULD NOT |
| 1.2 | Implement OAuth 2.1 with suitable protections for both confidential and public clients. | AS | MUST |
| 1.3 | Publish Protected Resource Metadata (RFC 9728). | Servers | MUST |
| 1.4 | Use PRM to discover the AS. | Clients | MUST |
| 1.5 | Offer RFC 8414 metadata or OpenID Connect Discovery (at least one). | AS | MUST |
| 1.6 | Support both discovery mechanisms. | Clients | MUST |
| 1.7 | Get a client ID through CIMD, pre-registration or Dynamic Client Registration before starting the flow. | Clients | MUST |
| 1.8 | Support CIMD. | AS and clients | SHOULD |
| 1.9 | Dynamic Client Registration (RFC 7591) is deprecated and kept only for backwards compatibility. | AS and clients | MAY |

## 2. Authorisation request and response

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 2.1 | Use PKCE, and check that the AS supports it before starting. If `code_challenge_methods_supported` is missing from the AS metadata, refuse to proceed. | Clients | MUST |
| 2.2 | Use the `S256` challenge method where technically capable. | Clients | MUST |
| 2.3 | Include `code_challenge_methods_supported` in OpenID Connect Discovery metadata. | AS using OIDC Discovery | MUST |
| 2.4 | Send the `resource` parameter (RFC 8707) in both the authorisation request and the token request, naming the server's canonical URI. Send it even if the AS does not support it. | Clients | MUST |
| 2.5 | Before redirecting, record the issuer from the AS's validated metadata alongside the PKCE verifier. | Clients | MUST |
| 2.6 | Include `iss` in authorisation responses, including error responses (RFC 9207). A future revision is expected to make this a MUST. | AS | SHOULD |
| 2.7 | If you include `iss`, advertise `authorization_response_iss_parameter_supported: true`. | AS | MUST |
| 2.8 | Check `iss` (RFC 9207 Section 2.4) before sending the code to any token endpoint. If metadata says `iss` is supported and it is missing, reject. If `iss` is present, compare it with the recorded issuer by exact string comparison, with no normalisation. | Clients | MUST |
| 2.9 | On an `iss` mismatch in an error response, don't act on or display the error fields. | Clients | MUST NOT |
| 2.10 | Register redirect URIs with the AS. | Clients | MUST |
| 2.11 | Validate redirect URIs exactly against the registered values. | AS | MUST |
| 2.12 | Use and verify `state`, and discard responses where it is missing or wrong. | Clients | SHOULD |
| 2.13 | Serve every AS endpoint over HTTPS. Redirect URIs are `localhost` or HTTPS. | AS / clients | MUST |

## 3. Scopes

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 3.1 | Put the scopes a request needs in the `WWW-Authenticate` challenge on a 401. | Servers | SHOULD |
| 3.2 | Choose scopes from the challenge first, then from `scopes_supported`. Request only what the task needs. | Clients | SHOULD |
| 3.3 | Treat the challenged scopes as authoritative for the current operation. | Clients | MUST |
| 3.4 | On a runtime scope shortfall, return 403 with `error="insufficient_scope"`, the needed `scope` and `resource_metadata`. List every scope the operation needs in one challenge. | Servers | SHOULD |
| 3.5 | When stepping up, request the union of previously requested and newly challenged scopes, with a retry limit. | Clients | SHOULD |
| 3.6 | Account for scope hierarchies when deciding whether a token is enough. | Servers | MUST |
| 3.7 | Don't put `offline_access` in the challenge or in `scopes_supported`. | Servers | SHOULD NOT |

## 4. Tokens

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 4.1 | Send the token in the `Authorization: Bearer` header on every request. Never in the URL query string. | Clients | MUST / MUST NOT |
| 4.2 | Validate every token (OAuth 2.1 Section 5.2), including that it was issued for this server as its audience. Return 401 for invalid or expired tokens. | Servers | MUST |
| 4.3 | Send a server only tokens issued by that server's AS. | Clients | MUST NOT send others |
| 4.4 | Accept only tokens meant for this server. Never accept or transit any other token. | Servers | MUST / MUST NOT |
| 4.5 | When calling an upstream API, use a separate token from the upstream AS. Never pass the client's token through. | Servers | MUST NOT pass through |
| 4.6 | Store tokens securely. | Clients and servers | MUST |
| 4.7 | Issue short-lived access tokens. | AS | SHOULD |
| 4.8 | Rotate refresh tokens for public clients. | AS | MUST |
| 4.9 | Keep refresh tokens confidential in transit and storage, and don't assume one will be issued. | Clients | MUST |

## 5. Proxies and consent

These apply to an MCP server that fronts a third-party API with one static client ID (the "confused deputy" case in the Best Practices page).

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 5.1 | Get the user's consent for each dynamically registered client before forwarding to the third-party AS. Keep a per-user registry of approved client IDs and check it first. | Proxy servers | MUST |
| 5.2 | The consent page names the client, shows the third-party scopes and the redirect URI, has CSRF protection, and cannot be framed (`frame-ancestors` or `X-Frame-Options: DENY`). | Proxy servers | MUST |
| 5.3 | Consent cookies use the `__Host-` prefix, `Secure`, `HttpOnly` and `SameSite=Lax`, are signed (or server-side), and are bound to the client ID. | Proxy servers | MUST |
| 5.4 | Match `redirect_uri` exactly against the registered value. No wildcards or patterns. | Proxy servers | MUST |
| 5.5 | Generate `state` randomly, store it only after consent, check it exactly at the callback, make it single-use and short-lived (for example ten minutes). | Proxy servers | MUST |

## 6. Client-side URL handling and SSRF

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 6.1 | Allow only `https://` authorisation URLs (`http://` only for loopback during development). Reject `javascript:`, `data:`, `file:` and similar. Prefer an allow-list. | Clients | MUST |
| 6.2 | Never open URLs through a shell. Use the platform's non-shell API. | Clients | MUST NOT |
| 6.3 | Sanitise and validate every URL received from a server. | Clients | MUST |
| 6.4 | Web-based clients set a Content Security Policy that blocks inline script. | Clients | SHOULD |
| 6.5 | Clients deployed on servers consider SSRF when fetching OAuth URLs. | Server-side clients | MUST |
| 6.6 | Require HTTPS for OAuth URLs in production; block private, loopback and link-local ranges (including `169.254.169.254`); apply the same checks to each redirect hop. Use a tested library, not hand-written IP parsing. | Clients | SHOULD |
| 6.7 | Route discovery through an egress proxy that blocks internal destinations. Watch for DNS answers that change between check and use. | Server-side client operators | SHOULD |
| 6.8 | Apply the same SSRF protections when fetching Client ID Metadata Documents. | AS | SHOULD |

## 7. Local servers

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 7.1 | For one-click local server setup, show the exact command in full, mark it as running code, require explicit approval, and allow cancel. | Clients | MUST |
| 7.2 | Highlight risky commands, warn that servers run with the client's privileges, and launch servers in a sandbox with minimal default access. | Clients | SHOULD |
| 7.3 | Servers meant to run locally use STDIO, or restrict HTTP access with a token or a Unix socket. | Local servers | SHOULD |
| 7.4 | Proxies that spawn STDIO servers sandbox them, restrict file access, log every launch and require extra authorisation for dangerous commands. | Local proxies | SHOULD |

## 8. State handles

The 2026-07-28 revision removed protocol sessions. A server that needs state across requests mints its own handle (a cart ID, a workflow ID) and gets it back as a tool argument.

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 8.1 | Verify every inbound request. | Servers with authorisation | MUST |
| 8.2 | Never treat holding a handle as proof of identity. | Servers | MUST NOT |
| 8.3 | Generate handles from a secure random source, and let them expire. | Servers | SHOULD |
| 8.4 | Bind handles to the user from the verified token, for example by storing state under `<user_id>:<handle>`, and reject anyone else's use. | Servers | SHOULD |

## 9. Client ID Metadata Documents

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 9.1 | Show the redirect URI hostname clearly during authorisation. | AS | MUST |
| 9.2 | Warn when a client uses only `localhost` redirect URIs: CIMD proves control of a domain, not which local process is listening. | AS | SHOULD |
| 9.3 | Apply domain-based trust policies (allow-lists, reputation, domain age). | AS | MAY |

## 10. Streamable HTTP transport

From the [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) page.

| # | Requirement | Applies to | Level |
| --- | --- | --- | --- |
| 10.1 | Validate the `Origin` header on every connection, to stop DNS rebinding. If it is present and invalid, return 403. | Servers | MUST |
| 10.2 | When running locally, bind to 127.0.0.1, not 0.0.0.0. | Local HTTP servers | SHOULD |
| 10.3 | Authenticate every connection. | Servers | SHOULD |
| 10.4 | Reject requests whose `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` or `Mcp-Param-*` headers are missing or don't match the body: 400 with error `-32020` (`HeaderMismatch`). This stops a gateway routing on one value while the server acts on another. | Servers that read the body | MUST |
| 10.5 | Intermediaries that enforce policy on mirrored headers (routing or rate limiting by tenant, say) check the protocol version first, and reject requests too old to have had their headers validated. | Gateways | SHOULD |
| 10.6 | Ignore any `Mcp-Session-Id` header from older clients, and never mint or echo session IDs. | Servers on 2026-07-28 only | SHOULD |

## A note on RFC 8707

The spec says resource indicators bind tokens to their audience "when the Authorization Server supports the capability". If the AS ignores the parameter, the server's own audience check is what protects you. Don't describe sending `resource` alone as binding a token to a server.

## A note on mix-up attacks

PKCE does not stop a mix-up attack, because the client sends its verifier to whichever token endpoint it is tricked into using. The `iss` check (rows 2.5 to 2.8) does, but only when honest authorisation servers emit `iss`.

## Common scope mistakes

From the Best Practices page:

- listing every possible scope in `scopes_supported`;
- wildcard or catch-all scopes such as `*` or `full-access`;
- bundling unrelated privileges to avoid later prompts;
- returning the whole scope catalogue in every challenge;
- changing what a scope means without versioning it;
- trusting the scopes in a token without server-side authorisation logic.
