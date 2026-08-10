from unittest.mock import Mock

import pytest

from tests.shared import steps as shared_steps
from tests.smoke.features import environment
from tests.smoke.features.steps import smoke_steps


def test_step_run_stores_command_result(monkeypatch, context, make_result):
    result = make_result(command="rpm --version")
    run = Mock(return_value=result)
    monkeypatch.setattr(shared_steps.host, "run", run)

    shared_steps.step_run(context, "rpm --version")

    assert context.result is result
    run.assert_called_once_with("rpm --version")


def test_command_status_steps_accept_expected_results(context, make_result):
    context.result = make_result(returncode=0)
    shared_steps.step_command_succeeds(context)

    context.result = make_result(returncode=1)
    shared_steps.step_command_fails(context)


def test_command_status_steps_report_unexpected_results(context, make_result):
    context.result = make_result(
        command="broken",
        returncode=9,
        stdout="failure details",
    )
    with pytest.raises(AssertionError) as succeeds_error:
        shared_steps.step_command_succeeds(context)
    assert "`broken` exited 9" in str(succeeds_error.value)
    assert "failure details" in str(succeeds_error.value)

    context.result = make_result(command="working", stdout="success details")
    with pytest.raises(AssertionError) as fails_error:
        shared_steps.step_command_fails(context)
    assert "`working` unexpectedly succeeded" in str(fails_error.value)
    assert "success details" in str(fails_error.value)


def test_output_steps_accept_expected_content(context, make_result):
    context.result = make_result(stdout="the expected value")

    shared_steps.step_output_contains(context, "expected")
    shared_steps.step_output_excludes(context, "missing")


def test_output_steps_report_unexpected_content(context, make_result):
    context.result = make_result(command="probe", stdout="actual output")

    with pytest.raises(AssertionError) as contains_error:
        shared_steps.step_output_contains(context, "expected")
    assert "did not contain 'expected'" in str(contains_error.value)
    assert "actual output" in str(contains_error.value)

    with pytest.raises(AssertionError) as excludes_error:
        shared_steps.step_output_excludes(context, "actual")
    assert "unexpectedly contained 'actual'" in str(excludes_error.value)


def test_binary_present_checks_path(monkeypatch, context):
    have = Mock(return_value=True)
    monkeypatch.setattr(shared_steps.host, "have", have)

    shared_steps.step_binary_present(context, "bootc")

    have.assert_called_once_with("bootc")


def test_binary_present_reports_missing_binary(monkeypatch, context):
    monkeypatch.setattr(shared_steps.host, "have", Mock(return_value=False))

    with pytest.raises(AssertionError, match="bootc is not on PATH"):
        shared_steps.step_binary_present(context, "bootc")


@pytest.mark.parametrize(
    ("step", "probe_name", "failure"),
    [
        (shared_steps.step_path_exists, "exists", "/path does not exist"),
        (shared_steps.step_path_is_dir, "isdir", "/path is not a directory"),
    ],
)
def test_path_steps_check_expected_file_type(monkeypatch, context, step, probe_name, failure):
    probe = Mock(return_value=True)
    monkeypatch.setattr(shared_steps.os.path, probe_name, probe)
    step(context, "/path")
    probe.assert_called_once_with("/path")

    probe.return_value = False
    with pytest.raises(AssertionError, match=failure):
        step(context, "/path")


def test_symlink_step_accepts_equivalent_trailing_slashes(monkeypatch, context):
    monkeypatch.setattr(shared_steps.os.path, "islink", Mock(return_value=True))
    readlink = Mock(return_value="/target/")
    monkeypatch.setattr(shared_steps.os, "readlink", readlink)

    shared_steps.step_path_is_symlink(context, "/link", "/target")

    readlink.assert_called_once_with("/link")


def test_symlink_step_reports_missing_or_wrong_link(monkeypatch, context):
    islink = Mock(return_value=False)
    readlink = Mock(return_value="/actual")
    monkeypatch.setattr(shared_steps.os.path, "islink", islink)
    monkeypatch.setattr(shared_steps.os, "readlink", readlink)

    with pytest.raises(AssertionError, match="/link is not a symlink"):
        shared_steps.step_path_is_symlink(context, "/link", "/expected")
    readlink.assert_not_called()

    islink.return_value = True
    with pytest.raises(AssertionError) as error:
        shared_steps.step_path_is_symlink(context, "/link", "/expected")
    assert "/link points at '/actual', expected '/expected'" in str(error.value)


