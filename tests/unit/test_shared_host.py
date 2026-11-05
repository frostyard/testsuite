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
        ("sundog", True),
        ("floe", False),
        ("unknown", False),
    ],
)
def test_is_graphical_uses_variant_allowlist(monkeypatch, variant, expected):
    monkeypatch.setattr(host, "VARIANT", variant)

    assert host.is_graphical() is expected


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("snow", "gnome"),
        ("snowfield", "gnome"),
        ("sundog", "kde"),
        ("floe", None),
    ],
)
def test_desktop_names_the_shipped_desktop(monkeypatch, variant, expected):
    monkeypatch.setattr(host, "VARIANT", variant)

    assert host.desktop() == expected


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


CANONICAL_ENTRY = """\
[Desktop Entry]
Type=Application
Name=ChairLift First Run
Comment=Set up this machine
Exec=/usr/bin/chairlift-first-run
Icon=org.frostyard.ChairLift
Terminal=false
NoDisplay=true
"""


def write_entry(directory, name, text):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def autostart_dir(monkeypatch, tmp_path):
    directory = tmp_path / "autostart"
    directory.mkdir()
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(directory),))
    return directory


# ── desktop_entry ─────────────────────────────────────────────────────────────


def test_desktop_entry_parses_the_desktop_entry_group(tmp_path):
    path = write_entry(
        tmp_path,
        "app.desktop",
        CANONICAL_ENTRY
        + """
[Desktop Action Open]
Exec=/usr/bin/other
""",
    )

    assert host.desktop_entry(str(path)) == {
        "Type": "Application",
        "Name": "ChairLift First Run",
        "Comment": "Set up this machine",
        "Exec": "/usr/bin/chairlift-first-run",
        "Icon": "org.frostyard.ChairLift",
        "Terminal": "false",
        "NoDisplay": "true",
    }


def test_desktop_entry_strips_around_equals_and_ignores_comments(tmp_path):
    path = write_entry(
        tmp_path,
        "app.desktop",
        "# a comment\n[Desktop Entry]\n  Name  =  Spaced  \n\n   # indented comment\n",
    )

    assert host.desktop_entry(str(path)) == {"Name": "Spaced"}


def test_desktop_entry_raises_for_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        host.desktop_entry(str(tmp_path / "absent.desktop"))


def test_desktop_entry_raises_for_a_line_that_is_not_key_value(tmp_path):
    path = write_entry(tmp_path, "broken.desktop", "[Desktop Entry]\nType=Application\nbroken\n")

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert f"{path}:3: not a key=value line in a group" in str(error.value)


def test_desktop_entry_raises_for_a_key_before_any_group(tmp_path):
    path = write_entry(tmp_path, "early.desktop", "Type=Application\n[Desktop Entry]\nName=x\n")

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert f"{path}:1: not a key=value line in a group" in str(error.value)


@pytest.mark.parametrize(
    ("text", "line", "group"),
    [
        ("[Desktop Entry]\nName=x\n[Desktop Entry]\nName=y\n", 3, "Desktop Entry"),
        (
            "[Desktop Entry]\nName=x\n[Desktop Action Open]\n[Desktop Action Open]\n",
            4,
            "Desktop Action Open",
        ),
    ],
)
def test_desktop_entry_raises_for_a_duplicate_group(tmp_path, text, line, group):
    path = write_entry(tmp_path, "twice.desktop", text)

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert f"{path}:{line}: group [{group}] appears twice" in str(error.value)


def test_desktop_entry_raises_for_a_duplicate_key(tmp_path):
    path = write_entry(
        tmp_path, "dup.desktop", "[Desktop Entry]\nExec=/usr/bin/a\nExec=/usr/bin/b\n"
    )

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert f"{path}:3: key Exec appears twice in [Desktop Entry]" in str(error.value)


