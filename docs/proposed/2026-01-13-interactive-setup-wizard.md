# Interactive Setup Wizard

## Background

ClaudeChain requires users to manually create workflow files, project directories, and configuration files. This is error-prone and creates friction for new users. An interactive setup wizard was introduced to guide users through the setup process step-by-step.

## What Has Been Done

### Command Implementation

Added `claudechain setup <repo_path>` command that provides an interactive CLI wizard with three main flows:

**1. Setup Repository**
- Validates the path is a git repository with GitHub remote
- Creates `.github/workflows/claudechain.yml` workflow file
- Optionally creates `.github/workflows/claudechain-statistics.yml` for Slack reporting
- Displays GitHub configuration instructions (secrets, permissions)
- Offers to create the first project

**2. Create New Spec (Project)**
- Prompts for project name and base branch
- Creates project directory under `claude-chain/<project-name>/`
- Generates starter files:
  - `spec.md` with sample tasks
  - `configuration.yml` (if non-default settings)
  - `pr-template.md`
  - `pre-action.sh` and `post-action.sh`

**3. Deploy Spec (Project)**
- Guides users through pushing changes to GitHub
- Offers PR flow or direct push flow
- Can trigger the first workflow run via `gh` CLI

### Files Added/Modified

- `src/claudechain/cli/commands/setup.py` - New 809-line interactive wizard
- `src/claudechain/cli/parser.py` - Added `setup` subcommand parser
- `src/claudechain/__main__.py` - Added command routing for `setup`

## What Remains

- [ ] **Write user documentation**

Create a feature guide at `docs/feature-guides/setup.md` explaining:
- How to run the setup wizard
- What each flow does
- Screenshots or example terminal output
- Troubleshooting common issues

- [ ] **Add unit tests**

Test the helper functions in `setup.py`:
- `validate_git_repo()`
- `validate_github_repo()`
- `has_claudechain_workflow()`
- `get_current_branch()`
- `get_workflow_name()`

- [ ] **Add integration tests**

Test the file creation functions:
- `create_workflow_file()`
- `create_statistics_workflow()`
- `add_project()` (creates correct directory structure)

- [ ] **Handle edge cases**

Consider and test:
- Non-standard default branch names (not `main`)
- Repositories without any remotes
- Existing but incomplete ClaudeChain setup
- Windows path handling (if applicable)

- [ ] **Add `--non-interactive` flag**

Allow scripted setup with defaults for CI/automation use cases:
```bash
claudechain setup /path/to/repo --non-interactive --project-name=my-project
```

- [ ] **Validate generated workflow files**

After creating workflow files, optionally validate YAML syntax to catch errors early.

- [ ] **Document Python version requirement**

Document the minimum Python version needed to run the CLI. Consider downgrading the required version if possible to support users with standard macOS Python installations (macOS ships with older Python versions, and requiring newer versions creates friction for local CLI usage).
