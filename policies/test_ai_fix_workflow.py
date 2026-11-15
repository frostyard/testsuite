"""Guard the AI fix workflow's Copilot assignment secret name.

core ADR-0020 names `COPILOT_ASSIGNMENT_TOKEN` as the one canonical secret for
AI automation and allows no aliases: the old spellings `COPILOT_AGENT_TOKEN`
and `COPILOT_ASSIGN_PAT` must not be used. A missing secret fails the run with
`COPILOT_ASSIGNMENT_TOKEN is not configured`, so it never skips silently.
`make verify` runs this test with the policy unittest suite.
https://github.com/frostyard/core/blob/main/docs/adr/0020-ai-automation-trust-boundaries.md
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ai-fix-requested.yml"
DOCUMENTATION = ROOT / "docs/ai-fix-workflow.md"

CANONICAL = "COPILOT_ASSIGNMENT_TOKEN"
LEGACY_NAMES = ("COPILOT_AGENT_TOKEN", "COPILOT_ASSIGN_PAT")
ADR_0020 = (
    "https://github.com/frostyard/core/blob/main/docs/adr/0020-ai-automation-trust-boundaries.md"
)


class AiFixWorkflowTests(unittest.TestCase):
    def test_workflow_uses_the_canonical_assignment_secret(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"the workflow {WORKFLOW} is missing")
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertEqual(
            workflow.count(f"secrets.{CANONICAL}"),
            1,
            f"the workflow must read secrets.{CANONICAL} exactly 1 time",
        )
        self.assertIn(
            f"GH_TOKEN: ${{{{ secrets.{CANONICAL} }}}}",
            workflow,
            f"the job env must set GH_TOKEN from secrets.{CANONICAL}",
        )
        self.assertIn(
            f"{CANONICAL} is not configured",
            workflow,
            "a missing secret must fail the run with a visible error",
        )
        self.assertNotIn("github.token", workflow, "the default token cannot start the agent")
        self.assertNotIn(
            "secrets.GITHUB_TOKEN", workflow, "the default token cannot start the agent"
        )

        for legacy_name in LEGACY_NAMES:
            self.assertNotIn(
                legacy_name, workflow, f"the workflow uses the legacy name {legacy_name}"
            )

    def test_documentation_names_the_canonical_secret(self) -> None:
        self.assertTrue(DOCUMENTATION.is_file(), f"the document {DOCUMENTATION} is missing")
        documentation = DOCUMENTATION.read_text(encoding="utf-8")

        self.assertIn(
            f"named `{CANONICAL}`",
            documentation,
            f"the setup steps must store the secret as {CANONICAL}",
        )
        self.assertIn(ADR_0020, documentation, "the document must cite core ADR-0020")
        self.assertNotIn(
            "named `COPILOT_AGENT_TOKEN`",
            documentation,
            "the setup steps must not store the secret under the legacy name",
        )

        # A legacy name may appear only where the document forbids it as an alias.
        alias_paragraphs = [
            paragraph
            for paragraph in documentation.split("\n\n")
            if any(legacy_name in paragraph for legacy_name in LEGACY_NAMES)
        ]
        self.assertEqual(
            len(alias_paragraphs),
            1,
            "exactly 1 paragraph names a legacy spelling, the alias rule",
        )
        alias_paragraph = alias_paragraphs[0]
        self.assertIn("alias", alias_paragraph, "the paragraph must forbid aliases")
        self.assertIn(
            f"`{CANONICAL} is not configured`",
            alias_paragraph,
            "the paragraph must name the failure of a missing secret",
        )
        for legacy_name in LEGACY_NAMES:
            self.assertIn(
                f"`{legacy_name}`",
                alias_paragraph,
                f"the paragraph must name the old spelling {legacy_name} as forbidden",
            )

    def test_no_legacy_secret_name_in_workflows_or_docs(self) -> None:
        workflows = [
            *sorted((ROOT / ".github/workflows").glob("*.yml")),
            *sorted((ROOT / ".github/workflows").glob("*.yaml")),
        ]
        docs = [
            path
            for path in sorted((ROOT / "docs").rglob("*.md"))
            if path != DOCUMENTATION  # checked paragraph by paragraph above
        ]
        searchable = [*workflows, *docs]
        self.assertIn(WORKFLOW, workflows, f"{WORKFLOW} is not in the workflow scan")
        self.assertGreater(len(docs), 1, "the doc scan found no document")

        for legacy_name in LEGACY_NAMES:
            for path in searchable:
                self.assertNotIn(legacy_name, path.read_text(encoding="utf-8"), f"{path}")


if __name__ == "__main__":
    unittest.main()
