# Prompt: pre-release check

Run before a person tags a release. It produces a report and draft release notes. It must not tag, publish or push.

---

Prepare a release check for this MCP server. Do not tag, publish, push or change CI. Use the release checklist at https://github.com/cafesecurity/mcp-security-guide/blob/main/checklists/05-release.md and the change checklist at https://github.com/cafesecurity/mcp-security-guide/blob/main/checklists/07-change.md.

1. Find the last release tag and list the commits since.
2. Compare the tool-definition snapshot at the last tag with now. For every tool whose name, description, parameters, schema or annotations changed, quote old and new. List new and removed tools.
3. List changed scopes, upstream systems and dependencies (with old and new versions).
4. Run the full test suite, the dependency audit and the checklist build check, and report the results.
5. Check that the version was bumped appropriately for the changes in steps 2 and 3, and that `CHANGELOG.md` describes every client-visible change in words.
6. Check the release workflow: trusted publishing, a release environment with required approval, actions pinned to commit SHAs, no publishing tokens in secrets, no publish on pull requests.
7. Check that `THREATMODEL.md` was reviewed since any new tool or scope was added.

Write `RELEASE-CHECK.md` with:
- a table of each checklist item: done, not done, or needs a person to confirm (and why);
- draft release notes, including the tool-definition snapshot hash;
- a list of what a person must confirm before tagging.
