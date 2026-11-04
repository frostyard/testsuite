import subprocess
import sys
from pathlib import Path

# Imported, not importorskip: a skipped case would pass vacuously in CI.
import behave  # noqa: F401

CHECKER = Path(__file__).resolve().parents[2] / "policies" / "check_feature_discovery.py"


def run_checker(features_dir):
    return subprocess.run(
        [sys.executable, CHECKER, str(features_dir)],
        capture_output=True,
        text=True,
        check=False,
    )


def write_feature(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_steps(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "from behave import given\n\n"
        "@given('a plain step')\n"
        "def plain_step(context):\n"
        "    pass\n",
        encoding="utf-8",
    )


def test_feature_discovery_rejects_zero_scenarios(tmp_path):
    features = tmp_path / "features"
    write_steps(features / "steps" / "steps.py")

    result = run_checker(features)

    assert result.returncode != 0
    assert "0 scenarios selected" in result.stdout
    assert "feature discovery failed" in result.stderr


def test_feature_discovery_rejects_wip_only(tmp_path):
    features = tmp_path / "features"
    write_feature(
        features / "wip.feature",
        "Feature: wip only\n"
        "  @wip\n"
        "  Scenario: excluded\n"
        "    Given a plain step\n",
    )
    write_steps(features / "steps" / "steps.py")

    result = run_checker(features)

    assert result.returncode != 0
    assert "0 scenarios selected" in result.stdout
    assert "0 scenarios selected" in result.stderr


def test_feature_discovery_accepts_one_plain_scenario(tmp_path):
    features = tmp_path / "features"
    write_feature(
        features / "plain.feature",
        "Feature: plain\n"
        "  Scenario: included\n"
        "    Given a plain step\n",
    )
    write_steps(features / "steps" / "steps.py")

    result = run_checker(features)

    assert result.returncode == 0, result.stderr
    assert "feature discovery: 1 features, 1 scenarios selected" in result.stdout
