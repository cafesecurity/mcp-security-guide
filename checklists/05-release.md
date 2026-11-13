# Checklist: 5. Release

*Generated from [05-release.md](../guide/05-release.md). Edit the page, not this file.*

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
