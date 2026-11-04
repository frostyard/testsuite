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


def test_feature_discovery_counts_outline_rows_not_background_or_wip(tmp_path):
    features = tmp_path / "features"
    write_feature(
        features / "mixed.feature",
        "Feature: mixed\n"
        "  Background:\n"
        "    Given a plain step\n"
        "\n"
        "  Scenario: plain\n"
        "    Given a plain step\n"
        "\n"
        "  Scenario Outline: rows <n>\n"
        "    Given a plain step\n"
        "    Examples:\n"
        "      | n |\n"
        "      | 1 |\n"
        "      | 2 |\n"
        "\n"
        "  @wip\n"
        "  Scenario: excluded\n"
        "    Given a plain step\n",
    )
    write_steps(features / "steps" / "steps.py")

    result = run_checker(features)

    assert result.returncode == 0, result.stderr
    assert "feature discovery: 1 features, 3 scenarios selected" in result.stdout


def test_discover_rejects_unknown_scenario_status(tmp_path, monkeypatch):
    sys.path.insert(0, str(CHECKER.parent))
    import check_feature_discovery

    def fake_run(command, **kwargs):
        output = Path(command[command.index("-o") + 1])
        output.write_text('[{"elements": [{"type": "scenario"}]}]', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(check_feature_discovery.subprocess, "run", fake_run)
    (tmp_path / "features").mkdir()

    _, _, error = check_feature_discovery.discover(tmp_path / "features")

    assert error == "unexpected scenario status: None"
