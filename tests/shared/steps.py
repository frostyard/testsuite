"""Step definitions shared by every snosi suite.

Importing this module registers its steps with behave. Each suite pulls it in
from `features/steps/shared_steps.py` so the vocabulary stays identical across
suites — a scenario should read the same whether it lives in smoke or system.
"""

from __future__ import annotations

import os

from behave import given, then, when  # type: ignore[import-untyped]

from tests.shared import host


# ── running commands ──────────────────────────────────────────────────────────


@when('I run "{command}"')
@given('I run "{command}"')
def step_run(context, command):
    context.result = host.run(command)


@then("the command succeeds")
def step_command_succeeds(context):
    assert context.result.ok, (
        f"`{context.result.command}` exited {context.result.returncode}\n"
        f"{context.result.output}"
    )


@then("the command fails")
def step_command_fails(context):
    assert not context.result.ok, (
        f"`{context.result.command}` unexpectedly succeeded\n{context.result.output}"
    )


@then('the output contains "{needle}"')
def step_output_contains(context, needle):
    assert needle in context.result.output, (
        f"`{context.result.command}` output did not contain {needle!r}\n"
        f"{context.result.output}"
    )


@then('the output does not contain "{needle}"')
def step_output_excludes(context, needle):
    assert needle not in context.result.output, (
        f"`{context.result.command}` output unexpectedly contained {needle!r}\n"
        f"{context.result.output}"
    )


# ── binaries and files ────────────────────────────────────────────────────────


@then('"{binary}" is on PATH')
@given('"{binary}" is on PATH')
def step_binary_present(context, binary):
    assert host.have(binary), f"{binary} is not on PATH"


@then('"{path}" exists')
def step_path_exists(context, path):
    assert os.path.exists(path), f"{path} does not exist"


@then('"{path}" is a directory')
def step_path_is_dir(context, path):
    assert os.path.isdir(path), f"{path} is not a directory"


@then('"{path}" is a symlink to "{target}"')
def step_path_is_symlink(context, path, target):
    assert os.path.islink(path), f"{path} is not a symlink"
    actual = os.readlink(path)
    assert actual.rstrip("/") == target.rstrip("/"), (
        f"{path} points at {actual!r}, expected {target!r}"
    )


# ── systemd ───────────────────────────────────────────────────────────────────


@given("systemd has finished booting")
def step_systemd_booted(context):
    state = host.run("systemctl is-system-running").output
    # 'degraded' is the expected steady state in a container: units that need
    # real hardware or a graphical seat cannot start. The suites assert on
    # *which* units failed rather than on the aggregate state.
    assert state in {"running", "degraded", "starting"}, (
        f"systemd is in state {state!r}, which means the image did not boot"
    )


@then('the "{unit}" unit is active')
def step_unit_active(context, unit):
    state = host.run(f"systemctl is-active {unit}").output
    assert state == "active", f"{unit} is {state!r}, expected active"


@then('the "{unit}" unit is enabled')
def step_unit_enabled(context, unit):
    assert host.unit_is_enabled(unit), (
        f"{unit} is not enabled "
        f"(systemctl reports {host.run(f'systemctl is-enabled {unit}').output!r})"
    )


@then('the "{unit}" unit is not masked')
def step_unit_not_masked(context, unit):
    state = host.run(f"systemctl is-enabled {unit}").output
    assert state != "masked", f"{unit} is masked"


# ── variant gating ────────────────────────────────────────────────────────────


@given("the image ships a graphical session")
def step_require_graphical(context):
    if not host.is_graphical():
        context.scenario.skip(
            f"variant {host.VARIANT!r} is headless; graphical assertions do not apply"
        )
