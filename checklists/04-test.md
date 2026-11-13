# Checklist: 4. Test

*Generated from [04-test.md](../guide/04-test.md). Edit the page, not this file.*

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
