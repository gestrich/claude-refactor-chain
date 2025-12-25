# ClaudeStep Action

Automate code refactoring with AI using Claude Code. This GitHub Action creates incremental pull requests for systematic codebase improvements, making large-scale refactoring manageable and continuous.

## Features

- 🤖 **AI-Powered Refactoring** - Uses Claude Code to perform refactoring tasks
- 📋 **Checklist-Driven** - Works through tasks in your spec.md file systematically
- 👥 **Multi-Reviewer Support** - Distributes PRs across team members
- 🔄 **Multiple Trigger Modes** - Scheduled, manual, or automatic on PR merge
- 📊 **Progress Tracking** - Track completed vs remaining tasks
- ⚡ **Incremental PRs** - One small PR at a time for easier review

## Quick Start

### 1. Create Your Refactor Project

Create a directory structure in your repository:

```
/refactor
  /swift-migration/
    configuration.json
    spec.md
    pr-template.md (optional)
```

**configuration.json**:
```json
{
  "label": "swift-migration",
  "branchPrefix": "refactor/swift-migration",
  "reviewers": [
    {
      "username": "alice",
      "maxOpenPRs": 1
    },
    {
      "username": "bob",
      "maxOpenPRs": 1
    }
  ]
}
```

**spec.md**:
```markdown
# Swift Migration

Convert Objective-C files to Swift following these guidelines:

- Use Swift naming conventions
- Replace NS types with Swift equivalents
- Use guard statements instead of nested if-let

## Checklist

- [ ] Convert UserManager.m to Swift
- [ ] Convert NetworkClient.m to Swift
- [ ] Convert DataStore.m to Swift
```

### 2. Set Up GitHub Action

Create `.github/workflows/continuous-refactor.yml`:

```yaml
name: ClaudeStep

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:
    inputs:
      project:
        description: 'Project name'
        required: true
        default: 'swift-migration'

permissions:
  contents: write
  pull-requests: write
  actions: read

jobs:
  refactor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: gestrich/claude-step@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          project_name: ${{ github.event.inputs.project || 'swift-migration' }}
```

### 3. Configure Repository

1. **Add API Key**: Go to Settings > Secrets and add `ANTHROPIC_API_KEY`
2. **Enable PR Creation**: Settings > Actions > General > Allow GitHub Actions to create PRs
3. **Create Label**: Run `gh label create "swift-migration" --color "0E8A16"`

### 4. Run and Review

- Trigger manually via Actions tab or wait for scheduled run
- Review and merge PRs as they're created
- Update spec.md instructions if needed to improve accuracy

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | ✅ | - | Anthropic API key for Claude Code |
| `github_token` | ✅ | `${{ github.token }}` | GitHub token for PR operations |
| `project_name` | ✅ | - | Project folder name under `/refactor` |
| `config_path` | ❌ | `refactor/{project}/configuration.json` | Custom config path |
| `spec_path` | ❌ | `refactor/{project}/spec.md` | Custom spec file path |
| `pr_template_path` | ❌ | `refactor/{project}/pr-template.md` | Custom PR template path |
| `claude_model` | ❌ | `claude-sonnet-4-5` | Claude model to use |
| `claude_allowed_tools` | ❌ | `Write,Read,Bash,Edit` | Tools Claude can use |
| `base_branch` | ❌ | `main` | Base branch for PRs |
| `working_directory` | ❌ | `.` | Working directory |

## Outputs

| Output | Description |
|--------|-------------|
| `pr_number` | Number of created PR (empty if none) |
| `pr_url` | URL of created PR (empty if none) |
| `reviewer` | Assigned reviewer username |
| `task_completed` | Task description completed |
| `has_capacity` | Whether reviewer had capacity |
| `all_tasks_done` | Whether all tasks are complete |

## Configuration

### configuration.json

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | ✅ | GitHub label for PRs |
| `branchPrefix` | string | ✅ | Prefix for branch names |
| `reviewers` | array | ✅ | List of reviewers with capacity |

**Reviewers** array items:
- `username` (string): GitHub username
- `maxOpenPRs` (number): Max open PRs per reviewer

### spec.md Format

The spec file combines instructions and checklist:

```markdown
# Your Instructions

[Detailed refactoring guidelines, examples, patterns to follow]

## Checklist

- [ ] Task 1
- [ ] Task 2
- [x] Completed task
```

