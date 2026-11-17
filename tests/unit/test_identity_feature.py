"""Run identity.feature's steps against stubbed os-release data.

The scenarios are matched to their step functions through behave's own step
registry, so the test checks the feature text and the steps together: an
assertion in the feature that only one Debian release can meet fails here.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from behave.parser import parse_file  # type: ignore[import-untyped]
from behave.step_registry import registry  # type: ignore[import-untyped]

from tests.smoke.features.steps import smoke_steps

FEATURE = (
    Path(__file__).resolve().parents[2] / "tests" / "smoke" / "features" / "identity.feature"
)

COMMON = {
    "ID": "snow",
    "ID_LIKE": "debian",
    "NAME": "Snow Linux",
    "PRETTY_NAME": "Snow Linux",
    "IMAGE_ID": "snow",
    "IMAGE_VERSION": "20261114163823",
    "SYSEXT_LEVEL": "1.0",
}


def run_feature(monkeypatch, release):
    monkeypatch.setattr(smoke_steps.host, "os_release", Mock(return_value=release))
    feature = parse_file(str(FEATURE))
    context = SimpleNamespace(scenario=SimpleNamespace(skip=Mock()))
    ran = 0
    for scenario in feature.scenarios:
        for step in scenario.steps:
            match = registry.find_match(step)
            assert match is not None, f"no step definition for {step.keyword} {step.name}"
            # Match.run needs a full behave Runner context; the step functions
            # need only the parsed arguments.
            match.func(context, **{arg.name: arg.value for arg in match.arguments})
            ran += 1
    assert ran > 0, "identity.feature ran no steps"


@pytest.mark.parametrize(
    ("codename", "version_id"),
    [("trixie", "13"), ("forky", "14")],
)
def test_identity_feature_accepts_each_snosi_release(monkeypatch, codename, version_id):
    run_feature(
        monkeypatch,
        {**COMMON, "VERSION_CODENAME": codename, "VERSION_ID": version_id},
    )


@pytest.mark.parametrize(
    ("codename", "version_id"),
    [("bookworm", "12"), ("forky", "13"), ("trixie", "14"), ("trixie", "1.0")],
)
def test_identity_feature_rejects_other_or_mismatched_release(monkeypatch, codename, version_id):
    with pytest.raises(AssertionError):
        run_feature(
            monkeypatch,
            {**COMMON, "VERSION_CODENAME": codename, "VERSION_ID": version_id},
        )