@pytest.mark.parametrize("state", ["running", "degraded", "starting"])
def test_systemd_booted_accepts_operational_states(monkeypatch, context, make_result, state):
    monkeypatch.setattr(
        shared_steps.host,
        "run",
        Mock(return_value=make_result(stdout=f"{state}\n")),
    )

    shared_steps.step_systemd_booted(context)


def test_systemd_booted_reports_failed_state(monkeypatch, context, make_result):
    monkeypatch.setattr(
        shared_steps.host,
        "run",
        Mock(return_value=make_result(stdout="maintenance\n")),
    )

    with pytest.raises(AssertionError, match="systemd is in state 'maintenance'"):
        shared_steps.step_systemd_booted(context)


def test_unit_active_requires_active_state(monkeypatch, context, make_result):
    run = Mock(return_value=make_result(stdout="active\n"))
    monkeypatch.setattr(shared_steps.host, "run", run)
    shared_steps.step_unit_active(context, "dbus.service")
    run.assert_called_once_with("systemctl is-active dbus.service")

    run.return_value = make_result(stdout="failed\n")
    with pytest.raises(AssertionError, match="dbus.service is 'failed', expected active"):
        shared_steps.step_unit_active(context, "dbus.service")


def test_unit_enabled_accepts_enabled_unit_without_diagnostic_probe(monkeypatch, context):
    monkeypatch.setattr(shared_steps.host, "unit_is_enabled", Mock(return_value=True))
    run = Mock()
    monkeypatch.setattr(shared_steps.host, "run", run)

    shared_steps.step_unit_enabled(context, "dbus.service")

    run.assert_not_called()


def test_unit_enabled_reports_systemctl_state(monkeypatch, context, make_result):
    monkeypatch.setattr(shared_steps.host, "unit_is_enabled", Mock(return_value=False))
    run = Mock(return_value=make_result(stdout="disabled\n"))
    monkeypatch.setattr(shared_steps.host, "run", run)

    with pytest.raises(AssertionError) as error:
        shared_steps.step_unit_enabled(context, "dbus.service")

    assert "dbus.service is not enabled" in str(error.value)
    assert "systemctl reports 'disabled'" in str(error.value)
    run.assert_called_once_with("systemctl is-enabled dbus.service")


def test_unit_not_masked_rejects_masked_unit(monkeypatch, context, make_result):
    run = Mock(return_value=make_result(stdout="enabled\n"))
    monkeypatch.setattr(shared_steps.host, "run", run)
    shared_steps.step_unit_not_masked(context, "dbus.service")

    run.return_value = make_result(stdout="masked\n")
    with pytest.raises(AssertionError, match="dbus.service is masked"):
        shared_steps.step_unit_not_masked(context, "dbus.service")


def test_graphical_requirement_allows_graphical_variant(monkeypatch, context):
    monkeypatch.setattr(shared_steps.host, "is_graphical", Mock(return_value=True))

    shared_steps.step_require_graphical(context)

    context.scenario.skip.assert_not_called()


def test_graphical_requirement_skips_headless_variant(monkeypatch, context):
    monkeypatch.setattr(shared_steps.host, "is_graphical", Mock(return_value=False))
    monkeypatch.setattr(shared_steps.host, "VARIANT", "cayo")

    shared_steps.step_require_graphical(context)

    context.scenario.skip.assert_called_once_with(
        "variant 'cayo' is headless; graphical assertions do not apply"
    )


def test_no_unexpected_failures_accepts_allowlisted_units(monkeypatch, context):
    known = next(iter(smoke_steps.EXPECTED_CONTAINER_FAILURES))
    monkeypatch.setattr(smoke_steps.host, "failed_units", Mock(return_value=[known]))

    smoke_steps.step_no_unexpected_failures(context)


