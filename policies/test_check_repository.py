import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from policies.check_repository import (
    GlobRequirement,
    PolicyConfigurationError,
    RepositoryPolicy,
    evaluate_policy,
    load_policy,
    main,
)


class RepositoryPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.policy = RepositoryPolicy(
            required_paths=("README.md",),
            required_globs=(GlobRequirement("tests/**/*.feature", 1),),
        )

    def test_policy_passes_when_requirements_are_present(self) -> None:
        (self.root / "README.md").touch()
        feature = self.root / "tests" / "smoke" / "boot.feature"
        feature.parent.mkdir(parents=True)
        feature.touch()

        self.assertEqual(evaluate_policy(self.root, self.policy), [])

    def test_policy_reports_all_missing_requirements(self) -> None:
        self.assertEqual(
            evaluate_policy(self.root, self.policy),
            [
                "required path is missing: README.md",
                "tests/**/*.feature matched 0 files; minimum is 1",
            ],
        )

    def test_load_policy_rejects_paths_outside_repository(self) -> None:
        policy_path = self.root / "repository.json"
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "required_paths": ["../credential"],
                    "required_globs": [],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(PolicyConfigurationError, "must stay within"):
            load_policy(policy_path)

    def test_main_returns_one_for_policy_violations(self) -> None:
        policy_path = self.root / "repository.json"
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "required_paths": ["README.md"],
                    "required_globs": [],
                }
            ),
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as stderr:
            result = main(["--root", str(self.root), "--policy", str(policy_path)])

        self.assertEqual(result, 1)
        self.assertIn("required path is missing", stderr.getvalue())

    def test_main_returns_two_for_invalid_policy(self) -> None:
        policy_path = self.root / "repository.json"
        policy_path.write_text("[]", encoding="utf-8")

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as stderr:
            result = main(["--root", str(self.root), "--policy", str(policy_path)])

        self.assertEqual(result, 2)
        self.assertIn("Policy configuration error", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
