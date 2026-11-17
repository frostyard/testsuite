@smoke
Feature: The image identifies itself correctly
  os-release is the contract every downstream tool reads to decide what it is
  running on — updex, chairlift, bootc, and third-party installers all branch on
  it. A wrong or missing field breaks them silently rather than loudly.

  Scenario: The image is derived from a supported Debian release
    # snosi builds the trixie stream (Debian 13) and the opt-in forky stream
    # (Debian 14; snosi ADR-0037 writes VERSION_ID="14" because Debian testing
    # ships none). The codename and VERSION_ID must name the same release:
    # sysext and sysupdate contracts key off VERSION_ID.
    Then os-release "ID_LIKE" is "debian"
    And os-release names a supported Debian release

  Scenario: The image carries build provenance
    # IMAGE_ID names the variant and IMAGE_VERSION is the mkosi build stamp.
    # Without them a running machine cannot say which build it came from, which
    # makes every field bug report unactionable.
    Then os-release "IMAGE_ID" is set
    And os-release "IMAGE_VERSION" is set

  Scenario: The image declares a sysext compatibility level
    # systemd-sysext refuses to merge an extension whose SYSEXT_LEVEL does not
    # match the host's. If this is unset, every shipped sysext fails to load.
    Then os-release "SYSEXT_LEVEL" is set

  Scenario: A human-readable name is present
    Then os-release "PRETTY_NAME" is set
    And os-release "NAME" is set
