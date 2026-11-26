import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LintWorkflowTests(unittest.TestCase):
    def lint_step(self, text: str, source: str) -> str:
        marker = re.search(r"(?m)^      - name: Lint Python\s*$", text)
        if marker is None:
            self.fail(f"{source} is missing the Lint Python step")
        step = text[marker.start():]
        boundary = re.search(r"\n(?:      - | {0,5}\S)", step)
        if boundary:
            step = step[:boundary.start()]
        return "\n".join(
            line.rstrip()
            for line in step.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def test_lint_step_requires_exact_uncommented_name(self) -> None:
        fixtures = {
            "commented out": "      #      - name: Lint Python\n        # run: ruff check\n",
            "renamed": "      - name: Lint Python 2\n        run: ruff check\n",
        }
        for case, text in fixtures.items():
            with self.subTest(case=case):
                with self.assertRaisesRegex(AssertionError, "missing the Lint Python step"):
                    self.lint_step(text, case)

    def test_lint_step_stops_at_next_step_or_job(self) -> None:
        step = "      - name: Lint Python\n        run: ruff check"
        fixtures = {
            "next step starts with if": "      - if: always()\n        run: echo Done\n",
            "last step in job": "  next-job:\n    runs-on: ubuntu-latest\n",
        }
        for case, suffix in fixtures.items():
            with self.subTest(case=case):
                self.assertEqual(self.lint_step(f"{step}\n{suffix}", case), step)

    def test_ci_and_nightly_run_same_ruff_correctness_check(self) -> None:
        workflows = (
            ".github/workflows/ci.yml",
            ".github/workflows/nightly-compliance.yml",
        )
        steps = []
        for relative_path in workflows:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            step = self.lint_step(text, relative_path)
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
