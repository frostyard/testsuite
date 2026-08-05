@smoke
Feature: The image boots to a usable system
  The most basic contract a bootc image owes: PID 1 comes up, the message bus
  is available, and nothing failed that is not a known limitation of running
  without real hardware.

  Background:
    Given systemd has finished booting

  Scenario: The system message bus is running
    # dbus-broker provides dbus.service on snosi. Nearly every later probe —
    # systemd state, logind, NetworkManager — depends on it, so a failure here
    # explains a cascade of others.
    Then the "dbus.service" unit is active

  Scenario: No unexpected units failed during boot
    Then no unexpected systemd units failed

  Scenario: The journal is readable
    When I run "journalctl --no-pager -n 1"
    Then the command succeeds

  Scenario: systemd reports a coherent unit inventory
    # Guards against a corrupt or truncated unit tree, which shows up as an
    # empty listing rather than an error.
    When I run "systemctl list-units --type=service --no-legend --plain --no-pager"
    Then the command succeeds
    And the output contains "systemd-journald.service"
