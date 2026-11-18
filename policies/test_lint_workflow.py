import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LintWorkflowTests(unittest.TestCase):
    def lint_step(self, relative_path: str) -> str:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        marker = "      - name: Lint Python"
        self.assertIn(marker, text, f"{relative_path} is missing the Lint Python step")
        step = text[text.index(marker):]
        next_step = re.search(r"\n      - (?:name:|uses:|run:)", step)
        if next_step:
            step = step[:next_step.start()]
        return "\n".join(
            line.rstrip()
            for line in step.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def test_ci_and_nightly_run_same_ruff_correctness_check(self) -> None:
        workflows = (
            ".github/workflows/ci.yml",
            ".github/workflows/nightly-compliance.yml",
        )
        steps = []
        for relative_path in workflows:
            step = self.lint_step(relative_path)
            self.assertRegex(
                step,
                r"(?m)^        uses: astral-sh/ruff-action@[0-9a-fA-F]{40}(?:\s|$)",
                f"{relative_path} must pin ruff-action to a 40-hex SHA",
            )
            self.assertIn("          args: check --select E,F", step, relative_path)
            self.assertRegex(step, r"(?m)^          version: \S+", relative_path)
            steps.append(step)
        self.assertEqual(steps[0], steps[1], "CI and nightly Lint Python steps must match")
        print(f"workflow lint contract: 2 workflows checked: {', '.join(workflows)}")


if __name__ == "__main__":
    unittest.main()