**Requirements:**
- Must contain at least one `- [ ]` or `- [x]` item
- Checklist items can appear anywhere in the file
- The entire file content is provided to Claude as context

### pr-template.md (Optional)

Template for PR descriptions with `{{TASK_DESCRIPTION}}` placeholder:

```markdown
## Task
{{TASK_DESCRIPTION}}

## Testing Checklist
- [ ] Code compiles
- [ ] Tests pass
- [ ] Follows project conventions
```

## Trigger Modes

### Scheduled (Recommended for Getting Started)

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
```

- Predictable, steady pace
- One PR per day per reviewer
- Easy to manage initially

### Manual Dispatch

```yaml
on:
  workflow_dispatch:
    inputs:
      project:
        description: 'Project name'
        required: true
```

- On-demand PR creation
- Useful for testing and demos
- Allows project selection

### Automatic (PR Merge)

```yaml
on:
  pull_request:
    types: [closed]

jobs:
  refactor:
    if: github.event.pull_request.merged == true
    # ...
```

- Creates next PR immediately when one merges
- Fastest iteration speed
- Best for active refactoring periods

## Examples

### Basic: Single Project, Scheduled

See [examples/basic/workflow.yml](examples/basic/workflow.yml)

### Advanced: Multi-Project with All Triggers

See [examples/advanced/workflow.yml](examples/advanced/workflow.yml)

## Best Practices

### Start Small
- Begin with `maxOpenPRs: 1` per reviewer
- Use scheduled trigger initially
- Scale up as confidence grows

### Write Good Instructions
- Include before/after examples in spec.md
- Document edge cases and exceptions
- Update instructions when you fix Claude's mistakes

### Review Process
- Treat AI-generated PRs like any other code review
- Fix issues directly in the PR when possible
- Update spec.md in the same PR to improve future output

### Team Coordination
- Align on review thoroughness per refactor type
- Define when QA needs to be involved
- Integrate into existing review cadence

## Troubleshooting

### No PRs Being Created

**Check:**
1. Are all reviewers at capacity? (Check workflow summary)
2. Are all tasks completed? (Check spec.md)
3. Do you have the label created? (Run `gh label list`)

### PR Creation Fails

**Common causes:**
- Missing `ANTHROPIC_API_KEY` secret
- Workflow doesn't have PR creation permissions
- Branch already exists (shouldn't happen with date prefix)

### Claude Makes Mistakes

**Solutions:**
1. Add more detailed instructions to spec.md
2. Include specific examples of what to do/avoid
3. Consider starting with one PR to set the pattern
4. Update instructions in the same PR when you fix issues

### Reviewer Assignment Not Working

The action uses artifacts to track PR assignments. If assignment seems wrong:
1. Check that artifact uploads are succeeding
2. Verify label matches between config and actual PRs
3. Wait for one full workflow run to establish state

## How It Works

1. **Check Capacity**: Finds first reviewer under their `maxOpenPRs` limit
2. **Find Task**: Scans spec.md for first unchecked `- [ ]` item
3. **Create Branch**: Names branch with format `YYYY-MM-{project}-{index}`
4. **Run Claude**: Provides entire spec.md as context for the task
5. **Create PR**: Assigns to reviewer, applies label, uses template
6. **Track Progress**: Uploads artifact with task metadata

## Security

- API keys stored as GitHub secrets (never in logs)
- Uses repository GITHUB_TOKEN with minimal permissions
- No external services beyond Anthropic API
- All code runs in GitHub Actions sandbox

## Limitations

- Requires Anthropic API key (costs apply based on usage)
- Claude Code action requires specific Claude models
- Maximum 90-day artifact retention for tracking
- GitHub API rate limits apply (rarely hit in practice)

## Contributing

Contributions welcome! Please:
1. Open an issue to discuss changes
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## License

MIT License - see LICENSE file

## Support

- 📚 [Full Documentation](docs/CONFIGURATION.md)
- 🐛 [Report Issues](https://github.com/gestrich/claude-step/issues)
- 💬 [Discussions](https://github.com/gestrich/claude-step/discussions)

## Credits

Created by [gestrich](https://github.com/gestrich)

Built with [Claude Code](https://github.com/anthropics/claude-code-action) by Anthropic
