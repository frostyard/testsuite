from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/claude-code-review.yml"
DOCUMENTATION = ROOT / "docs/claude-code-review.md"
ACTION_SHA = "6b082c41935b4c8a3b8b0ef85ba4ba4d9eeb8975"
ALLOWED_TOOLS = (
    "mcp__github_inline_comment__create_inline_comment,"
    "Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)"
)


class ClaudeReviewWorkflowTests(unittest.TestCase):
    def test_workflow_is_pinned_and_least_privilege(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("  pull_request:\n", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertIn("permissions: {}", workflow)
        self.assertIn("github.event.pull_request.draft == false", workflow)
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            workflow,
        )
        self.assertIn("timeout-minutes: 10", workflow)

        self.assertIn("      contents: read", workflow)
        self.assertIn("      pull-requests: write", workflow)
        for forbidden in (
            "contents: write",
            "issues: write",
            "actions: write",
            "id-token: write",
        ):
            self.assertNotIn(forbidden, workflow)

        self.assertIn("persist-credentials: false", workflow)
        self.assertIn(f"anthropics/claude-code-action@{ACTION_SHA}", workflow)
        self.assertIsNone(re.search(r"anthropics/claude-code-action@v", workflow))
        self.assertIn(
            "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}", workflow
        )
        self.assertIn(f'--allowedTools "{ALLOWED_TOOLS}"', workflow)
        self.assertNotIn("        run:", workflow)

    def test_documentation_records_secret_and_trust_boundary(self) -> None:
        documentation = " ".join(
            DOCUMENTATION.read_text(encoding="utf-8").split()
        )

        for required in (
            "ANTHROPIC_API_KEY",
            "Fork pull requests are deliberately skipped",
            "comments are advisory and require human verification",
            "contents: read",
            "pull-requests: write",
            "pull_request_target",
            "cannot change contents",
        ):
            self.assertIn(required, documentation)


if __name__ == "__main__":
    unittest.main()
