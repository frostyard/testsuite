import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FeatureDiscoveryWorkflowTests(unittest.TestCase):
    def assert_discovery_step_uses_checker(self, relative_path: str) -> None:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        marker = "- name: Validate feature discovery"
        self.assertIn(marker, text, f"{relative_path} is missing the discovery step")

        step = text.split(marker, 1)[1]
        next_step = step.find("\n      - name:")
        if next_step >= 0:
            step = step[:next_step]

        self.assertIn("policies/check_feature_discovery.py", step)
        self.assertNotIn("python3 -m behave", step)
        self.assertNotIn("/usr/bin/python3 -m behave", step)
        print(f"workflow feature-discovery contract: 1 workflow checked: {relative_path}")

    def test_nightly_compliance_runs_feature_discovery_checker(self) -> None:
        self.assert_discovery_step_uses_checker(".github/workflows/nightly-compliance.yml")

    def test_ci_runs_feature_discovery_checker(self) -> None:
        self.assert_discovery_step_uses_checker(".github/workflows/ci.yml")


if __name__ == "__main__":
    unittest.main()
