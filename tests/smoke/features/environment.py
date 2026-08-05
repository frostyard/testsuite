"""behave environment hooks for the smoke suite."""

from tests.shared import host


def before_all(context):
    # Echoed into the workflow log so a failed run identifies its own subject
    # without cross-referencing the Argo parameters.
    context.variant = host.VARIANT
    context.image = host.IMAGE
    print(f"snosi smoke suite — variant={host.VARIANT} image={host.IMAGE}")

    release = host.os_release()
    print(f"  {release.get('PRETTY_NAME', '<no PRETTY_NAME>')}")
    print(f"  IMAGE_ID={release.get('IMAGE_ID', '<unset>')} "
          f"IMAGE_VERSION={release.get('IMAGE_VERSION', '<unset>')}")
