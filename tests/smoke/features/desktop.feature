@smoke @graphical
Feature: Graphical variants ship a working desktop stack
  These scenarios assert only what is provable without a seat: the components
  are installed and systemd is configured to reach a graphical session. Whether
  GDM actually starts a session needs a real seat and belongs to the VM lane.

  Every scenario is skipped on headless variants (cayo), so the same suite runs
  unmodified against the whole image family.

  Background:
    Given the image ships a graphical session

  Scenario: The system boots into a graphical target
    Then the default systemd target is "graphical.target"

  Scenario: GNOME Shell is installed
    Then "gnome-shell" is on PATH

  Scenario: The display manager is installed
    Then "gdm3" is on PATH
    And "/usr/lib/systemd/system/gdm.service" exists

  Scenario: The terminal emulator is installed
    Then "ptyxis" is on PATH

  Scenario: Flatpak is installed
    # cayo ships no flatpak — application delivery on the server image is
    # containers and sysexts only.
    Then "flatpak" is on PATH

  Scenario: Desktop frostyard tooling is installed
    # chairlift (system management) and igloo (dev environments) are part of
    # the desktop experience and are absent from the headless image.
    Then "chairlift" is on PATH
    And "igloo" is on PATH
