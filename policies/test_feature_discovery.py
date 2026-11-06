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
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertTrue(
            any(
                line.strip().startswith(("- run: make ci", "run: make ci"))
                for line in workflow.splitlines()
            ),
            ".github/workflows/ci.yml has no `make ci` step",
        )

        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        recipe = self.recipe(makefile, "verify-python")
        self.assertIn("policies/check_feature_discovery.py tests/smoke/features/", recipe)
        self.assertNotIn("-m behave", recipe)
        self.assertIn("verify-python", self.prerequisites(makefile, "verify"))
        self.assertIn("verify", self.prerequisites(makefile, "ci"))
        print(
            "make gate feature-discovery contract: 2 files checked: "
            ".github/workflows/ci.yml, Makefile"
        )

    def recipe(self, makefile: str, target: str) -> str:
        lines = makefile.splitlines()
        start = lines.index(f"{target}:") + 1
        recipe = []
        for line in lines[start:]:
            if not line.startswith("\t"):
                break
            recipe.append(line)
        self.assertTrue(recipe, f"Makefile target {target} has no recipe")
        return "\n".join(recipe)

    def prerequisites(self, makefile: str, target: str) -> list[str]:
        lines = [line for line in makefile.splitlines() if line.startswith(f"{target}:")]
        self.assertEqual(len(lines), 1, f"Makefile must declare the {target} target once")
        return lines[0].split(":", 1)[1].split()


if __name__ == "__main__":
    unittest.main()
