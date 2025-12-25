# Plan: Convert to Reusable GitHub Action

## Executive Summary

Convert the ClaudeStep system from a repository-specific workflow into a reusable GitHub Action that can be easily integrated into any repository. This will enable other teams to adopt the continuous refactoring approach without copying/modifying workflow files.

## 1. Action Architecture

### Recommended Type: **Composite Action**

**Rationale:**
- **Composite actions** are ideal for this use case because:
  - Can execute multiple steps (setup Python, run scripts, call other actions)
  - Supports calling existing actions (anthropics/claude-code-action@v1)
  - No need to build/publish Docker images or npm packages
  - Easier to maintain and iterate on
  - Users can see exactly what steps run (transparency)

**Alternatives Considered:**
- **Docker action**: Overkill for our needs, slower startup, requires container registry
- **JavaScript/TypeScript action**: Would require rewriting Python logic, additional build step

### Structure

```
claude-step/
├── action.yml                    # Action metadata & interface
├── README.md                      # Usage documentation
├── LICENSE                        # MIT or Apache 2.0
├── .github/
│   └── workflows/
│       ├── test.yml              # CI testing of the action
│       └── release.yml           # Automated releases
├── scripts/
│   ├── refactor_chain.py         # Core Python logic (moved here)
│   └── requirements.txt          # Python dependencies (if any)
├── examples/
│   ├── basic/                    # Simple example usage
│   │   └── workflow.yml
│   └── advanced/                 # Advanced multi-project example
│       └── workflow.yml
└── docs/
    ├── CONFIGURATION.md          # Configuration guide
    ├── TROUBLESHOOTING.md        # Common issues
    └── ARCHITECTURE.md           # How it works
```

## 2. Action Interface (action.yml)

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | ✅ | - | Anthropic API key for Claude Code |
| `github_token` | ✅ | `${{ github.token }}` | GitHub token for PR creation |
| `project_name` | ✅ | - | Project folder name under `/refactor` |
| `config_path` | ❌ | `refactor/{project}/configuration.json` | Path to config file |
| `spec_path` | ❌ | `refactor/{project}/spec.md` | Path to spec file |
| `pr_template_path` | ❌ | `refactor/{project}/pr-template.md` | Path to PR template |
| `claude_model` | ❌ | `claude-sonnet-4-5` | Claude model to use |
| `claude_allowed_tools` | ❌ | `Write,Read,Bash,Edit` | Tools Claude can use |
| `base_branch` | ❌ | `main` | Base branch for PRs |
| `working_directory` | ❌ | `.` | Working directory for the action |

### Outputs

| Output | Description |
|--------|-------------|
| `pr_number` | Number of created PR (empty if none created) |
| `pr_url` | URL of created PR (empty if none created) |
| `reviewer` | Assigned reviewer username |
| `task_completed` | Task description that was completed |
| `has_capacity` | Whether a reviewer had capacity (true/false) |
| `all_tasks_done` | Whether all tasks are complete (true/false) |

### Permissions Required

Users must grant these permissions in their workflow:

```yaml
permissions:
  contents: write       # Push branches
  pull-requests: write  # Create PRs
  actions: read         # Read workflow artifacts
```

## 3. Configuration Schema

### configuration.json

