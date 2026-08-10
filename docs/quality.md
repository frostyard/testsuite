# Quality dashboard

This page is the entry point for the testsuite's quality signals. It links to
live sources rather than copying point-in-time values that quickly become
stale.

[![CI status](https://github.com/frostyard/testsuite/actions/workflows/ci.yml/badge.svg)](https://github.com/frostyard/testsuite/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/frostyard/testsuite/branch/main/graph/badge.svg)](https://codecov.io/gh/frostyard/testsuite)

## Signals

| Signal | Quality expectation | Live source |
| --- | --- | --- |
| Repository CI | The latest `main` run and every pull request pass. | [CI workflow runs](https://github.com/frostyard/testsuite/actions/workflows/ci.yml) |
| Repository policy | Required governance, CI, documentation, and test assets satisfy the versioned policy on every pull request. | [`policies/repository.json`](../policies/repository.json) |
| Nightly compliance | Repository policy, Ruff correctness checks, Python compilation, feature discovery, and CodeQL pass each night; scheduled failures are tracked as bug issues. | [Nightly workflow runs](https://github.com/frostyard/testsuite/actions/workflows/nightly-compliance.yml) |
| Runtime suites | Behave suites pass against published images; failures are investigated in the lab that exercised the image. | [frostyard/lab workflow runs](https://github.com/frostyard/lab/actions) |
| Coverage | Project coverage does not fall by more than 2%; changed Python code reaches 80%. | [Codecov dashboard](https://codecov.io/gh/frostyard/testsuite) and [gate configuration](../codecov.yml) |
| Pull request acceptance | Accepted and closed-unmerged pull requests are reported monthly with their counts and acceptance percentage. | [Metric definition](metrics.md), [merged PRs](https://github.com/frostyard/testsuite/pulls?q=is%3Apr+is%3Amerged), and [closed, unmerged PRs](https://github.com/frostyard/testsuite/pulls?q=is%3Apr+is%3Aclosed+-is%3Amerged) |
| Open defects | Regressions and test defects are triaged rather than hidden by broad allowlists. | [Open bug reports](https://github.com/frostyard/testsuite/issues?q=is%3Aissue+is%3Aopen+label%3Abug) |

## Reading the dashboard

A red repository CI run blocks its commit or pull request. A runtime-suite
failure may indicate either a testsuite regression or a defect in the image
under test; use the failing lab run's pinned image reference and Behave output
to distinguish them. Coverage status follows `codecov.yml`, which is the source
of truth for thresholds.

Reviewers should apply the [pull request review rubric](review-rubric.md) before
approval. Non-gating scenarios must carry `@wip`, and expected nested-container
failures must remain narrowly scoped and documented. These exceptions are
visible in test output and are not equivalent to passing coverage.

## Review cadence

- **Per pull request:** inspect repository CI, affected runtime-suite evidence,
  and patch coverage.
- **After each published image:** inspect the corresponding lab run and triage
  unexpected Behave failures.
- **Monthly:** report pull request acceptance using the UTC-period definition in
  [project metrics](metrics.md), and review open defects and stale `@wip`
  scenarios.
