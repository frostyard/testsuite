<!-- Branch from the latest main. Reviews apply AGENTS.md,
docs/review-rubric.md and the docs rules in docs/README.md. -->

## Summary

<!-- What does this change do, and why? Which scenarios, steps, probes or
workflows does it affect? -->

## Related issue

- Closes #

## Risk tier

Declare the highest applicable tier, never lower; the scale is
[docs/risk-tiers.md](https://github.com/frostyard/testsuite/blob/main/docs/risk-tiers.md) (Low, Medium, High). A `risk:high`
label (a path in `.github/risk-paths.json` at level L1 or L2) means High: name
each matched path and why the change is safe, and give the rollback or
safe-disable step. The caller of core's `pr-triage` workflow also adds 1 level
label, `level:L1` to `level:L4`, and removes `ready-for-human` when the head
commit moves.

- Tier: Low / Medium / High
- Rationale:

## Validation

<!-- List the commands you actually ran and their outcome. -->

- [ ] `make verify` passes (template gate, repository policy, policy unittests, pytest, feature discovery)
- [ ] For a scenario, step or probe change: `PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip` against a live snosi machine or a nested image, or the reason it could not run
- [ ] Revert test for a fix: the new test fails with the fix reverted; command: <!-- name it -->
- [ ] Workflows changed: every action is SHA-pinned with a version comment, read-only top-level `permissions`, and `persist-credentials: false`
- [ ] Not run (explain why)

## Docs housekeeping

<!-- Delete rows that do not apply. -->

- [ ] Documentation updated (`AGENTS.md`, `README.md`, `docs/`) where relevant
- [ ] New docs started from their category's `TEMPLATE.md` and indexed in `docs/README.md`
- [ ] Cross-links added in both directions (ADR ↔ design ↔ spec ↔ plan)
- [ ] New significant decision recorded as an ADR first, in this PR

## Checklist

- [ ] No secrets, tokens or credentials are committed
- [ ] I have checked this change against the [PR review rubric](https://github.com/frostyard/testsuite/blob/main/docs/review-rubric.md)
- [ ] Blocking review point fixed: guard added and 1 file added under `.memory/corrections/`
