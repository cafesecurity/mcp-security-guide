# Checklist: 3. Build

*Generated from [03-build.md](../guide/03-build.md). Edit the page, not this file.*

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