def test_desktop_entry_raises_for_a_duplicate_key_in_another_group(tmp_path):
    path = write_entry(
        tmp_path,
        "dup.desktop",
        "[Desktop Entry]\nName=x\n\n[Desktop Action Open]\nExec=/usr/bin/a\nExec=/usr/bin/b\n",
    )

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert f"{path}:6: key Exec appears twice in [Desktop Action Open]" in str(error.value)


def test_desktop_entry_raises_without_a_desktop_entry_group(tmp_path):
    path = write_entry(tmp_path, "other.desktop", "[Desktop Action Open]\nExec=/usr/bin/a\n")

    with pytest.raises(ValueError) as error:
        host.desktop_entry(str(path))

    assert str(path) in str(error.value)
    assert "no [Desktop Entry] group" in str(error.value)


# ── autostart_entries ─────────────────────────────────────────────────────────


def test_autostart_entries_returns_sorted_desktop_names(monkeypatch, tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    write_entry(first, "b.desktop", CANONICAL_ENTRY)
    write_entry(first, "a.desktop", CANONICAL_ENTRY)
    write_entry(first, "notes.txt", "ignored\n")
    write_entry(second, "c.desktop", CANONICAL_ENTRY)
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(first), str(second)))

    assert host.autostart_entries() == [
        str(first / "a.desktop"),
        str(first / "b.desktop"),
        str(second / "c.desktop"),
    ]


def test_autostart_entries_lists_names_without_an_isfile_filter(monkeypatch, tmp_path):
    write_entry(tmp_path, "file.desktop", CANONICAL_ENTRY)
    (tmp_path / "folder.desktop").mkdir()
    (tmp_path / "dangling.desktop").symlink_to(tmp_path / "gone.desktop")
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    assert host.autostart_entries() == [
        str(tmp_path / "dangling.desktop"),
        str(tmp_path / "file.desktop"),
        str(tmp_path / "folder.desktop"),
    ]


def test_autostart_entries_treats_a_missing_directory_as_empty(monkeypatch, tmp_path):
    present = tmp_path / "present"
    write_entry(present, "only.desktop", CANONICAL_ENTRY)
    monkeypatch.setattr(
        host,
        "AUTOSTART_DIRS",
        (str(tmp_path / "absent"), str(present)),
    )

    assert host.autostart_entries() == [str(present / "only.desktop")]


def test_autostart_entries_raises_when_an_autostart_path_is_not_a_directory(
    monkeypatch, tmp_path
):
    path = tmp_path / "autostart"
    path.write_text("not a directory\n", encoding="utf-8")
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(path),))

    with pytest.raises(RuntimeError) as error:
        host.autostart_entries()

    assert str(path) in str(error.value)
    assert "cannot list" in str(error.value)


# ── first_login_entries ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("name", "exec_line"),
    [
        ("org.frostyard.ChairLift.FirstRun.desktop", "/usr/bin/chairlift-first-run"),
        ("org.frostyard.FirstSetup.desktop", "/usr/bin/snow-first-setup"),
        ("custom.desktop", "snow-first-setup --autostart"),
        ("custom.desktop", "/usr/bin/chairlift-first-run"),
        ("custom.desktop", "chairlift --first-run"),
    ],
)
def test_first_login_entries_recognizes_each_trigger(monkeypatch, tmp_path, name, exec_line):
    entry = write_entry(
        tmp_path,
        name,
        f"[Desktop Entry]\nType=Application\nExec={exec_line}\n",
    )
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    assert host.first_login_entries() == [str(entry)]


def test_first_login_entries_ignores_other_entries(monkeypatch, tmp_path):
    write_entry(
        tmp_path,
        "org.frostyard.News.desktop",
        "[Desktop Entry]\nExec=/usr/bin/chairlift\n",
    )
    write_entry(tmp_path, "other.desktop", "[Desktop Entry]\nExec=/usr/bin/other --first-run\n")
    write_entry(tmp_path, "noexec.desktop", "[Desktop Entry]\nName=No Exec\n")
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    assert host.first_login_entries() == []


