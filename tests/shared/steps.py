"""Step definitions shared by every snosi suite.

Importing this module registers its steps with behave. Each suite pulls it in
from `features/steps/shared_steps.py` so the vocabulary stays identical across
suites — a scenario should read the same whether it lives in smoke or system.
"""

from __future__ import annotations

import os
import stat

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


@then('"{binary}" is not on PATH')
def step_binary_absent(context, binary):
    assert not host.have(binary), f"{binary} is unexpectedly on PATH"


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


@then('"{path}" does not exist')
def step_path_missing(context, path):
    # lexists, not exists: a dangling symlink is leftover packaging too, and the
    # scenario asserts the path is gone in every form.
    dangling = " (dangling symlink)" if os.path.islink(path) else ""
    assert not os.path.lexists(path), f"{path} exists{dangling}"


@then('"{path}" is an executable file for every user')
def step_path_is_executable_for_all(context, path):
    if host.is_executable_by_all(path):
        return
    try:
        mode = os.stat(path).st_mode
    except OSError as error:
        raise AssertionError(
            f"{path} is not an executable file for every user ({error.strerror})"
        ) from None
    kind = "a regular file" if stat.S_ISREG(mode) else "not a regular file"
    raise AssertionError(
        f"{path} is not an executable file for every user "
        f"(mode {stat.S_IMODE(mode):04o}, {kind})"
    )


# ── first-login autostart ─────────────────────────────────────────────────────


@then('the desktop entry "{path}" sets "{key}" to "{value}"')
def step_desktop_entry_sets(context, path, key, value):
    assert os.path.isfile(path), f"desktop entry {path} does not exist"
    entry = host.desktop_entry(path)
    actual = entry.get(key)
    assert actual == value, (
        f"desktop entry {path} sets {key} to {actual!r}, expected {value!r} "
        f"(keys: {sorted(entry)})"
    )


@then('the desktop entry "{path}" starts in a GNOME session')
def step_desktop_entry_starts_on_gnome(context, path):
    assert os.path.isfile(path), f"desktop entry {path} does not exist"
    entry = host.desktop_entry(path)
    assert host.starts_on_gnome(entry), (
        f"desktop entry {path} would not be started by GNOME "
        f"(Type={entry.get('Type')!r}, Hidden={entry.get('Hidden')!r}, "
        f"X-GNOME-Autostart-enabled={entry.get('X-GNOME-Autostart-enabled')!r}, "
        f"OnlyShowIn={entry.get('OnlyShowIn')!r}, NotShowIn={entry.get('NotShowIn')!r})"
    )
    extra = sorted(
        key
        for key in entry
        if key not in host.CANONICAL_KEYS and not key.startswith(host.CANONICAL_LOCALIZED)
    )
    assert not extra, (
        f"desktop entry {path} carries keys the guard does not validate: "
        f"{', '.join(extra)} (they can stop GNOME from starting it)"
    )
    terminal = entry.get("Terminal", "false")
    assert terminal == "false", (
        f"desktop entry {path} must not set Terminal={terminal}"
    )


@then('the only first-login autostart entry is "{path}"')
def step_only_first_login_entry(context, path):
    found = host.first_login_entries()
    assert found == [path], (
        f"expected the only first-login autostart entry to be {path}, "
        f"found: {', '.join(found) or '(none)'}"
    )


@then("no first-login autostart entry exists")
def step_no_first_login_entry(context):
    found = host.first_login_entries()
    assert not found, (
        "unexpected first-login autostart entries:\n  " + "\n  ".join(found)
    )


@then('no "{name}" autostart entry exists')
def step_no_named_autostart_entry(context, name):
    found = [
        path
        for path in host.autostart_entries()
        if os.path.basename(path).startswith(name)
    ]
    assert not found, (
        f"unexpected {name} autostart entries:\n  " + "\n  ".join(found)
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


@given("the image ships no graphical session")
def step_require_headless(context):
    if host.is_graphical():
        context.scenario.skip(
            f"variant {host.VARIANT!r} ships a graphical session; "
            f"headless assertions do not apply"
        )


@given('the image ships the "{desktop}" desktop')
def step_require_desktop(context, desktop):
    shipped = host.desktop()
    if shipped != desktop:
        context.scenario.skip(
            f"variant {host.VARIANT!r} ships {shipped or 'no'} desktop; "
            f"{desktop} assertions do not apply"
        )
