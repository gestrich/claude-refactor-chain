# Quick Start Guide

Get up and running with ClaudeStep in 5 minutes.

## Prerequisites

- GitHub repository with code to refactor
- Anthropic API key ([get one here](https://console.anthropic.com))

## Step 1: Create Refactor Project (2 min)

Create this directory structure in your repo:

```bash
mkdir -p refactor/my-refactor
```

Create `refactor/my-refactor/configuration.json`:

```json
{
  "label": "ai-refactor",
  "branchPrefix": "refactor/ai-refactor",
  "reviewers": [
    {
      "username": "YOUR_GITHUB_USERNAME",
      "maxOpenPRs": 1
    }
  ]
}
```

Create `refactor/my-refactor/spec.md`:

```markdown
# My Refactoring Project

Describe what you want to refactor and how to do it.

Include:
- Specific patterns to follow
- Before/after code examples
- Any edge cases or special handling

## Checklist

- [ ] First task to refactor
- [ ] Second task to refactor
- [ ] Third task to refactor
```

## Step 2: Configure GitHub (1 min)

### Add API Key

1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: (paste your Anthropic API key)
5. Click "Add secret"

### Enable PR Creation

1. Go to Settings > Actions > General
2. Scroll to "Workflow permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"
4. Click "Save"

### Create Label

```bash
gh label create "ai-refactor" --color "0E8A16"
```

## Step 3: Add Workflow (1 min)

Create `.github/workflows/ai-refactor.yml`:

```yaml
name: ClaudeStep

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:     # Allow manual trigger

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
          project_name: 'my-refactor'
```

## Step 4: Run & Test (1 min)

### Manual Test

1. Go to Actions tab in GitHub
2. Click "ClaudeStep" workflow
3. Click "Run workflow"
4. Wait ~2-5 minutes
5. Check for new PR!

### What to Expect

- ✅ Workflow runs successfully
- ✅ New branch created: `2025-01-my-refactor-1`
- ✅ PR created with label "ai-refactor"
- ✅ PR assigned to you
- ✅ First task from spec.md is completed

## Step 5: Review & Iterate

### Review the PR

1. Check the code changes
2. Verify it follows your spec
3. Make any needed fixes
4. **Important**: If you fix issues, update spec.md in the same PR to improve future PRs

### Merge

1. When satisfied, merge the PR
2. Next run (tomorrow or manual) will create PR for next task

### Improve

As you review PRs, update spec.md with:
- More specific instructions
- Edge cases you discover
- Examples of good/bad patterns

The instructions will improve over time!

## Next Steps

### Scale Up

Once comfortable:

```json
{
  "reviewers": [
    {
      "username": "alice",
      "maxOpenPRs": 2  // ← Increase capacity
    },
    {
      "username": "bob",   // ← Add more reviewers
      "maxOpenPRs": 1
    }
  ]
}
```

### Add PR Merge Trigger

For faster iteration:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:
  pull_request:  # ← Add this
    types: [closed]

jobs:
  refactor:
    # Only run on merged PRs
    if: github.event_name != 'pull_request' || github.event.pull_request.merged == true
    # ... rest of job
```

Now when you merge a PR, it immediately creates the next one!

### Multiple Projects

Create additional refactor projects:

```
refactor/
├── swift-migration/
│   ├── configuration.json
│   └── spec.md
├── typescript-conversion/
│   ├── configuration.json
│   └── spec.md
└── api-refactor/
    ├── configuration.json
    └── spec.md
```

Run different projects on different schedules or manually.

## Troubleshooting

### No PR Created

**Check workflow summary** - it shows:
- Reviewer capacity (are all reviewers at max?)
- Available tasks (are all tasks complete or in progress?)

**Common fixes:**
- Increase `maxOpenPRs` if at capacity
- Add more unchecked tasks to spec.md
- Verify label exists and matches config

### Bad PR Quality

**Update spec.md** with:
- More detailed instructions
- Concrete before/after examples
- Common mistakes to avoid

The more context you provide, the better Claude performs.

### Permission Errors

**Verify:**
- `ANTHROPIC_API_KEY` secret exists
- Workflow has PR creation permission enabled
- You have write access to the repo

## Tips for Success

1. **Start with clear, simple tasks**
   ```markdown
   - [ ] Convert UserService.js to TypeScript
   ```
   Not: `- [ ] Fix the auth stuff`

2. **Provide examples in spec.md**
   - Show before/after code
   - Document patterns to follow
   - Explain edge cases

3. **Review thoroughly at first**
   - First few PRs may need guidance
   - Update spec.md when you fix issues
   - Quality improves quickly with good instructions

4. **One PR at a time initially**
   - Set `maxOpenPRs: 1`
   - Increase after you're confident
   - Easier to iterate on instructions

5. **Merge regularly**
   - Don't let PRs pile up
   - Keep momentum going
   - Batch review if needed

## Full Documentation

- [Complete README](ACTION_README.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Examples](examples/)

## Need Help?

- Check the [Troubleshooting section](ACTION_README.md#troubleshooting)
- Review [examples](examples/) for reference
- Open an issue if stuck

Happy refactoring! 🚀
