## Background

The current Slack notification for ClaudeChain statistics uses Unicode box-drawing characters (┌─┬─┐, │, └─┴─┘) to render tables. While this works, the resulting output is visually unappealing in Slack because:

1. **Monospace dependency**: The table relies on fixed-width fonts, but Slack doesn't guarantee consistent monospace rendering
2. **Code block ugliness**: Tables are wrapped in triple backticks (```), creating a gray code block that looks out of place in a notification
3. **No native styling**: Inside code blocks, we lose all Slack formatting (bold, links, emojis render as text)
4. **Mobile issues**: Wide tables require horizontal scrolling on mobile devices

## Experiment Results

Tested both Table Block and Section Fields approaches with incoming webhooks on 2026-01-06:

- **Table Block**: Works with webhooks when placed in `attachments[].blocks`. Renders clean tabular data with proper column alignment. However, only supports `raw_text` (no mrkdwn formatting, emojis, or links).

- **Section Fields**: Works with webhooks in top-level `blocks`. Supports rich formatting including progress bars, clickable PR links, emojis, and flexible layouts.

**Decision**: Use Section Fields approach for richer formatting capabilities (progress bars, PR links with age indicators, conditional emojis).

## Target Format

The final Slack message structure:

```json
{
  "text": "ClaudeChain Statistics - Fallback",
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "ClaudeChain Statistics", "emoji": true}
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "📅 2026-01-06  •  Branch: main"}
      ]
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*auth-migration*\n████████░░ 80%"}
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "4/5 merged  •  💰 $0.45"}
      ]
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "• <https://github.com/org/repo/pull/42|#42 Add OAuth support> (2d)"}
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*api-refactor* ✅\n██████████ 100%"}
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "5/5 merged  •  💰 $2.10"}
      ]
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*🏆 Leaderboard*"}
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "🥇 *alice*\n5 merged"},
        {"type": "mrkdwn", "text": "🥈 *bob*\n3 merged"}
      ]
    }
  ]
}
```

### Format Rules

1. **Project header**: `*project-name*` with ✅ only if 100% complete
2. **Progress bar**: Unicode blocks (████░░) with percentage on same line
3. **Stats context**: "X/Y merged • 💰 $cost" in smaller context text
4. **Open PRs**: Bullet list with clickable links, age in days, ⚠️ for stale (5d+)
5. **Completed projects**: No PR list (none open)
6. **Leaderboard**: 2-column fields with medal emojis, merged count only

## Phases

- [x] Phase 1: Experiment with Slack Block Kit in webhooks

Tested both Table Block and Section Fields approaches. Both work with incoming webhooks. Chose Section Fields for richer formatting support.

- [x] Phase 2: Create Block Kit message builder

Created `SlackBlockKitFormatter` class in `src/claudechain/domain/formatters/slack_block_kit_formatter.py` with support for header, context, section, divider blocks, and section fields for leaderboard.

- [x] Phase 3: Implement project progress blocks

Implemented `format_project_blocks` method with project name + ✅, progress bar, stats context, and open PRs list with ⚠️ for stale.

- [x] Phase 4: Implement leaderboard blocks

Implemented `format_leaderboard_blocks` method with medal emojis and 2-column section fields layout.

- [x] Phase 5: Update format_for_slack to output Block Kit JSON

Added `format_for_slack_blocks()` method to `StatisticsReport` that returns Block Kit JSON dict. Updated statistics command to use new method and output JSON for webhooks.

- [x] Phase 6: Update tests

Created `tests/unit/domain/formatters/test_slack_block_kit_formatter.py` with 32 tests covering:
- Block builder functions (header, context, section, divider)
- Progress bar generation
- Project blocks (checkmarks, progress, stats, PR links, warnings)
- Leaderboard blocks (medals, section fields, limits)
- Warnings blocks

Updated `tests/integration/cli/commands/test_statistics.py` with Block Kit JSON verification tests.

- [x] Phase 7: Validation

All 69 tests pass (32 unit + 16 integration + 21 other formatters). Coverage for slack_block_kit_formatter.py: 98.94%
