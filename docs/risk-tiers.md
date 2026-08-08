# Change risk tiers

Every pull request must identify the highest risk tier that applies to its
changes. The tier describes the potential impact of a mistake and determines
the review evidence expected before merge.

When a change matches more than one tier, use the highest one. If the impact is
unclear, choose the higher tier and explain the uncertainty in the pull
request. Reviewers may ask for a pull request to be reclassified.

## Tiers

| Tier | Typical changes | Potential impact |
| --- | --- | --- |
| **Low** | Prose-only documentation, comments, issue templates, or repository metadata that does not affect execution | Confusing guidance or incomplete project information |
| **Medium** | Feature specifications, suite-local steps, variant-specific behavior, or non-security CI behavior | Incorrect test results for a bounded suite or variant |
| **High** | Shared probes or steps, expected-failure allowlists, execution-model changes, dependencies, workflow triggers or permissions, and security-sensitive assertions | Regressions hidden across suites, untrusted code gaining privileges, or the validation pipeline becoming unreliable |

A large diff is not automatically high risk, and a small diff is not
automatically low risk. Classify the behavior that changes, not the number of
lines.

## Review requirements

All tiers require a linked issue or clear motivation, author self-review, and
passing repository CI.

| Tier | Additional evidence |
| --- | --- |
| **Low** | Confirm that links and instructions remain accurate. Documentation-only changes do not require runtime Behave output. |
| **Medium** | Provide focused test output for the affected suite or explain why a suitable image was unavailable. Review variant gates and failure diagnostics when applicable. |
| **High** | Provide focused runtime evidence, describe the failure and rollback paths, and obtain review from a maintainer familiar with the affected area. Explicitly examine permissions, trust boundaries, and whether the change could hide regressions. |

The tier supplements the [pull request review rubric](review-rubric.md); it does
not replace any applicable gate in that rubric.
