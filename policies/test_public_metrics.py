import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/metrics/README.md"
TUNING = ROOT / ".github/auto-qa-tuning.json"


class PublicMetricsTests(unittest.TestCase):
    def test_public_metrics_index_is_substantive(self) -> None:
        self.assertTrue(INDEX.parent.is_dir(), "docs/metrics must be a directory")
        contents = INDEX.read_text(encoding="utf-8")

        for required in (
            "# Public metrics",
            "## Signal index",
            "## Pull-request acceptance",
            "## Publication and privacy contract",
            "https://github.com/frostyard/testsuite/actions/workflows/ci.yml",
            "https://github.com/frostyard/lab/actions",
            "https://codecov.io/gh/frostyard/testsuite",
            "accepted PRs / (accepted PRs + closed, unmerged PRs) × 100",
        ):
            self.assertIn(required, contents)

    def test_tuning_signal_targets_the_canonical_metric(self) -> None:
        tuning = json.loads(TUNING.read_text(encoding="utf-8"))
        self.assertEqual(
            tuning["signals"]["pr_acceptance_rate"],
            "docs/metrics/README.md#pull-request-acceptance",
        )


if __name__ == "__main__":
    unittest.main()