def test_first_login_entries_raises_for_a_dangling_symlink(monkeypatch, tmp_path):
    entry = tmp_path / "org.frostyard.FirstSetup.autostart.desktop"
    entry.symlink_to(tmp_path / "gone.desktop")
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    with pytest.raises(RuntimeError) as error:
        host.first_login_entries()

    assert str(entry) in str(error.value)


def test_first_login_entries_raises_for_an_unparseable_entry(monkeypatch, tmp_path):
    entry = write_entry(tmp_path, "broken.desktop", "[Desktop Entry]\nbroken\n")
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    with pytest.raises(RuntimeError) as error:
        host.first_login_entries()

    assert str(entry) in str(error.value)
    assert "not a key=value line in a group" in str(error.value)


def test_first_login_entries_raises_for_an_unreadable_exec(monkeypatch, tmp_path):
    entry = write_entry(
        tmp_path,
        "quoted.desktop",
        '[Desktop Entry]\nExec="/usr/bin/chairlift-first-run\n',
    )
    monkeypatch.setattr(host, "AUTOSTART_DIRS", (str(tmp_path),))

    with pytest.raises(RuntimeError) as error:
        host.first_login_entries()

    assert str(entry) in str(error.value)
    assert "cannot parse Exec" in str(error.value)


# ── starts_on_gnome ───────────────────────────────────────────────────────────


def canonical_entry(tmp_path):
    return host.desktop_entry(str(write_entry(tmp_path, "entry.desktop", CANONICAL_ENTRY)))


def entry_with(tmp_path, **overrides):
    entry = canonical_entry(tmp_path)
    for key, value in overrides.items():
        if value is None:
            entry.pop(key, None)
        else:
            entry[key] = value
    return entry


def test_starts_on_gnome_accepts_the_canonical_entry(tmp_path):
    assert host.starts_on_gnome(canonical_entry(tmp_path)) is True


def test_starts_on_gnome_accepts_a_localized_name(tmp_path):
    entry = entry_with(tmp_path, **{"Name[de]": "Ersteinrichtung"})

    assert host.starts_on_gnome(entry) is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"Hidden": "true"},
        {"X-GNOME-Autostart-enabled": "false"},
        {"Type": "Link"},
        {"Type": None},
        {"OnlyShowIn": "KDE;"},
        {"OnlyShowIn": ""},
        {"NotShowIn": "GNOME;"},
    ],
    ids=[
        "hidden",
        "gnome-disabled",
        "type-link",
        "type-missing",
        "only-kde",
        "only-empty",
        "not-gnome",
    ],
)
def test_starts_on_gnome_rejects_an_entry_gnome_would_not_start(tmp_path, overrides):
    assert host.starts_on_gnome(entry_with(tmp_path, **overrides)) is False


def test_starts_on_gnome_accepts_an_other_desktop_in_only_show_in(tmp_path):
    entry = entry_with(tmp_path, OnlyShowIn="GNOME;KDE;")

    assert host.starts_on_gnome(entry) is True


# ── is_executable_by_all ──────────────────────────────────────────────────────


@pytest.mark.parametrize("mode", [0o755, 0o757])
def test_is_executable_by_all_accepts_a_file_others_may_run(tmp_path, mode):
    path = tmp_path / "run"
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(mode)

    assert host.is_executable_by_all(str(path)) is True


@pytest.mark.parametrize("mode", [0o700, 0o750, 0o644, 0o600])
def test_is_executable_by_all_rejects_a_file_others_may_not_run(tmp_path, mode):
    path = tmp_path / "run"
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(mode)

    assert host.is_executable_by_all(str(path)) is False


def test_is_executable_by_all_rejects_a_directory(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    path.chmod(0o755)

    assert host.is_executable_by_all(str(path)) is False


def test_is_executable_by_all_rejects_a_missing_path(tmp_path):
    assert host.is_executable_by_all(str(tmp_path / "absent")) is False


def test_is_executable_by_all_follows_a_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o755)
    link = tmp_path / "link"
    link.symlink_to(target)

    assert host.is_executable_by_all(str(link)) is True
