"""Guard the risk-path list against core's risk-paths spec, rules B and C.

core's validator (scripts/lib/risk-paths.mjs, run by `make verify`) checks the
JSON shape only. Rule B (each `why` names 1 category) and rule C (the list and
its caller are listed) are checked here.
https://github.com/frostyard/core/blob/main/docs/specs/risk-paths.md
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RISK_PATHS = ROOT / ".github/risk-paths.json"

# core docs/specs/risk-paths.md, rule B. This repository has no governance
# policy with protected-boundary identifiers, so a `why` names a category.
CATEGORIES = (
    "boot chain",
    "signing and keys",
    "update verification",
    "auth",
    "publication",
    "secrets and credentials",
    "rulesets and settings",
    "destructive operations",
    "governance",
)


class RiskPathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = json.loads(RISK_PATHS.read_text(encoding="utf-8"))["paths"]

    def test_every_why_starts_with_a_spec_category(self) -> None:
        self.assertTrue(self.paths, "risk-paths.json lists no paths")
        for entry in self.paths:
            category = entry["why"].split(":", 1)[0].strip()
            self.assertIn(
                category,
                CATEGORIES,
                f"{entry['glob']}: why must start with a risk-paths category, got {category!r}",
            )
        print(f"risk-paths categories: {len(self.paths)} entries checked")

    def test_list_and_caller_are_listed(self) -> None:
        globs = {entry["glob"] for entry in self.paths}
        self.assertIn(".github/risk-paths.json", globs)
        self.assertTrue(
            {".github/workflows/risk-paths.yml", ".github/workflows/**"} & globs,
            "the caller workflow .github/workflows/risk-paths.yml is not listed",
        )


if __name__ == "__main__":
    unittest.main()
