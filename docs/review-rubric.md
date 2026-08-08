# Pull request review rubric

Use this rubric to keep reviews consistent and focused on regressions that the
image test pipeline can detect. A pull request is ready to approve when every
applicable gate passes and all blocking findings are resolved.

## Review gates

### 1. Scope and execution model

- The change tests behavior provided by the shipped image, not behavior created
  by installing an extra dependency.
- Container-invisible claims about the kernel, graphical seat, disk layout,
  Secure Boot, TPM/LUKS, or A/B updates are left to the lab VM lanes.
- The diff is focused; unrelated scenarios, helpers, and generated files are
  not changed.

### 2. Scenario quality

- Feature language describes observable behavior rather than implementation
  details and makes a failed assertion diagnostically useful.
- Variant-specific behavior is gated explicitly and does not weaken assertions
  for other variants.
- Non-gating work is tagged `@wip`. Expected container failures are based on a
  clean observed boot, explain why they cannot pass, and are no broader than
  necessary.

### 3. Step and probe implementation

- Reusable vocabulary lives in `tests/shared/steps.py`, and reusable host probes
  live in `tests/shared/host.py`; suite-local steps are genuinely suite-specific.
- Probes run locally inside the image, use bounded timeouts, and preserve enough
  command output to explain failures.
- Assertions tolerate irrelevant output formatting differences without hiding
  meaningful failures.

### 4. Verification

- New or changed behavior has a focused scenario, including an important
  failure path when applicable.
- The affected suite was run against a suitable live snosi system or nested
  image with the repository's Behave 1.2.6 command, or the pull request clearly
  explains why runtime verification was unavailable.
- Required CI checks pass and the change does not reduce helper-code coverage
  beyond the configured gates.

### 5. Documentation and maintainability

- README, contributor, and agent guidance match any changed execution model or
  convention.
- The implementation is understandable without speculative allowlists,
  duplicated steps, or dependencies that the image does not ship.

## Finding labels

Prefix review comments with one of these labels:

- **Blocking:** correctness, regression coverage, execution-model, security, or
  required-documentation issue that must be fixed before approval.
- **Non-blocking:** worthwhile improvement that can follow separately.
- **Question:** context or clarification needed before deciding whether there
  is a defect.
- **Nit:** optional minor wording or style suggestion; do not repeat automated
  formatter or linter feedback.

A useful finding identifies the affected behavior, explains its impact, and
suggests a concrete resolution when possible. Re-check resolved blocking
findings and required CI before approving.
