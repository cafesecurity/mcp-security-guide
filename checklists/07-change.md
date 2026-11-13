# Checklist: 7. Change

*Generated from [07-change.md](../guide/07-change.md). Edit the page, not this file.*

- [ ] The change-classification table (or your version of it) is in the contribution guide.
- [ ] The snapshot test fails the build on any change to tool names, descriptions, schemas or annotations.
- [ ] Every client-visible change bumps the version and is described in words in the release notes.
- [ ] New tools, new scopes and new upstream access update the threat model and need a person's approval.
- [ ] The server sends `notifications/tools/list_changed` when its tools change.
- [ ] The tool-definition hash is published with each release.
- [ ] Dependency upgrades are read by a person before they reach production.
- [ ] The server is migrated to the 2026-07-28 spec, or has a dated plan to be.