def test_no_unexpected_failures_reports_new_and_tolerated_units(monkeypatch, context):
    known = next(iter(smoke_steps.EXPECTED_CONTAINER_FAILURES))
    monkeypatch.setattr(
        smoke_steps.host,
        "failed_units",
        Mock(return_value=["zeta.service", known, "alpha.service"]),
    )

    with pytest.raises(AssertionError) as error:
        smoke_steps.step_no_unexpected_failures(context)

    message = str(error.value)
    assert "Unexpected failed units:\n  alpha.service\n  zeta.service" in message
    assert f"Tolerated (known container limitations):\n  {known}" in message


def test_os_release_equals_accepts_matching_value(monkeypatch, context):
    monkeypatch.setattr(
        smoke_steps.host,
        "os_release",
        Mock(return_value={"IMAGE_ID": "snow"}),
    )

    smoke_steps.step_os_release_equals(context, "IMAGE_ID", "snow")


def test_os_release_equals_reports_missing_or_different_value(monkeypatch, context):
    release = Mock(return_value={"NAME": "Snosi"})
    monkeypatch.setattr(smoke_steps.host, "os_release", release)

    with pytest.raises(AssertionError, match="/etc/os-release has no IMAGE_ID"):
        smoke_steps.step_os_release_equals(context, "IMAGE_ID", "snow")

    release.return_value = {"IMAGE_ID": "cayo"}
    with pytest.raises(AssertionError) as error:
        smoke_steps.step_os_release_equals(context, "IMAGE_ID", "snow")
    assert "os-release IMAGE_ID is 'cayo', expected 'snow'" in str(error.value)


@pytest.mark.parametrize("value", ["snow", "0"])
def test_os_release_set_accepts_nonempty_value(monkeypatch, context, value):
    monkeypatch.setattr(
        smoke_steps.host,
        "os_release",
        Mock(return_value={"IMAGE_VERSION": value}),
    )

    smoke_steps.step_os_release_set(context, "IMAGE_VERSION")


@pytest.mark.parametrize("release", [{}, {"IMAGE_VERSION": ""}])
def test_os_release_set_reports_missing_or_empty_value(monkeypatch, context, release):
    monkeypatch.setattr(smoke_steps.host, "os_release", Mock(return_value=release))

    with pytest.raises(AssertionError, match="IMAGE_VERSION is missing or empty"):
        smoke_steps.step_os_release_set(context, "IMAGE_VERSION")


def test_default_target_requires_expected_target(monkeypatch, context, make_result):
    run = Mock(return_value=make_result(stdout="graphical.target\n"))
    monkeypatch.setattr(smoke_steps.host, "run", run)
    smoke_steps.step_default_target(context, "graphical.target")
    run.assert_called_once_with("systemctl get-default")

    run.return_value = make_result(stdout="multi-user.target\n")
    with pytest.raises(AssertionError) as error:
        smoke_steps.step_default_target(context, "graphical.target")
    assert "default target is 'multi-user.target', expected 'graphical.target'" in str(error.value)


def test_before_all_records_and_prints_image_identity(monkeypatch, context, capsys):
    monkeypatch.setattr(environment.host, "VARIANT", "snow")
    monkeypatch.setattr(environment.host, "IMAGE", "ghcr.io/frostyard/snow@sha256:123")
    monkeypatch.setattr(
        environment.host,
        "os_release",
        Mock(
            return_value={
                "PRETTY_NAME": "Snosi Snow",
                "IMAGE_ID": "snow",
                "IMAGE_VERSION": "2026.08",
            }
        ),
    )

    environment.before_all(context)

    assert context.variant == "snow"
    assert context.image == "ghcr.io/frostyard/snow@sha256:123"
    output = capsys.readouterr().out
    assert "variant=snow image=ghcr.io/frostyard/snow@sha256:123" in output
    assert "Snosi Snow" in output
    assert "IMAGE_ID=snow IMAGE_VERSION=2026.08" in output


def test_before_all_prints_placeholders_for_missing_release_fields(
    monkeypatch,
    context,
    capsys,
):
    monkeypatch.setattr(environment.host, "os_release", Mock(return_value={}))

    environment.before_all(context)

    output = capsys.readouterr().out
    assert "<no PRETTY_NAME>" in output
    assert "IMAGE_ID=<unset> IMAGE_VERSION=<unset>" in output
