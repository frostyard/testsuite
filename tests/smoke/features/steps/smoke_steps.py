"""Steps specific to the smoke suite."""

from __future__ import annotations

from behave import then  # type: ignore[import-untyped]

from tests.shared import host


# Units that cannot succeed inside a nested container and whose failure says
# nothing about the image.
#
# This list is empirical, not predicted: it is exactly the set observed failing
# on a clean `podman run --systemd=always` of ghcr.io/frostyard/snow:latest.
# Keep it that way. Every entry carries the reason it cannot pass, and anything
# not listed here fails the suite — a speculative allowlist is how a real
# regression gets tolerated forever.
EXPECTED_CONTAINER_FAILURES = {
    # binfmt_misc is a kernel filesystem the container is not permitted to
    # mount; the host owns it.
    "proc-sys-fs-binfmt_misc.automount",
    # Reads /proc/pressure via the host kernel's PSI, which is not namespaced.
    "low-memory-monitor.service",
    # Reconciles the bootc shim second-stage bootloader against the ESP. A
    # container has no ESP and no boot partition, so this cannot apply. On a
    # real install this unit MUST succeed — that is the VM lane's job.
    "snosi-bootc-bootloader-reconcile.service",
}


@then("no unexpected systemd units failed")
def step_no_unexpected_failures(context):
    failed = set(host.failed_units())
    unexpected = sorted(failed - EXPECTED_CONTAINER_FAILURES)

    # Report the whole picture on failure — what is new and what was tolerated —
    # so triage does not need a second run to get the context.
    tolerated = sorted(failed & EXPECTED_CONTAINER_FAILURES)
    assert not unexpected, (
        "Unexpected failed units:\n  "
        + "\n  ".join(unexpected)
        + "\n\nTolerated (known container limitations):\n  "
        + ("\n  ".join(tolerated) or "(none)")
    )


@then('os-release "{key}" is "{expected}"')
def step_os_release_equals(context, key, expected):
    values = host.os_release()
    assert key in values, f"/etc/os-release has no {key} (keys: {sorted(values)})"
    assert values[key] == expected, (
        f"os-release {key} is {values[key]!r}, expected {expected!r}"
    )


@then('os-release "{key}" is set')
def step_os_release_set(context, key):
    values = host.os_release()
    assert values.get(key), (
        f"/etc/os-release {key} is missing or empty (keys: {sorted(values)})"
    )


@then("the default systemd target is \"{target}\"")
def step_default_target(context, target):
    actual = host.run("systemctl get-default").output
    assert actual == target, f"default target is {actual!r}, expected {target!r}"
