"""Guard the risk-path list against core's risk-paths spec, rules B and C.

core's validator (scripts/lib/risk-paths.mjs, run by `make verify`) checks the
JSON shape only. Rule B (each `why` of an entry at L1 or L2 names 1 category),
rule C (the list and its caller are listed, at L1 or L2 in a version 2 list) and
the version 2 fields (`schema_version`, `default_level`, `level`) are checked
here.
https://github.com/frostyard/core/blob/main/docs/specs/risk-paths.md
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RISK_PATHS = ROOT / ".github/risk-paths.json"
CALLER = ".github/workflows/risk-paths.yml"

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

# core docs/specs/risk-paths.md, the interface table: L1 is the strictest.
LEVELS = ("L1", "L2", "L3", "L4")
REQUIRED_PATHS = (".github/risk-paths.json", CALLER)


def matches(glob: str, path: str) -> bool:
    """True when a glob of this list matches a path (rule A, the forms used here).

    The other rule A forms (`*` and `?` in a segment, brace expansion) are
    checked by the template gate (`checkRequiredPaths` in
    scripts/check-template.mjs); no glob of this list uses them.
    """
    if glob == path or glob == "**":
        return True
    if glob.endswith("/**"):
        prefix = glob[: -len("/**")]
        return path == prefix or path.startswith(prefix + "/")
    return False


class RiskPathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(RISK_PATHS.read_text(encoding="utf-8"))
        self.paths = self.document["paths"]

    def level(self, entry: dict) -> str:
        """The level of 1 entry; a version 1 list reads as every glob at L1."""
        return entry["level"] if self.document["schema_version"] == 2 else "L1"

    def test_schema_version_and_levels(self) -> None:
        version = self.document["schema_version"]
        self.assertIn(version, (1, 2), f"schema_version must be 1 or 2, got {version!r}")
        if version == 2:
            self.assertIn(
                self.document.get("default_level"),
                LEVELS,
                f"default_level must be 1 of {', '.join(LEVELS)}, "
                f"got {self.document.get('default_level')!r}",
            )
            self.assertEqual(
                self.document["default_level"],
                "L3",
                "the grading rule of the spec sets default_level L3, the level of ordinary code",
            )
        else:
            self.assertNotIn(
                "default_level", self.document, "a version 1 list has no default_level"
            )
        for entry in self.paths:
            if version == 2:
                self.assertIn(
                    entry.get("level"),
                    LEVELS,
                    f"{entry['glob']}: level must be 1 of {', '.join(LEVELS)}, "
                    f"got {entry.get('level')!r}",
                )
            else:
                self.assertNotIn("level", entry, f"{entry['glob']}: a version 1 entry has no level")
        print(f"risk-paths levels: {len(self.paths)} entries checked at schema version {version}")

    def test_every_why_at_l1_or_l2_starts_with_a_spec_category(self) -> None:
        self.assertTrue(self.paths, "risk-paths.json lists no paths")
        for entry in self.paths:
            if self.level(entry) not in ("L1", "L2"):
                continue
            category = entry["why"].split(":", 1)[0].strip()
            self.assertIn(
                category,
                CATEGORIES,
                f"{entry['glob']}: why must start with a risk-paths category, got {category!r}",
            )
        print(f"risk-paths categories: {len(self.paths)} entries checked")

    def test_list_and_caller_are_listed(self) -> None:
        self.assertTrue((ROOT / CALLER).is_file(), f"the caller workflow {CALLER} is missing")
        for required in REQUIRED_PATHS:
            globs = [entry["glob"] for entry in self.paths if matches(entry["glob"], required)]
            self.assertTrue(globs, f"no glob of the list matches the required path {required}")
            for entry in self.paths:
                if not matches(entry["glob"], required):
                    continue
                self.assertIn(
                    self.level(entry),
                    ("L1", "L2"),
                    f"{entry['glob']}: a glob that matches {required} must be L1 or L2",
                )


if __name__ == "__main__":
    unittest.main()