Create a JSON schema file for validation:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["label", "branchPrefix", "reviewers"],
  "properties": {
    "label": {
      "type": "string",
      "description": "GitHub label to apply to PRs",
      "pattern": "^[a-z0-9-]+$"
    },
    "branchPrefix": {
      "type": "string",
      "description": "Prefix for branch names",
      "pattern": "^[a-z0-9/-]+$"
    },
    "reviewers": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["username", "maxOpenPRs"],
        "properties": {
          "username": {
            "type": "string",
            "description": "GitHub username"
          },
          "maxOpenPRs": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Maximum open PRs for this reviewer"
          }
        }
      }
    },
    "branchFormat": {
      "type": "string",
      "description": "Branch name format template",
      "default": "{date}-{project}-{index}"
    },
    "commitMessageFormat": {
      "type": "string",
      "description": "Commit message template",
      "default": "Complete task: {task}"
    }
  }
}
```

## 4. Key Design Decisions

### 4.1 Monolithic vs Modular

**Decision: Monolithic composite action**

Provide a single action that handles the entire flow. Don't split into separate actions (check-capacity, find-task, create-pr) because:
- Simpler for users (one action to configure)
- Internal steps can be optimized/reorganized without breaking changes
- Reduces complexity of passing data between actions

### 4.2 Project Structure

**Decision: Support the `/refactor/{project}` convention**

- Keep the current convention as the default
- Allow users to override paths via inputs for flexibility
- Document the recommended structure in README

### 4.3 Trigger Modes

**Decision: Support all three modes**

The action should work with:
1. **Schedule trigger**: `cron: '0 9 * * *'`
2. **Manual trigger**: `workflow_dispatch` with project input
3. **Automatic trigger**: `pull_request.merged` when PR has matching label

Users configure the trigger in their workflow file (not in the action).

### 4.4 Error Handling

**Decision: Fail gracefully with clear messages**

- If no capacity: Exit successfully with notice (not error)
- If no tasks: Exit successfully with notice
- If config invalid: Exit with error and detailed message
- If Claude fails: Exit with error and preserve logs

### 4.5 Backwards Compatibility

**Decision: Support config evolution**

- Use semantic versioning (v1.x.x)
- Maintain backwards compatibility within major versions
- Document breaking changes clearly
- Provide migration guides for major version bumps

## 5. Implementation Plan

### Phase 1: Core Action Setup

1. **Create new repository**: `claude-step`
   - Initialize with LICENSE (MIT recommended)
   - Create basic README with placeholder content
   - Set up branch protection for `main`

2. **Create action.yml**
   - Define all inputs/outputs
   - Set action name, description, branding
   - Implement composite run steps

3. **Port Python script**
   - Move `refactor_chain.py` to `scripts/`
   - Ensure no hardcoded paths
   - Make paths configurable via environment variables
   - Add input validation

### Phase 2: Documentation

4. **Write comprehensive README**
   - Quick start example
   - Full configuration reference
   - Multiple usage examples
   - Troubleshooting section
   - Link to examples/ directory

5. **Create example workflows**
   - Basic example (single project, scheduled)
   - Advanced example (multiple projects, PR trigger)
   - Migration guide from current setup

6. **Write supporting docs**
   - CONFIGURATION.md: Deep dive on all options
   - TROUBLESHOOTING.md: Common issues and solutions
   - ARCHITECTURE.md: How the system works internally

### Phase 3: Testing & CI

7. **Set up testing workflow**
   - Test action with different trigger types
   - Validate configuration parsing
   - Test capacity checking logic
   - Mock Claude Code execution for tests

8. **Add release automation**
   - Semantic release workflow
   - Automated changelog generation
   - Update major version tags (v1, v2) automatically

### Phase 4: Publishing

9. **Prepare for publication**
   - Complete all documentation
   - Add action branding (icon, color)
   - Create initial release (v1.0.0)
   - Test with real repository

10. **Publish to GitHub Marketplace**
    - Submit action for listing
    - Add relevant tags/categories
    - Monitor initial user feedback

## 6. Usage Example

Here's how users would integrate the action:

### Minimal Example

```yaml
# .github/workflows/continuous-refactor.yml
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

### Advanced Example (Multi-Trigger)

```yaml
name: ClaudeStep

on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:
    inputs:
      project:
        description: 'Project name'
        required: true
  pull_request:
    types: [closed]

permissions:
  contents: write
  pull-requests: write
  actions: read

jobs:
  refactor:
    runs-on: ubuntu-latest
    # Only run on merged PRs or non-PR triggers
    if: github.event_name != 'pull_request' || github.event.pull_request.merged == true
    steps:
      - uses: actions/checkout@v4

      - name: Determine project
        id: project
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "name=${{ github.event.inputs.project }}" >> $GITHUB_OUTPUT
          elif [ "${{ github.event_name }}" = "pull_request" ]; then
            # Extract from branch name: 2025-01-swift-migration-5
            PROJECT=$(echo "${{ github.head_ref }}" | sed -E 's/^[0-9]{4}-[0-9]{2}-([^-]+)-[0-9]+$/\1/')
            echo "name=$PROJECT" >> $GITHUB_OUTPUT
          else
            echo "name=swift-migration" >> $GITHUB_OUTPUT
          fi

      - uses: gestrich/claude-step@v1
        id: refactor
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          project_name: ${{ steps.project.outputs.name }}
          claude_model: claude-sonnet-4-5

      - name: Summary
        if: steps.refactor.outputs.pr_number
        run: |
          echo "✅ Created PR #${{ steps.refactor.outputs.pr_number }}"
          echo "📋 Task: ${{ steps.refactor.outputs.task_completed }}"
          echo "👤 Reviewer: ${{ steps.refactor.outputs.reviewer }}"
```

