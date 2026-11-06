# Agent instructions

This file is the canonical instruction file. `CLAUDE.md`, `GEMINI.md`,
`.cursorrules` and `.github/copilot-instructions.md` are symlinks to it, and
`.claude/skills` links to `.agents/skills/` (core ADR-0018, ADR-0029).

- Keep changes focused and reviewable; do not modify unrelated scenarios or helper code.
- Tests run inside the image under test. Assert only on what the shipped image provides, and do not add dependencies that must be installed for a scenario to pass.
- Put shared step vocabulary in `tests/shared/steps.py` and probe helpers in `tests/shared/host.py` when adding or updating scenarios.
- Tag scenarios that should not gate the pipeline with `@wip`; the lab excludes those by default.
- Validate test changes with `PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip` when a live snosi machine or suitable container is available, and with `make verify` before you open a pull request.
- Record unfinished-work handoffs in `.claude/session-summary.md`; keep entries concise and remove them when the follow-up is complete.

## Gate and guards

- `make verify` is the gate: the template gate and its Node tests
  (`verify-template`), then the repository policy check, the policy unittests,
  the pytest suite of `tests/unit` and the behave feature-discovery check
  (`verify-python`). `make check` is the same thing, for developers. `make ci`
  is `verify` plus the append-only corrections check against `BASE`
  (`make ci BASE=origin/main`).
- behave and pytest come from the distribution packages `python3-behave` and
  `python3-pytest`; mise pins only Node. No Python comes from pip.
- A blocking review point adds a guard in the pull request that fixes it: a
  test that fails without the fix, or a rule here when no test can catch it,
  plus 1 line in `.memory/corrections.jsonl` (ADR-0018; `make verify` validates
  it).
- A path in `.github/risk-paths.json` gives the pull request the `risk:high`
  label. Do not remove that label to make a pull request ready: the change
  leaves the pull request, with the reason in it.

## Docs

- Docs live in `docs/`, in its 4 categories (ADR-0025): `adr/`, `design/`,
  `specs/` and `plans/`. Each new doc starts from its category's `TEMPLATE.md`
  and is indexed in `docs/README.md`; `make verify` fails on an unindexed doc.
- The root `README.md` follows core's README standard (ADR-0072): it declares
  the kind `infrastructure`. Check a change to it with core's
  `check-readme.mjs` from the `frostyard-readme` skill.
- `docs/plans/` holds only open work. A plan for finished work is removed once
  its record is in `docs/quality.md` or an ADR.
