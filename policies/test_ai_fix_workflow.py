from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ai-fix-requested.yml"
DOCUMENTATION = ROOT / "docs/ai-fix-workflow.md"


class AiFixWorkflowTests(unittest.TestCase):
    def test_workflow_requires_user_token_and_guards_automatic_events(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("GH_TOKEN: ${{ secrets.COPILOT_AGENT_TOKEN }}", workflow)
        self.assertNotIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertIn('id: credentials', workflow)
        self.assertIn(
            'if [[ "$GITHUB_EVENT_NAME" == "workflow_dispatch" ]]; then',
            workflow,
        )
        self.assertIn(
            "::warning title=Copilot assignment skipped::", workflow
        )
        self.assertIn(
            'echo "available=false" >>"$GITHUB_OUTPUT"', workflow
        )
        self.assertIn(
            "if: steps.credentials.outputs.available == 'true'", workflow
        )

    def test_documentation_explains_setup_and_recovery(self) -> None:
        documentation = " ".join(
            DOCUMENTATION.read_text(encoding="utf-8").split()
        )

        for required in (
            "user-to-server token",
            "COPILOT_AGENT_TOKEN",
            "## Missing-secret behavior",
            "records a warning and job summary",
            "manual replay still fails",
            "administrator configures the secret",
        ):
            self.assertIn(required, documentation)


if __name__ == "__main__":
    unittest.main()
