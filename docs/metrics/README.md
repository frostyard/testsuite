# Public metrics

The testsuite publishes repository quality, runtime validation, and automation
signals from public, auditable sources. This page is the stable index for those
signals and defines the pull-request acceptance metric used by repository
tuning. It contains no secrets, private prompts, or telemetry from unpublished
images and environments.

## Signal index

| Signal | Public source | Interpretation |
| --- | --- | --- |
| Repository CI | [CI workflow runs](https://github.com/frostyard/testsuite/actions/workflows/ci.yml) | Per-commit repository policy and contract-test status. |
| Runtime validation | [frostyard/lab workflow runs](https://github.com/frostyard/lab/actions) | Behave results against published image digests; investigate failures using the pinned image and suite output. |
| Coverage | [Codecov dashboard](https://codecov.io/gh/frostyard/testsuite) | Project and patch coverage interpreted under [`codecov.yml`](../../codecov.yml). |
| Pull-request acceptance | [Merged pull requests](https://github.com/frostyard/testsuite/pulls?q=is%3Apr+is%3Amerged) and [closed, unmerged pull requests](https://github.com/frostyard/testsuite/pulls?q=is%3Apr+is%3Aclosed+-is%3Amerged) | Monthly ratio defined below; review with rejection reasons and feedback. |
| Open defects | [Open bug reports](https://github.com/frostyard/testsuite/issues?q=is%3Aissue+is%3Aopen+label%3Abug) | Regressions and test defects awaiting triage or correction. |
| AI review activity | [Claude review workflow runs](https://github.com/frostyard/testsuite/actions/workflows/claude-code-review.yml) | Advisory feedback on eligible same-repository pull requests; comments require human verification. |
| Quality-gate definitions | [Quality dashboard](../quality.md) | Canonical expectations, sources, and review cadence for each signal. |

These links expose source evidence rather than a copied snapshot that can go
stale. A failed or missing signal must be investigated at its source; it is not
silently converted into a passing value here.

## Pull-request acceptance

The pull-request acceptance rate measures how often resolved pull requests are
merged:

```text
accepted PRs / (accepted PRs + closed, unmerged PRs) × 100
```

An accepted PR is any pull request merged during the reporting period. A
rejected PR is a pull request closed without merging during that period. Open
pull requests are excluded.

Report the metric monthly using UTC calendar months and GitHub pull-request
data. Assign each pull request to the month in which it was merged or closed,
and report the month, accepted count, closed-unmerged count, and percentage so
changes in review volume remain visible. If neither category has an item in a
month, report `N/A` rather than zero.

Acceptance measures whether proposed changes reach the repository. Review it
alongside rejection reasons, superseded work, review feedback, CI outcomes, and
sample size; the percentage alone is not a quality score for human or automated
contributors.

## Publication and privacy contract

Only repository metadata and validation evidence already public through GitHub,
Codecov, or frostyard/lab belongs in this index. Do not publish credentials,
workflow secrets, private prompts, personal data, embargoed vulnerability
findings, unpublished image references, or private environment output. Model
comments and generated reports remain untrusted until reviewed. Public metrics
are audit evidence, not approval and not a substitute for repository CI,
runtime validation, or maintainer review.
