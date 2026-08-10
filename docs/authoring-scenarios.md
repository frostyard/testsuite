# Authoring a testsuite scenario

This guide follows one minimal scenario from Gherkin to its Python step
implementation and runtime validation. Read the [execution
model](../README.md#the-execution-model) first: these suites run inside the
image under test, not against it over SSH.

## 1. Choose the suite

Add scenarios for the currently implemented suite under
`tests/smoke/features/`. The lab also reserves two suite names for contracts
that do not belong in `smoke`:

- `smoke` for basic boot, identity, and shipped-tool checks;
- `system` for bootc and composefs behavior visible from the running image;
- `sysext` for systemd-sysext and updex behavior.

Only `smoke` is populated today. If a new scenario establishes one of the
reserved contracts, create `tests/system/features/` or
`tests/sysext/features/` as appropriate; the Lab pipeline already accepts both
names, so there is no separate registry to edit. Do not put Behave scenarios in
`tests/e2e/`: that directory is only an ACMM discovery marker, and `e2e` is not
a Lab suite name.

## 2. Write the feature

For example, the first feature in the reserved `system` suite could reuse the
shared command vocabulary to check the image's shipped Debian tooling:

```gherkin
# tests/system/features/package_tooling.feature
@system
Feature: The base package database is readable
  The installed package database must remain usable by image-local tools.

  Scenario: dpkg can report its version
    When I run "dpkg --version"
    Then the command succeeds
    And the output contains "Debian"
```

Keep feature text about observable behavior rather than Python implementation.
The `@system` tag is descriptive; Lab selects the `system` suite by directory,
not by this tag.

## 3. Register the shared steps

Each suite imports the common vocabulary through a small Behave discovery
module. When creating a suite's first feature, add:

```python
# tests/system/features/steps/shared_steps.py
"""Register the step vocabulary shared by every suite."""

from tests.shared import steps  # noqa: F401
```

Importing `tests.shared.steps` registers its decorated functions with Behave.
`PYTHONPATH=.` in the validation command makes the repository-level `tests`
package importable. A suite only needs an `environment.py` when it has Behave
hooks or suite-wide setup; do not add an empty one.

The two steps used by the example are implemented in
`tests/shared/steps.py`. In simplified form, their implementation is:

```python
from behave import then, when

from tests.shared import host


@when('I run "{command}"')
def step_run(context, command):
    context.result = host.run(command)


@then("the command succeeds")
def step_command_succeeds(context):
    assert context.result.ok, (
        f"`{context.result.command}` exited {context.result.returncode}\n"
        f"{context.result.output}"
    )
```

Use existing phrases before adding another definition. Put vocabulary that
makes sense in more than one suite in `tests/shared/steps.py`, and put reusable
probe logic in `tests/shared/host.py`. A genuinely suite-specific definition
belongs in another module under `tests/<suite>/features/steps/`; Behave
automatically discovers every Python module there. Import `host` rather than
open-coding subprocess handling, and store intermediate results on `context`
when later steps consume them.

Never add a package installation to make a scenario pass. Other than the
harness's `python3-behave` installation, the test must use only what the image
already ships.

## 4. Tag deliberately

An untagged scenario, or one carrying only descriptive tags such as `@system`,
gates the Lab run. Add `@wip` only while a scenario is intentionally
non-gating:

```gherkin
@wip
Scenario: A contract that is not ready to gate
  ...
```

Lab invokes Behave with `--tags ~@wip`, so it will not execute that scenario.
Do not use `@wip` to hide a regression in an established test. Behave is pinned
to 1.2.6; its tag negation syntax is `~@wip`, not `not @wip`.

## 5. Validate before Lab picks it up

A dry run catches undefined or ambiguous steps without executing the probe:

```bash
PYTHONPATH=. python3 -m behave \
  tests/system/features/package_tooling.feature --dry-run
```

That is only a fast authoring check. Before requesting review or enabling the
scenario as a gate, run the complete affected suite on a live snosi machine:

```bash
PYTHONPATH=. python3 -m behave \
  tests/system/features/ --no-capture --tags ~@wip
```

Use Debian trixie's `python3-behave` package (Behave 1.2.6). If a live machine
is unavailable, use the repository's [Lab-equivalent container
invocation](../README.md#running-it), replacing `smoke` with the affected suite,
and state exactly what could not be validated in the pull request. Include the
passing Behave output with the change; repository CI does not replace this
image-runtime validation.
