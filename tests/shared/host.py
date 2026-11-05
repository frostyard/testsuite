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

# The keys the canonical first-login entry may carry, and the prefixes of the
# localized Name/Comment keys it may also carry. Every other key (TryExec,
# OnlyShowIn, NotShowIn, Hidden, AutostartCondition, X-GNOME-Autostart-*,
# X-KDE-*, ...) can stop GNOME from starting it; copied from snosi.
CANONICAL_KEYS = frozenset(
    {
        "Type",
        "Name",
        "GenericName",
        "Comment",
        "Exec",
        "Icon",
        "Terminal",
        "NoDisplay",
        "StartupNotify",
        "Categories",
        "Version",
    }
)
CANONICAL_LOCALIZED = ("Name[", "GenericName[", "Comment[")


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
    """Return the `[Desktop Entry]` group of a desktop entry file.

    The whole file is validated, as snosi's first-login check does: every
    non-blank, non-comment line must be a group header or a `key=value` line
    inside a group, no group or key may appear twice, and a `[Desktop Entry]`
    group must exist. Anything else raises ValueError with `path:line` in the
    message: a desktop file we cannot read with confidence must not pass a
    scenario. A missing file raises FileNotFoundError.
    """
    groups: dict[str, dict[str, str]] = {}
    current: str | None = None
    with open(path, encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                current = stripped[1:-1]
                if current in groups:
                    raise ValueError(f"{path}:{number}: group [{current}] appears twice")
                groups[current] = {}
                continue
            if current is None or "=" not in stripped:
                raise ValueError(f"{path}:{number}: not a key=value line in a group")
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key in groups[current]:
                raise ValueError(f"{path}:{number}: key {key} appears twice in [{current}]")
            groups[current][key] = value.strip()

    if "Desktop Entry" not in groups:
        raise ValueError(f"{path}: no [Desktop Entry] group")
    return groups["Desktop Entry"]


def autostart_entries() -> list[str]:
    """Absolute paths of the XDG autostart entries present in the image.

    Every `*.desktop` name is listed, whether or not it is a readable file: a
    dangling symlink is leftover packaging, and a caller that must read the
    entry fails closed on it. A missing directory is not an error; a path that
    exists but cannot be listed is.
    """
    entries: list[str] = []
    for directory in AUTOSTART_DIRS:
        if not os.path.lexists(directory):
            continue
        try:
            names = os.listdir(directory)
        except OSError as error:
            raise RuntimeError(f"cannot list {directory}: {error}") from error
        for name in names:
            if name.endswith(".desktop"):
                entries.append(os.path.join(directory, name))
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


def starts_on_gnome(entry: dict[str, str]) -> bool:
    """Would GNOME's autostart start this `[Desktop Entry]`?

    Copied from snosi's first-login check, so the suite and the image agree on
    what a trigger is.
    """

    def listed(key: str) -> list[str]:
        return [value for value in entry.get(key, "").split(";") if value]

    if entry.get("Type") != "Application":
        return False
    if entry.get("Hidden", "false").lower() == "true":
        return False
    if entry.get("X-GNOME-Autostart-enabled", "true").lower() == "false":
        return False
    # A present but empty OnlyShowIn allows no desktop at all.
    if "OnlyShowIn" in entry and "GNOME" not in listed("OnlyShowIn"):
        return False
    if "GNOME" in listed("NotShowIn"):
        return False
    return True


def is_executable_by_all(path: str) -> bool:
    """Is `path` a regular file (symlinks followed) that every user may run?

    A first-login entry runs as the desktop user, not as root, so the file
    needs the execute bit for other, not only for owner or group. `os.access`
    cannot answer this: the suite runs as root, which may execute anything it
    can read.
    """
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return False
    return stat.S_ISREG(mode) and bool(mode & stat.S_IXOTH)


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
