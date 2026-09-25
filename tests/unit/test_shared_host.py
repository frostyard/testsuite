import subprocess
from unittest.mock import Mock, mock_open

import pytest

from tests.shared import host


@pytest.mark.parametrize(
    ("returncode", "expected"),
    [
        (0, True),
        (1, False),
    ],
)
def test_result_ok_reflects_return_code(make_result, returncode, expected):
    assert make_result(returncode=returncode).ok is expected


def test_result_output_combines_and_strips_streams(make_result):
    result = make_result(stdout="standard output\n", stderr="standard error\n")

    assert result.output == "standard output\nstandard error"


def test_run_captures_command_result(monkeypatch):
    completed = subprocess.CompletedProcess(
        args="false",
        returncode=7,
        stdout="stdout",
        stderr="stderr",
    )
    run = Mock(return_value=completed)
    monkeypatch.setattr(host.subprocess, "run", run)

    result = host.run("false", timeout=12)

    assert result == host.Result(
        command="false",
        returncode=7,
        stdout="stdout",
        stderr="stderr",
    )
    run.assert_called_once_with(
        "false",
        shell=True,
        capture_output=True,
        text=True,
        timeout=12,
    )


@pytest.mark.parametrize(
    ("resolved", "expected"),
    [
        ("/usr/bin/tool", True),
        (None, False),
    ],
)
def test_have_uses_path_lookup(monkeypatch, resolved, expected):
    which = Mock(return_value=resolved)
    monkeypatch.setattr(host.shutil, "which", which)

    assert host.have("tool") is expected
    which.assert_called_once_with("tool")


def test_os_release_parses_values_and_ignores_non_assignments(monkeypatch):
    release = """\
# generated file
NAME="Snosi Linux"
ID='snosi'
IMAGE_VERSION=2026.08
EMPTY=
not-an-assignment
"""
    monkeypatch.setattr("builtins.open", mock_open(read_data=release))

    assert host.os_release() == {
        "NAME": "Snosi Linux",
        "ID": "snosi",
        "IMAGE_VERSION": "2026.08",
        "EMPTY": "",
    }


def test_os_release_returns_empty_mapping_when_file_is_missing(monkeypatch):
    monkeypatch.setattr("builtins.open", Mock(side_effect=FileNotFoundError))

    assert host.os_release() == {}


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("snow", True),
        ("snowfield-ab", True),
        ("cayo", False),
        ("unknown", False),
    ],
)
def test_is_graphical_uses_variant_allowlist(monkeypatch, variant, expected):
    monkeypatch.setattr(host, "VARIANT", variant)

    assert host.is_graphical() is expected


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("enabled\n", True),
        ("enabled-runtime\n", False),
        ("disabled\n", False),
        ("", False),
    ],
)
def test_unit_is_enabled_requires_exact_enabled_state(monkeypatch, make_result, output, expected):
    run = Mock(return_value=make_result(stdout=output))
    monkeypatch.setattr(host, "run", run)

    assert host.unit_is_enabled("example.service") is expected
    run.assert_called_once_with("systemctl is-enabled example.service")


def test_failed_units_returns_unit_names(monkeypatch, make_result):
    output = """\
alpha.service loaded failed failed Alpha
beta.socket loaded failed failed Beta

"""
    monkeypatch.setattr(host, "run", Mock(return_value=make_result(stdout=output)))

    assert host.failed_units() == ["alpha.service", "beta.socket"]


def test_failed_units_ignores_indented_lines(monkeypatch, make_result):
    output = "alpha.service loaded failed failed Alpha\n beta.service loaded failed failed Beta\n"
    monkeypatch.setattr(host, "run", Mock(return_value=make_result(stdout=output)))

    assert host.failed_units() == ["alpha.service"]


def test_failed_units_returns_empty_list_on_successful_empty_output(monkeypatch, make_result):
    monkeypatch.setattr(host, "run", Mock(return_value=make_result(stdout="")))

    assert host.failed_units() == []


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr", "diagnostic"),
    [
        (1, "stale.service loaded failed failed Stale", "", "stale.service"),
        (7, "", "Failed to connect to bus", "Failed to connect to bus"),
    ],
)
def test_failed_units_raises_on_systemctl_failure(
    monkeypatch, make_result, returncode, stdout, stderr, diagnostic
):
    result = make_result(returncode=returncode, stdout=stdout, stderr=stderr)
    monkeypatch.setattr(host, "run", Mock(return_value=result))

    with pytest.raises(RuntimeError) as error:
        host.failed_units()

    message = str(error.value)
    assert "systemctl list-units --failed --no-legend --plain --no-pager" in message
    assert f"exited {returncode}" in message
    assert diagnostic in message


def test_failed_units_bounds_failure_diagnostics(monkeypatch, make_result):
    result = make_result(returncode=1, stdout="x" * 10000, stderr="y" * 10000)
    monkeypatch.setattr(host, "run", Mock(return_value=result))

    with pytest.raises(RuntimeError) as error:
        host.failed_units()

    message = str(error.value)
    assert "stdout" in message and "stderr" in message
    assert len(message) < 1000
