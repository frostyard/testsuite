@smoke @graphical
Feature: Graphical variants ship a working desktop stack
  These scenarios assert only what is provable without a seat: the components
  are installed and systemd is configured to reach a graphical session. Whether
  the display manager actually starts a session needs a real seat and belongs
  to the VM lane.

  Every scenario is skipped on headless variants (floe), so the same suite runs
  unmodified against the whole image family. Desktop-specific scenarios also
  skip on variants that ship the other desktop: snow and snowfield ship GNOME,
  sundog ships KDE Plasma.

  Background:
    Given the image ships a graphical session

  Scenario: The system boots into a graphical target
    Then the default systemd target is "graphical.target"

  Scenario: GNOME Shell is installed
    Given the image ships the "gnome" desktop
    Then "gnome-shell" is on PATH

  Scenario: The GNOME display manager is installed
    Given the image ships the "gnome" desktop
    Then "gdm3" is on PATH
    And "/usr/lib/systemd/system/gdm.service" exists

  Scenario: The GNOME terminal emulator is installed
    Given the image ships the "gnome" desktop
    Then "ptyxis" is on PATH

  Scenario: Plasma Shell is installed
    Given the image ships the "kde" desktop
    Then "plasmashell" is on PATH

  Scenario: The KDE display manager is installed
    Given the image ships the "kde" desktop
    Then "sddm" is on PATH
    And "/usr/lib/systemd/system/sddm.service" exists

  Scenario: The KDE terminal emulator is installed
    Given the image ships the "kde" desktop
    Then "konsole" is on PATH

  Scenario: Flatpak is installed
    # floe ships no flatpak — application delivery on the server image is
    # containers and sysexts only.
    Then "flatpak" is on PATH

  Scenario: Desktop frostyard tooling is installed
    # chairlift (system management) is part of the desktop experience and is
    # absent from the headless image. igloo is deliberately not asserted:
    # snosi removed it from Snow (snosi#515) and it may return, so this
    # scenario stays neutral about it.
    Then "chairlift" is on PATH

  Scenario: First login runs the chairlift first run
    # snosi ADR-0028 (snosi#1224): Snow and Snowfield ship exactly one
    # first-login trigger, an XDG autostart entry that runs chairlift's pure-Go
    # gate. The gate exits at once when a done marker exists (its own or the
    # legacy snow-first-setup.done), so the entry is safe at every login.
    Given the image ships the "gnome" desktop
    Then the only first-login autostart entry is "/etc/xdg/autostart/org.frostyard.ChairLift.FirstRun.desktop"
    And the desktop entry "/etc/xdg/autostart/org.frostyard.ChairLift.FirstRun.desktop" sets "Exec" to "/usr/bin/chairlift-first-run"
    And "/usr/bin/chairlift-first-run" is an executable file

  Scenario: SNOW First Setup is retired
    # The chairlift first run replaced snow-first-setup (snosi ADR-0028). A
    # leftover entry would start a second first-login app, or a missing one.
    Given the image ships the "gnome" desktop
    Then no "org.frostyard.FirstSetup" autostart entry exists
    And "/usr/share/applications/org.frostyard.FirstSetup.desktop" does not exist
    And "snow-first-setup" is not on PATH

  Scenario: Plasma has no first-login app
    # Sundog gets no first run (plan T843, decision T843b): Firn owns the
    # first-install choices, and the first run is GNOME-only.
    Given the image ships the "kde" desktop
    Then no first-login autostart entry exists
    And "snow-first-setup" is not on PATH