## 7. Migration Guide

For users of the current repository-based approach:

### Step 1: Create Action Repository

```bash
# Create new repo
gh repo create claude-step --public
cd claude-step

# Copy action files
cp -r ../claude-refactor-chain/action.yml .
cp -r ../claude-refactor-chain/scripts .
cp -r ../claude-refactor-chain/README.md .
```

### Step 2: Update Your Project

1. Keep your `/refactor/` directory structure (no changes needed)
2. Replace `.github/workflows/claude-code.yml` with simplified version
3. Remove `.github/workflows/scripts/` (now in the action)
4. Test with `workflow_dispatch` trigger first

### Step 3: Gradual Rollout

1. Create new workflow file alongside existing one
2. Test with one project
3. Gradually migrate other projects
4. Remove old workflow when confident

## 8. Versioning & Releases

### Semantic Versioning

- **v1.0.0**: Initial release
- **v1.1.0**: New features (new inputs, new outputs)
- **v1.0.1**: Bug fixes
- **v2.0.0**: Breaking changes (changed behavior, removed features)

### Release Process

1. Update CHANGELOG.md
2. Create GitHub release with tag
3. Automated workflow updates major version ref:
   - Release v1.2.3 → update `v1` tag to point to v1.2.3
4. Users reference `@v1` for latest v1.x.x

### Tag Strategy

Users can choose stability level:
- `@v1`: Latest v1.x.x (recommended for most users)
- `@v1.2`: Latest v1.2.x (more stability)
- `@v1.2.3`: Exact version (maximum stability)
- `@main`: Bleeding edge (not recommended for production)

## 9. Testing Strategy

### Unit Tests (Python)

```python
# tests/test_refactor_chain.py
def test_find_next_available_task():
    """Test task finding with in-progress tasks"""
    # Create temp spec.md
    # Call find_next_available_task()
    # Assert correct task returned

def test_reviewer_capacity():
    """Test reviewer selection logic"""
    # Mock GitHub API responses
    # Call find_available_reviewer()
    # Assert correct reviewer selected
```

### Integration Tests (Workflow)

```yaml
# .github/workflows/test.yml
name: Test Action

on: [push, pull_request]

jobs:
  test-basic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Create test refactor project
      - name: Setup test project
        run: |
          mkdir -p refactor/test
          cp tests/fixtures/configuration.json refactor/test/
          cp tests/fixtures/spec.md refactor/test/

      # Test the action
      - uses: ./
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          project_name: test
```

### Smoke Tests

Before each release:
1. Test all trigger modes (schedule, manual, PR merge)
2. Test with 0, 1, and multiple reviewers
3. Test when all reviewers at capacity
4. Test when all tasks complete
5. Test with invalid configuration

## 10. Branding & Marketplace

### Action Metadata

```yaml
# action.yml
name: 'ClaudeStep'
description: 'Automate code refactoring with AI using Claude Code. Creates incremental PRs for systematic codebase improvements.'
author: 'Anthropic'
branding:
  icon: 'git-pull-request'
  color: 'orange'
```

### Marketplace Categories

- Code Quality
- Continuous Integration
- Project Management
- Utilities

### Keywords

- refactoring
- ai
- claude
- automation
- pull-request
- code-quality
- anthropic

## 11. Best Practices Implemented

### Security

