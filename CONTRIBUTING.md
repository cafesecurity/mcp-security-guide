# Contributing

Corrections and additions are welcome. Three rules keep the guide trustworthy:

1. **Every factual claim needs a source.** Add or update its row in [reference/sources.md](reference/sources.md), with the date you checked it. Prefer the primary source: the specification, the vendor's advisory, the researchers' own write-up. A search-result snippet is not a source.
2. **Say what kind of case it is.** A breach, a disclosed vulnerability and a research demonstration are different things. Mark demonstrations as demonstrations.
3. **No attribution without strong sourcing.** Don't name a group or country as responsible for an attack unless the primary source does.

## Style

- British English. Short sentences, plain words.
- Dates in full (13 November 2026). Product names exactly as their makers write them.
- Each guide page keeps the same five parts: what to do, what goes wrong, controls, "If a coding agent is doing this", checklist.

## How to propose a change

- **A correction:** open an issue with the "Correction" template, or a pull request that changes the text and the sources row together.
- **A missing control or case:** use the "Missing control" template.
- **A change to `AGENTS.md`:** say which guide page the rule comes from. Every rule there should trace to a page.

## Checks

Run these before a pull request; CI runs them too.

```bash
python3 scripts/check_links.py         # relative links and #anchors resolve
python3 scripts/build_checklists.py    # regenerate checklists/ from the guide pages
python3 scripts/check_skills.py        # SKILL.md format
python3 -m unittest discover -s skills/tests && python3 -m unittest discover -s tests
```

`bin/mcp-guide` stays a single standard-library file with no network access of its own (the audit scripts it runs fetch packages). It must never pull, update itself, or overwrite a file the user changed without `--force`. Security rules for changes to it and the audit scripts:

- Default to the safe choice. Anything that runs or contacts someone else's code is a named entry in `RISKS`, off unless accepted, and recorded in the audit's summary. Don't add a blanket "yes to everything" flag.
- Treat the repository it runs in as possibly hostile: validate the manifest, and never write, delete or follow a link outside the repository.
- Treat everything from a package or server as untrusted text: pass it through `clean()` before it reaches a terminal or a report an agent will read.
- Every such rule has a test in `tests/` or `skills/tests/`. Add one with any change.
- The Claude Code guardrail rules can't be tested in CI (they need a signed-in Claude Code). After changing `GUARDRAILS`, run `python3 scripts/check_guardrails_live.py` on your own machine and paste its table into the pull request.

Checklists are generated from the `## Checklist` section of each guide page. Edit the page, not `checklists/`.

External links aren't checked automatically. Before each release, open every link in `reference/sources.md` and update its "Checked" date.

## The example server

Changes to `examples/ask-trevor/` need passing tests (`npm ci && npm test && npm run snapshot:check`). A change to a tool's definition also needs a version bump and an entry in its `CHANGELOG.md`. Don't add write tools; the example is deliberately read-only.
