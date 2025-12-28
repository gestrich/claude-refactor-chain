# Standardize Slack Notifications

## Background

Currently, ClaudeStep has two different patterns for handling Slack notifications:

1. **Main action** (`action.yml`): Accepts `slack_webhook_url` as an input parameter and internally calls the Slack action. Users just pass the webhook URL and the action handles posting.

2. **Statistics action** (`statistics/action.yml`): Does NOT accept a webhook URL input. Instead, it outputs a `slack_message` and expects the workflow to call the Slack action externally using job-level environment variables.

This inconsistency is confusing for users because:
- The same secret (`SLACK_WEBHOOK_URL`) is used differently in different workflows
- Documentation says "weekly statistics notifications will still work" but doesn't explain the workflow must handle Slack posting
- Users might expect the statistics action to work the same way as the main action

**Goal**: Standardize on Option A - have both actions handle Slack internally. This provides a consistent, simpler user experience where they just pass `slack_webhook_url` as an input parameter and the action handles the rest.

## Phases

- [ ] Phase 1: Add slack_webhook_url input to statistics action

Add the `slack_webhook_url` input parameter to `statistics/action.yml` to match the pattern used in the main action.

**Tasks:**
- Add `slack_webhook_url` input to `statistics/action.yml` inputs section (after `working_directory`)
  - Description: 'Slack webhook URL for statistics notifications (optional)'
  - Required: false
  - Default: ''
- Pass the input to the statistics step environment as `SLACK_WEBHOOK_URL: ${{ inputs.slack_webhook_url }}`
- Update the statistics command to read from environment and output as step output (similar to prepare.py:59,151)

**Files to modify:**
- `statistics/action.yml`
- `src/claudestep/cli/commands/statistics.py` (if needed to output the webhook URL)

**Expected outcome:**
- Statistics action accepts `slack_webhook_url` as an input parameter
- The value is available in the statistics step environment
- The value is output as a step output for use in later steps

- [ ] Phase 2: Move Slack posting into statistics action

Move the Slack notification step from the workflow into the statistics action itself, matching the pattern in the main action.

**Tasks:**
- Add a new step in `statistics/action.yml` after the "Generate statistics" step
- Name it "Post to Slack"
- Add condition: `if: steps.stats.outputs.has_statistics == 'true' && steps.stats.outputs.slack_webhook_url != ''`
- Use `slackapi/slack-github-action@v2` with the same webhook-type and payload structure as currently in `claudestep-statistics.yml`
- Use `webhook: ${{ steps.stats.outputs.slack_webhook_url }}` to get the URL from step outputs
- Add `continue-on-error: true` to prevent failures from blocking the workflow

**Files to modify:**
- `statistics/action.yml`

**Expected outcome:**
- Statistics action internally posts to Slack when webhook URL is provided
- Workflow no longer needs to handle Slack posting
- Error handling prevents Slack failures from failing the entire action

- [ ] Phase 3: Update claudestep-statistics.yml workflow

Update the example statistics workflow to pass the webhook URL as an action input instead of using job-level environment variables and manual Slack posting.

**Tasks:**
- Remove the job-level `env:` section with `SLACK_WEBHOOK_URL` (line 21-23)
- Remove the entire "Post to Slack" step (lines 35-71)
- Add `slack_webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}` to the "Generate ClaudeStep Statistics" step inputs (after `days_back`)
- Update the workflow comment at the top to reflect the new pattern:
  - Change "2. Posting results to Slack using the official Slack GitHub Action" to "2. Automatic Slack notifications via action input"
- Update the commented-out project-specific example to use the same pattern (pass webhook as input, remove manual Slack step)

**Files to modify:**
- `.github/workflows/claudestep-statistics.yml`

**Expected outcome:**
- Statistics workflow uses the same pattern as the main action workflow
- Users pass `slack_webhook_url` as an input parameter
- Workflow is simpler - no manual Slack posting required

- [ ] Phase 4: Update documentation

Update README.md and other documentation to reflect the consistent Slack notification pattern across both actions.

**Tasks:**
- Update README.md to explain that both PR notifications and statistics notifications use the same pattern
- Update the note at line 127 to clarify that `slack_webhook_url` must be passed as an action input for both the main action and statistics action
- Consider adding a dedicated "Slack Notifications" section that explains:
  - How to get a Slack webhook URL
  - How to add it as a GitHub secret
  - How to pass it to both actions
  - What notifications you'll receive (PR creation + statistics)
- Update any references to the statistics workflow pattern

**Files to modify:**
- `README.md`

**Expected outcome:**
- Documentation clearly explains the consistent pattern
- Users understand they use the same approach for both actions
- No confusion about different patterns for different notifications

- [ ] Phase 5: Update architecture documentation

Update architecture documentation to reflect the standardized Slack notification approach.

**Tasks:**
- Check if there are any architecture docs in `docs/architecture/` that mention Slack notifications
- Update them to describe the consistent input-based pattern
- Document the flow: input parameter → env variable → step output → Slack action parameter
- Remove any references to the old workflow-level pattern for statistics

**Files to check/modify:**
- `docs/architecture/*.md` (if they mention Slack)
- `docs/completed/*.md` (if any mention the old statistics pattern)

**Expected outcome:**
- Architecture documentation is accurate and up-to-date
- Future contributors understand the standardized approach

- [ ] Phase 6: Validation

Validate that both Slack notification types work correctly with the new consistent pattern.

**Testing approach:**

1. **Manual testing** (preferred for this workflow-based change):
   - Test main action Slack notifications:
     - Trigger a ClaudeStep run with `slack_webhook_url` input
     - Verify PR creation notification is posted to Slack
   - Test statistics action Slack notifications:
     - Trigger the statistics workflow with `slack_webhook_url` input
     - Verify statistics report is posted to Slack
   - Test without webhook URL:
     - Run both actions without `slack_webhook_url`
     - Verify they complete successfully without errors
     - Verify no Slack notifications are sent

2. **Code review**:
   - Verify the patterns are identical in both `action.yml` and `statistics/action.yml`
   - Verify documentation accurately reflects the implementation
   - Check that the example workflow in `claudestep-statistics.yml` follows best practices

**Success criteria:**
- Both actions use the same `slack_webhook_url` input parameter pattern
- Both actions internally post to Slack when the webhook URL is provided
- Both actions gracefully handle missing webhook URLs
- Documentation is clear and consistent
- No workflow changes required for existing users (backwards compatible)
