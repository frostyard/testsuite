# Automated Copilot review application

The `Apply Copilot review feedback` workflow closes the review feedback loop by
handing actionable Copilot code review findings to the Copilot coding agent.
It runs when `copilot-pull-request-reviewer[bot]` submits a review on an open,
non-draft pull request. Maintainers can also run it manually for an open pull
request from the Actions tab.

The workflow checks that the review contains inline findings and posts one
`@copilot` handoff comment per review. The coding agent follows the repository
instructions and [review rubric](review-rubric.md), validates its changes, and
pushes fixes to the pull request branch. A hidden review-ID marker prevents
duplicate handoffs. The workflow does not check out or execute pull request
code.

## Required secret

Create a repository Actions secret named `COPILOT_AGENT_TOKEN`. Use a token
owned by a maintainer who is allowed to invoke the Copilot coding agent and
comment on pull requests. Grant only the repository permissions needed to read
pull requests and create pull request comments.

The workflow fails with an explicit configuration error when the secret is
missing. This avoids a successful-looking run that did not hand feedback to the
agent.

## Manual recovery

If an automatic run failed after Copilot submitted a review, run the workflow
manually and enter the pull request number. It selects the most recent Copilot
review. Reviews without inline findings are left unchanged.
