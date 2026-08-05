"""Steps specific to the smoke suite."""

from __future__ import annotations

from behave import then  # type: ignore[import-untyped]

from tests.shared import host


# Units that cannot succeed under the container harness and whose failure says
# nothing about the image.
#
# This list is empirical, not predicted: every entry was observed failing on a
# real run and carries the reason it cannot pass. Anything not listed fails the
# suite — a speculative allowlist is how a real regression gets tolerated
# forever, so do not add a unit here without first seeing it fail.
#
# The set is harness-scoped, not image-scoped: it is the union across the
# environments the suite runs in (a plain `podman run` on a workstation and the
# lab's privileged pod), because those differ in seccomp, capabilities, and
# which paths the harness pins. A unit listed here is NOT excused on real
# hardware — that is what the VM lane exists to check.
EXPECTED_CONTAINER_FAILURES = {
    # ── genuinely impossible in any container ────────────────────────────────
    # binfmt_misc is a kernel filesystem the container may not mount; the host
    # owns it.
    "proc-sys-fs-binfmt_misc.automount",
    # Reads PSI via /proc/pressure, which is not namespaced.
    "low-memory-monitor.service",
    # Needs RLIMIT_RTPRIO and SCHED_RESET_ON_FORK. Available under a plain
    # privileged podman run, refused under the lab pod's seccomp profile.
    "rtkit-daemon.service",
    # Reconciles the bootc shim second-stage bootloader against the ESP. A
    # container has no ESP and no boot partition. On a real install this unit
    # MUST succeed — that is the VM lane's job.
    "snosi-bootc-bootloader-reconcile.service",

    # ── induced by the harness, not by the image ─────────────────────────────
    # The lab bind-mounts /etc/resolv.conf read-only so apt has working DNS
    # inside the nested container. systemd-resolved cannot manage a read-only
    # resolv.conf and fails, taking its two Varlink sockets with it. Removing
    # the mount would fix these three and break every apt-dependent step, so
    # the trade is deliberate.
    "systemd-resolved.service",
    "systemd-resolved-monitor.socket",
    "systemd-resolved-varlink.socket",
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
