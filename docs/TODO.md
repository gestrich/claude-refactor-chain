# TODO


## V1

- [ ] **Trigger action off of closed, not just merged**

Our linked project at /Users/bill/Developer/personal/claude-step-demo triggers off merged PRs. But we need to assume PRs may be closed without merging too. Note this may trigger the same PR to be opened again so we may want to advise against closing PRs and instead updating the markdown to remove that step if not needed and merge that change first before closing the PR to avoid a cycle of it re-opening.

- [ ] **Secure Secrets**

- Confirm secure approach for Claude token Actions
- Confirm secure approach for webhooks (secrets?)

- [ ] **Cost Control**

Explore how to avoid runaway costs from either jobs taking to long or too many PRs opening.

- [ ] **Record video walkthrough**

Create "ClaudeStep" tutorial video.

- [ ] **Write blog post**

Written guide explaining the approach.

## V2

- [ ] **Local Build Script**

Fetch open PRs and build locally on a schedule. Ready to run when you sit down to review.

- [ ] **UI Automation Screenshots**

Capture screenshots showing the result. Visual verification without manual testing.

- [ ] Support additional claude mentions in PR

Use Claude Code mentions to update the PR