# Cross-session knowledge

This directory is the durable entry point for lessons that should survive
individual agent sessions. Project documentation remains the source of truth:

- [`README.md`](../README.md) defines the execution model and test conventions.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) defines the contribution workflow.
- [`docs/review-rubric.md`](../docs/review-rubric.md) defines review gates.
- [`docs/quality.md`](../docs/quality.md) indexes current quality signals.
- [`.claude/session-summary.md`](../.claude/session-summary.md) holds temporary
  handoffs for unfinished work.

## Recording knowledge

Promote a lesson here only when it is verified, reusable across future work,
and not already captured by an authoritative document. Prefer updating the
authoritative document when the lesson changes a project contract or
convention.

Store each lesson in a focused, kebab-case Markdown file with:

- the date and scope in which it was verified;
- the concise fact, correction, or decision future sessions must preserve;
- links to supporting issues, pull requests, commits, or documentation; and
- a superseding link when later evidence makes the lesson stale.

Do not record credentials, private data, raw logs, speculation, or temporary
task state. Use the session summary for temporary handoffs and remove those
handoffs after the knowledge is completed or promoted.
