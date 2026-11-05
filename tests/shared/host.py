"""Helpers for probing the snosi image under test.

Every suite runs *inside* the image being tested: the lab boots the bootc OCI
image as a nested systemd container and runs behave against that live system.
So there is no SSH, no serial console, and no remote transport here — a probe is
just a subprocess against the local root filesystem.

What that buys: the tests read exactly like the assertions a user would make on
a running machine. What it costs: anything requiring real hardware, a graphical
seat, or a distinct kernel cannot be asserted here and belongs in the VM lane.
"""

from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
from dataclasses import dataclass


# Set by the lab's run-container-tests template. Defaults keep the suite usable
# when run by hand on a snosi machine.
VARIANT = os.environ.get("SNOSI_VARIANT", "snow")
IMAGE = os.environ.get("SNOSI_IMAGE", "<unknown>")

# The desktop each graphical variant ships. floe is the headless server image,
# so it is absent and desktop expectations are never asserted against it.
DESKTOPS = {
    "snow": "gnome",
    "snowfield": "gnome",
    "snow-ab": "gnome",
    "snowfield-ab": "gnome",
    "sundog": "kde",
}
GRAPHICAL_VARIANTS = frozenset(DESKTOPS)

# The directories XDG autostart reads, in the order snosi's own first-login
# checker (shared/composition/first-login-check.py) reads them. An entry in any
# of them runs its program at the start of a graphical session.
AUTOSTART_DIRS = (
    "/etc/xdg/autostart",
    "/usr/etc/xdg/autostart",
    "/etc/skel/.config/autostart",
)

# The first-login apps snosi has shipped. Snow and Snowfield ship chairlift's
# first run (snosi ADR-0028); snow-first-setup is the retired predecessor. Both
# halves are here so a leftover entry of either is found.
FIRST_LOGIN_NAMES = (
    "org.frostyard.ChairLift.FirstRun",
    "org.frostyard.FirstSetup",
)
FIRST_LOGIN_PROGRAMS = (
    "chairlift-first-run",
    "snow-first-setup",
)


@dataclass(frozen=True)
class Result:
    """Outcome of a command run against the image under test."""

    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        """Combined output — most probes do not care which stream a tool used."""
        return (self.stdout + self.stderr).strip()


def run(command: str, timeout: int = 60) -> Result:
    """Run `command` through a shell and capture its result.

    Never raises on a non-zero exit: a failing command is frequently the thing
    under test, and a step that wants failure to be fatal asserts on it.
    """
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return Result(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def have(binary: str) -> bool:
    """Is `binary` on PATH?"""
    return shutil.which(binary) is not None


def os_release() -> dict[str, str]:
    """Parse /etc/os-release into a dict, with quotes stripped."""
    values: dict[str, str] = {}
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return values


def is_graphical() -> bool:
    return VARIANT in GRAPHICAL_VARIANTS


def desktop() -> str | None:
    """The desktop the variant under test ships, or None when headless."""
    return DESKTOPS.get(VARIANT)


def unit_is_enabled(unit: str) -> bool:
    """True when systemd reports the unit as enabled.

    `is-enabled` exits non-zero for 'disabled', 'static', and 'masked' alike, so
    the exit code alone cannot distinguish them. Match on the word instead.
    """
    return run(f"systemctl is-enabled {unit}").output.splitlines()[:1] == ["enabled"]


def desktop_entry(path: str) -> dict[str, str]:
    """Parse the `[Desktop Entry]` group of an XDG desktop entry file.

    Keys in other groups are ignored, as are blank lines and comments. The
    parse fails closed: a duplicate key, or a file with no `[Desktop Entry]`
    group, raises ValueError rather than returning a partial entry, because a
    desktop file we cannot read with confidence must not pass a scenario. A
    missing file raises FileNotFoundError.
    """
    entry: dict[str, str] = {}
    seen_group = False
    in_group = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                in_group = line == "[Desktop Entry]"
                if in_group:
                    if seen_group:
                        raise ValueError(f"{path}: [Desktop Entry] appears more than once")
                    seen_group = True
                continue
            if not in_group:
                continue
            key, separator, value = line.partition("=")
            if not separator:
                continue
            key = key.strip()
            if key in entry:
                raise ValueError(f"{path}: duplicate key {key!r} in [Desktop Entry]")
            entry[key] = value.strip()

    if not seen_group:
        raise ValueError(f"{path}: no [Desktop Entry] group")
    return entry


def autostart_entries() -> list[str]:
    """Absolute paths of the XDG autostart entries present in the image.

    A missing directory is not an error: a variant that ships no autostart
    directory has no entries to run.
    """
    entries: list[str] = []
    for directory in AUTOSTART_DIRS:
        try:
            names = os.listdir(directory)
        except (FileNotFoundError, NotADirectoryError):
            continue
        for name in names:
            path = os.path.join(directory, name)
            if name.endswith(".desktop") and os.path.isfile(path):
                entries.append(path)
    return sorted(entries)


def first_login_entries() -> list[str]:
    """The autostart entries that start a first-login app.

    An entry counts when its file name starts with a known first-login name, or
    when its `Exec` program is a known first-login program, so a rename on
    either side still gets found. An entry that cannot be read or parsed raises
    RuntimeError: an unreadable entry might be a first-login trigger, so it must
    fail the scenario rather than hide in a passing list.
    """
    entries: list[str] = []
    for path in autostart_entries():
        try:
            entry = desktop_entry(path)
        except (OSError, ValueError) as error:
            raise RuntimeError(f"cannot read desktop entry {path}: {error}") from error

        try:
            words = shlex.split(entry.get("Exec", ""))
        except ValueError as error:
            raise RuntimeError(f"cannot parse Exec of {path}: {error}") from error

        name = os.path.basename(path)
        program = os.path.basename(words[0]) if words else ""
        if (
            any(name.startswith(prefix) for prefix in FIRST_LOGIN_NAMES)
            or program in FIRST_LOGIN_PROGRAMS
            or (program == "chairlift" and "--first-run" in words[1:])
        ):
            entries.append(path)
    return entries


def is_executable_file(path: str) -> bool:
    """Is `path` a regular file (symlinks followed) with an execute bit?

    `os.access` cannot answer this: the suite runs as root, which may execute
    anything it can read. The mode bits are what the image ships.
    """
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return False
    return stat.S_ISREG(mode) and bool(mode & 0o111)


def failed_units() -> list[str]:
    """Names of units in the failed state."""
    result = run("systemctl list-units --failed --no-legend --plain --no-pager")
    if not result.ok:
        raise RuntimeError(
            "systemctl list-units --failed --no-legend --plain --no-pager "
            f"exited {result.returncode}: "
            f"stderr={result.stderr.strip()[:200]!r}; "
            f"stdout={result.stdout.strip()[:200]!r}"
        )
    return [
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith(" ")
    ]
