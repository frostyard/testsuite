@smoke
Feature: The shipped toolchain is present and runnable
  Every binary here is one a snosi machine is expected to have on first boot.
  Presence on PATH is the floor; where a tool can answer a harmless query
  without side effects, the scenario runs it, because a binary that exists but
  cannot execute (missing library, wrong interpreter) is a shipped-broken image.

  Scenario: bootc is installed and functional
    Then "bootc" is on PATH
    When I run "bootc --version"
    Then the command succeeds
    And the output contains "bootc"

  Scenario: bootc can report host status
    # In a container `booted` is null — there is no real deployment. What is
    # under test is that the binary runs and emits well-formed status rather
    # than crashing on a non-bootc root.
    When I run "bootc status"
    Then the command succeeds
    And the output contains "kind: BootcHost"

  Scenario: The sysext toolchain is present
    Then "systemd-sysext" is on PATH
    And "updex" is on PATH
    And "/var/lib/extensions" is a directory

  Scenario: updex runs
    When I run "updex --help"
    Then the command succeeds

  Scenario: Debian package tooling is intact
    Then "apt" is on PATH
    And "dpkg" is on PATH
    When I run "dpkg --list"
    Then the command succeeds

  Scenario: The container toolchain is present
    Then "podman" is on PATH
    And "distrobox" is on PATH
