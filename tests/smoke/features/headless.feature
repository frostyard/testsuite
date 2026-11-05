@smoke
Feature: The headless image starts no desktop app at first login
  floe has no graphical session, so desktop.feature skips it as a whole. This
  feature holds the headless side of the desktop contracts, and it skips every
  graphical variant.

  Background:
    Given the image ships no graphical session

  Scenario: No first-login app is installed
    # snosi ADR-0028: only Snow and Snowfield ship a first-login trigger.
    Then no first-login autostart entry exists
    And "snow-first-setup" is not on PATH
    And "chairlift-first-run" is not on PATH
