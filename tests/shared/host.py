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
import shutil
import subprocess
from dataclasses import dataclass


# Set by the lab's run-container-tests template. Defaults keep the suite usable
# when run by hand on a snosi machine.
VARIANT = os.environ.get("SNOSI_VARIANT", "snow")
IMAGE = os.environ.get("SNOSI_IMAGE", "<unknown>")

# Variants that ship a graphical session. cayo is the headless server image, so
# desktop expectations must not be asserted against it.
GRAPHICAL_VARIANTS = {"snow", "snowfield", "snow-ab", "snowfield-ab"}


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


def unit_is_enabled(unit: str) -> bool:
    """True when systemd reports the unit as enabled.

    `is-enabled` exits non-zero for 'disabled', 'static', and 'masked' alike, so
    the exit code alone cannot distinguish them. Match on the word instead.
    """
    return run(f"systemctl is-enabled {unit}").output.splitlines()[:1] == ["enabled"]


def failed_units() -> list[str]:
    """Names of units in the failed state."""
    result = run("systemctl list-units --failed --no-legend --plain --no-pager")
    if not result.ok:
        return []
    return [
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith(" ")
    ]
