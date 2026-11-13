# Checklist: 0. Decide

*Generated from [00-decide.md](../guide/00-decide.md). Edit the page, not this file.*

- [ ] There is a written reason why this is an MCP server rather than an API, a library or the vendor's own server.
- [ ] The brief states where it runs (local or remote), who calls it (staff or customers), what it reads, what it changes, and what it must never do.
- [ ] It has a named owner and an entry in the inventory.
- [ ] Every action (write, send, pay, delete) is listed and justified on its own; the default is read-only.
- [ ] The systems and data behind it are named, with whose credentials it will reach them.
- [ ] The brief is committed as the first section of `THREATMODEL.md`.
