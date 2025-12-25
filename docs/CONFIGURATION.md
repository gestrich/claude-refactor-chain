# Configuration Guide

Complete reference for configuring the ClaudeStep action.

## Table of Contents

- [Project Structure](#project-structure)
- [configuration.json](#configurationjson)
- [spec.md](#specmd)
- [pr-template.md](#pr-templatemd)
- [Action Inputs](#action-inputs)
- [Examples](#examples)

## Project Structure

The recommended directory structure:

```
your-repo/
├── .github/
│   └── workflows/
│       └── continuous-refactor.yml
└── refactor/
    └── {project-name}/
        ├── configuration.json    (required)
        ├── spec.md               (required)
        └── pr-template.md        (optional)
```

You can have multiple refactor projects:

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

## configuration.json

### Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["label", "branchPrefix", "reviewers"],
  "properties": {
    "label": {
      "type": "string",
      "description": "GitHub label to apply to all PRs"
    },
    "branchPrefix": {
      "type": "string",
      "description": "Prefix for branch names (not used directly, branches use YYYY-MM-{project}-{index} format)"
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
            "description": "Maximum concurrent open PRs for this reviewer"
          }
        }
      }
    }
  }
}
```

### Fields

#### label (required)

The GitHub label to apply to all PRs created for this project.

**Requirements:**
- Must be lowercase alphanumeric with dashes
- Label must exist in your repository before first run
- Used to filter PRs when checking reviewer capacity

**Example:**
```json
"label": "swift-migration"
```

**Create the label:**
```bash
gh label create "swift-migration" \
  --description "Automated Swift migration PRs" \
  --color "0E8A16"
```

#### branchPrefix (required)

A descriptive prefix for the refactor project. Note: Actual branch names use the format `YYYY-MM-{project}-{index}`, where {project} is derived from the project folder name.

**Example:**
```json
"branchPrefix": "refactor/swift-migration"
```

This field is primarily for documentation purposes. The actual branch names will be like `2025-01-swift-migration-1`, `2025-01-swift-migration-2`, etc.

#### reviewers (required)

Array of reviewer configurations. Each reviewer can have multiple PRs open simultaneously up to their `maxOpenPRs` limit.

**Properties:**
- `username` (string): GitHub username (case-sensitive)
- `maxOpenPRs` (number): Maximum concurrent open PRs (1-10)

**Example:**
```json
"reviewers": [
  {
    "username": "alice",
    "maxOpenPRs": 2
  },
  {
    "username": "bob",
    "maxOpenPRs": 1
  }
]
```

**How it works:**
- Action checks each reviewer in order
- Assigns PR to first reviewer under their limit
- If all reviewers at capacity, no PR is created
- Reviewer is tracked via workflow artifacts

**Best practices:**
- Start with `maxOpenPRs: 1` initially
- Increase as team gets comfortable with volume
- Distribute capacity based on reviewer availability
- Use 2-3 reviewers for redundancy

### Complete Example

```json
{
  "label": "typescript-migration",
  "branchPrefix": "refactor/typescript",
  "reviewers": [
    {
      "username": "lead-dev",
      "maxOpenPRs": 2
    },
    {
      "username": "senior-dev",
      "maxOpenPRs": 2
    },
    {
      "username": "junior-dev",
      "maxOpenPRs": 1
    }
  ]
}
```

## spec.md

The specification file that combines refactoring instructions and task checklist.

### Format Requirements

1. **Must be valid Markdown**
2. **Must contain at least one checklist item:**
   - Unchecked: `- [ ] Task description`
   - Checked: `- [x] Completed task`
3. **Checklist items can appear anywhere** in the file

### Structure

```markdown
# Title

Your instructions here...

## Section 1

More instructions...

## Checklist

- [ ] Task 1
- [ ] Task 2
- [x] Completed task
```

Or interspersed:

```markdown
# Instructions

General guidelines here...

- [ ] First task

## More Details

Additional context...

- [ ] Second task
- [ ] Third task
```

### Writing Effective Instructions

#### Be Specific

Bad:
```markdown
- [ ] Update the user service
```

Good:
```markdown
- [ ] Convert UserService.getUserById() to use async/await instead of callbacks
```

#### Provide Context

The entire spec.md file is provided to Claude, so you can include:

- **Before/After Examples:**
  ```markdown
  Before:
  ‌```javascript
  function getUser(id, callback) {
    db.query(id, callback);
  }
  ‌```

  After:
  ‌```javascript
  async function getUser(id) {
    return await db.query(id);
  }
  ‌```
  ```

- **Coding Patterns:**
  ```markdown
  ## Patterns to Follow

  - Use async/await (not .then())
  - Handle errors with try/catch
  - Add JSDoc comments to public methods
  ```

- **Edge Cases:**
  ```markdown
  ## Special Cases

  - If function has no return value, don't add `return await`
  - Keep callback versions for backwards compatibility
  - Add deprecation notices to old functions
  ```

#### Iterative Improvement

Start with basic instructions and refine them based on PR reviews:

1. **Initial spec.md:**
   ```markdown
   Convert to TypeScript

   - [ ] Convert user.js
   ```

2. **After first PR, update to:**
   ```markdown
   Convert to TypeScript

   - Use strict mode (`strict: true`)
   - Add explicit return types
   - Don't use `any` type

   - [ ] Convert auth.js
   ```

3. **Continue refining:**
   ```markdown
   Convert to TypeScript

   ... (previous guidelines) ...

   - Export interfaces from separate .types.ts files
   - Use `unknown` instead of `any` for truly unknown types

   - [ ] Convert data.js
   ```

### Task Lifecycle

1. **Unchecked (`- [ ]`)**: Task is pending
2. **Action picks task**: Creates PR for it
3. **PR merged**: Action automatically marks as `- [x]`
4. **Checked (`- [x]`)**: Task is skipped in future runs

### Common Patterns

#### Group Related Tasks

```markdown
## Database Layer

- [ ] Convert UserRepository
- [ ] Convert ProductRepository
- [ ] Convert OrderRepository

## API Layer

- [ ] Convert UserController
- [ ] Convert ProductController
```

#### Progressive Complexity

```markdown
## Phase 1: Simple Components

- [ ] Convert Button component
- [ ] Convert Input component

## Phase 2: Complex Components

- [ ] Convert UserProfile (uses context)
- [ ] Convert DataTable (uses custom hooks)
```

#### File-by-File

```markdown
## src/services/

- [ ] auth.ts
- [ ] user.ts
- [ ] product.ts
```

## pr-template.md

Optional template for pull request descriptions.

### Template Variables

Use `{{VARIABLE_NAME}}` syntax for substitution:

| Variable | Description |
|----------|-------------|
| `{{TASK_DESCRIPTION}}` | The task description from spec.md |

### Example Template

```markdown
## Task

{{TASK_DESCRIPTION}}

## Changes

This PR was automatically created by ClaudeStep.

## Review Checklist

- [ ] Code follows project conventions
- [ ] Tests pass
- [ ] No unintended changes
- [ ] Documentation updated if needed

## Instructions for Reviewer

If you find issues:
1. Fix them directly in this PR
2. Update spec.md with improved instructions
3. Merge when ready

---

_Auto-generated by ClaudeStep_
```

### Default Template

If no pr-template.md exists, this default is used:

```markdown
## Task
{task description}
```

## Action Inputs

### Required Inputs

#### anthropic_api_key

Your Anthropic API key.

**How to set:**
1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Add to repository: Settings > Secrets and variables > Actions
3. Create secret named `ANTHROPIC_API_KEY`

**Usage:**
```yaml
with:
  anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### github_token

GitHub token for API access and PR creation.

**Default:** `${{ github.token }}`

**Usage:**
```yaml
with:
  github_token: ${{ secrets.GITHUB_TOKEN }}
```

#### project_name

Name of the project folder under `/refactor`.

**Example:**
```yaml
with:
  project_name: 'swift-migration'
```

**Dynamic example:**
```yaml
with:
  project_name: ${{ github.event.inputs.project || 'default-project' }}
```

### Optional Inputs

#### config_path

Override default configuration file location.

**Default:** `refactor/{project_name}/configuration.json`

**Usage:**
```yaml
with:
  config_path: 'custom/path/to/config.json'
```

#### spec_path

Override default spec file location.

**Default:** `refactor/{project_name}/spec.md`

**Usage:**
```yaml
with:
  spec_path: 'custom/path/to/spec.md'
```

#### pr_template_path

Override default PR template location.

**Default:** `refactor/{project_name}/pr-template.md`

**Usage:**
```yaml
with:
  pr_template_path: 'custom/path/to/template.md'
```

#### claude_model

Specify which Claude model to use.

**Default:** `claude-sonnet-4-5`

**Options:**
- `claude-sonnet-4-5` (recommended - balanced performance and cost)
- `claude-opus-4-5` (highest capability, higher cost)

**Usage:**
```yaml
with:
  claude_model: 'claude-opus-4-5'
```

#### claude_allowed_tools

Comma-separated list of tools Claude can use.

**Default:** `Write,Read,Bash,Edit`

**Available tools:**
- `Write` - Create new files
- `Read` - Read files
- `Bash` - Execute shell commands
- `Edit` - Edit existing files
- `Glob` - Find files by pattern
- `Grep` - Search file contents

**Usage:**
```yaml
with:
  claude_allowed_tools: 'Write,Read,Bash,Edit,Glob,Grep'
```

**Security note:** Only add tools that are safe for your use case. More tools = more power but also more potential for unintended changes.

#### base_branch

The base branch to create PRs against.

**Default:** `main`

**Usage:**
```yaml
with:
  base_branch: 'develop'
```

#### working_directory

Working directory for the action (if your refactor files aren't at repo root).

**Default:** `.`

**Usage:**
```yaml
with:
  working_directory: 'frontend'
```

## Examples

### Minimal Configuration

```yaml
# workflow.yml
- uses: gestrich/claude-step@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    project_name: 'swift-migration'
```

```json
// configuration.json
{
  "label": "swift-migration",
  "branchPrefix": "refactor/swift",
  "reviewers": [
    { "username": "you", "maxOpenPRs": 1 }
  ]
}
```

```markdown
<!-- spec.md -->
# Swift Migration

Convert Objective-C to Swift.

- [ ] Convert AppDelegate.m
```

### Full-Featured Configuration

```yaml
# workflow.yml
- uses: gestrich/claude-step@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    project_name: 'typescript-migration'
    claude_model: 'claude-opus-4-5'
    claude_allowed_tools: 'Write,Read,Bash,Edit,Glob,Grep'
    base_branch: 'develop'
```

```json
// configuration.json
{
  "label": "typescript-conversion",
  "branchPrefix": "refactor/typescript",
  "reviewers": [
    { "username": "lead-dev", "maxOpenPRs": 3 },
    { "username": "senior-dev-1", "maxOpenPRs": 2 },
    { "username": "senior-dev-2", "maxOpenPRs": 2 }
  ]
}
```

```markdown
<!-- spec.md -->
# TypeScript Migration

Convert JavaScript files to TypeScript with strict type checking.

## Guidelines

- Use strict mode
- Prefer interfaces over types for objects
- Export types from .types.ts files
- Add JSDoc for complex functions

## Before/After

...

## Checklist

- [ ] src/services/auth.js
- [ ] src/services/user.js
...
```

## Validation

The action validates your configuration at runtime:

### configuration.json Validation

- ✅ File exists and is valid JSON
- ✅ Required fields present
- ✅ Reviewers array has at least one entry
- ✅ Each reviewer has username and maxOpenPRs

### spec.md Validation

- ✅ File exists
- ✅ Contains at least one checklist item (`- [ ]` or `- [x]`)

If validation fails, the workflow will error with a descriptive message.

## Best Practices

1. **Start simple** - Basic instructions, one reviewer, low capacity
2. **Test manually** - Use workflow_dispatch to test before scheduling
3. **Iterate on instructions** - Update spec.md based on review feedback
4. **Monitor capacity** - Check workflow summaries to see reviewer load
5. **Version control everything** - Commit config changes with code changes
6. **Document gotchas** - Add special cases to spec.md as you discover them
