# Documentation

Docs are split by the question they answer
(core [ADR-0025](https://github.com/frostyard/core/blob/main/docs/adr/0025-consolidate-repository-docs-into-docs.md)):

| Directory | Question | Contents |
| --- | --- | --- |
| [adr/](adr/) | **Why** did we choose this? | Architecture Decision Records — immutable once accepted; superseded, never edited. Repo-local only: org-wide decisions live in [frostyard/core](https://github.com/frostyard/core/tree/main/docs/adr) (see [org-adrs.md](org-adrs.md)) |
| [design/](design/) | **How** does it fit together? | Living documents describing the current architecture |
| [specs/](specs/) | **What exactly** is the contract? | Precise, testable interface definitions |
| [plans/](plans/) | **When/in what order** do we build? | Open work only; updated as work lands |

## Index

### Decisions (ADRs)

*(none yet)*

### Org-wide decisions

- [org-adrs.md](org-adrs.md) — the frostyard/core ADRs that bind this repository

### Design

- [execution-model.md](design/execution-model.md) — how the suites run inside
  the image under test, the layout, the `podman` run the lab uses, the
  environment and the test conventions

### Specs

*(none yet)*

### Plans

*(none yet)*

### Uncategorized (indexed where they stand)

- [authoring-scenarios.md](authoring-scenarios.md) — a copyable scenario from
  Gherkin to its step implementation and runtime validation
- [quality.md](quality.md) — quality signals, coverage, and known gaps
- [review-rubric.md](review-rubric.md) — what review checks, by risk tier
- [risk-tiers.md](risk-tiers.md) — change risk tiers used by review and CI
- [SECURITY-AI.md](SECURITY-AI.md) — security posture for AI automation
- [ai-fix-workflow.md](ai-fix-workflow.md) — the AI fix-request workflow
- [metrics/README.md](metrics/README.md) — the public metrics index and PR
  acceptance definition

## Conventions

- **New docs start from their category's `TEMPLATE.md`** (in each directory).
- New decision → new ADR with the next number; if it reverses an old one, mark
  the old one `Superseded by NNNN` rather than editing it. Repo-local decisions
  only: org-wide decisions get an ADR in frostyard/core plus a line in
  [org-adrs.md](org-adrs.md).
- Design docs are updated in place to always reflect reality.
- Specs change only alongside the code that implements them.
- Cross-links between categories are mandatory in both directions — see the
  documentation rules in [AGENTS.md](../AGENTS.md) (`CLAUDE.md`, `GEMINI.md`,
  `.cursorrules` and `.github/copilot-instructions.md` are symlinks to it,
  ADR-0029).
- `docs/plans/` holds only open work: a plan for finished work is removed once
  its record is in `quality.md` or an ADR, and git keeps it.
- Adding a doc means adding it to the index above.