- ✅ No secrets in logs
- ✅ Require explicit API key input (no defaults)
- ✅ Use `secrets.GITHUB_TOKEN` for repository operations
- ✅ Validate all user inputs
- ✅ Pin action dependencies to major versions

### Usability

- ✅ Sensible defaults for optional inputs
- ✅ Clear error messages with actionable guidance
- ✅ Comprehensive documentation with examples
- ✅ Step summaries visible in GitHub UI
- ✅ Outputs for downstream job integration

### Maintainability

- ✅ Modular Python code with clear functions
- ✅ Type hints and docstrings
- ✅ Comprehensive error handling
- ✅ Automated testing
- ✅ Automated releases

### Performance

- ✅ Composite action (fast startup)
- ✅ Minimal dependencies
- ✅ Caching where appropriate
- ✅ Efficient GitHub API usage (pagination, filtering)

## 12. Future Enhancements (Post-v1)

### v1.1: Enhanced Reporting

- Slack/Discord notifications when PRs created
- Metrics dashboard (PRs created, merged, review time)
- Progress tracking (X/Y tasks complete)

### v1.2: Advanced Features

- Support for draft PRs
- Auto-close/update PRs on rejection
- Custom Claude prompts per task
- Support for multiple spec formats (YAML, JSON)

### v1.3: Multi-Repository Support

- Run refactoring across multiple repositories
- Share spec files between repos
- Coordinated rollouts

### v2.0: Breaking Changes

- Rename `branchPrefix` to `branch_prefix` (snake_case consistency)
- Move configuration into action inputs (optional, deprecate JSON file)
- Support for other LLM providers

## 13. Success Criteria

### Launch (v1.0.0)

- ✅ Action published to GitHub Marketplace
- ✅ Complete documentation (README, examples, guides)
- ✅ Tested with 2+ real-world projects
- ✅ No critical bugs in first week

### Adoption (Month 1)

- 🎯 10+ external repositories using the action
- 🎯 5+ GitHub stars
- 🎯 Positive feedback from early adopters
- 🎯 Zero critical bug reports

### Sustainability (Month 3)

- 🎯 50+ repositories using the action
- 🎯 20+ GitHub stars
- 🎯 Active community (issues, discussions, PRs)
- 🎯 At least one community contribution merged

## 14. Open Questions to Resolve

### Configuration Location

**Q:** Should configuration be in JSON files (current) or action inputs?

**Options:**
1. **Keep JSON files** (current approach)
   - ✅ Pro: Easier to manage complex configs, version with code
   - ❌ Con: Less discoverable, harder to override in workflow
2. **Move to action inputs**
   - ✅ Pro: More standard GitHub Actions pattern, visible in workflow
   - ❌ Con: Verbose for multiple reviewers, harder to version
3. **Support both**
   - ✅ Pro: Maximum flexibility
   - ❌ Con: More complex, two ways to do the same thing

**Recommendation:** Keep JSON files for v1, add input-based config in v2.

### Claude Credentials

**Q:** How should users provide Anthropic API keys?

**Options:**
1. **Repository secret** (current)
   - ✅ Pro: Secure, standard GitHub pattern
   - ❌ Con: Must configure per-repository
2. **Organization secret**
   - ✅ Pro: Configure once for all repos
   - ❌ Con: Requires org-level permissions
3. **GitHub App with token exchange**
   - ✅ Pro: No manual secret management
   - ❌ Con: Complex setup, requires Anthropic integration

**Recommendation:** Repository secret for v1 (simplest), explore GitHub App in future.

### Action Namespace

**Q:** Where should the action be published?

**Options:**
1. `anthropics/claude-step`
2. `anthropics/claude-refactor-action`
3. `anthropics/ai-refactor-action`

**Recommendation:** `gestrich/claude-step` (descriptive, matches branding)

## 15. Next Steps

1. **Get approval on plan** (this document)
2. **Create action repository** with initial structure
3. **Implement Phase 1** (core action)
4. **Internal testing** with 2-3 projects
5. **Implement Phase 2** (documentation)
6. **Beta release** (v0.1.0) for early adopters
7. **Gather feedback** and iterate
8. **Stable release** (v1.0.0)
9. **Publish to Marketplace**
10. **Promote** via blog post, video, social media
