# ClaudeStep Metadata Schema

This document defines the JSON schema used for storing ClaudeStep metadata in the `claudestep-metadata` branch.

## Data Model Overview

ClaudeStep uses a **hybrid model** that separates task definitions from pull request execution:

```
Project
  ├── Tasks[] (lightweight task references from spec.md)
  │   └── Task Properties (index, description, status)
  └── PullRequests[] (execution details)
      ├── PR Properties (task_index, pr_number, branch, reviewer, state, etc.)
      └── AIOperations[] (individual AI operations)
          └── AI Properties (type, model, cost, tokens, duration, workflow_run_id)
```

**Key Design**: Tasks represent "what" (from spec.md) while PullRequests represent "how" (execution). This separation allows:
- All tasks from spec.md are always present (even if not started)
- Multiple PRs can reference the same task (retry scenario)
- Task status is derived from PR state (single source of truth)

**Typical Flow**: Each task in `spec.md` gets a Pull Request with 2 AI operations:
1. **PRCreation**: Claude Code generates the code changes
2. **PRSummary**: AI generates the PR description

## Directory Structure

The `claudestep-metadata` branch has the following structure:

```
claudestep-metadata/
├── projects/
│   ├── project-name-1.json
│   ├── project-name-2.json
│   └── project-name-3.json
└── README.md
```

### File Organization

- **`projects/`**: Directory containing one JSON file per project
  - File naming: `{project-name}.json` (matches the project directory name)
  - Each file contains all step metadata for that project
- **`README.md`**: Explains the purpose of the metadata branch

### Design Rationale

- **Flat structure**: Simple and efficient for typical ClaudeStep usage (5-20 projects per repo)
- **One file per project**: Enables atomic updates per project and parallel writes across projects
- **Human-readable JSON**: Easy to inspect and debug using GitHub's web interface or git commands
- **Hybrid model**: Separates tasks (spec.md content) from pull requests (execution), providing clear separation of concerns

## JSON Schema

### Project Metadata File

Each project file (`projects/{project-name}.json`) has the following structure:

```json
{
  "schema_version": "2.0",
  "project": "my-refactor",
  "last_updated": "2025-01-15T10:30:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Refactor authentication module",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Add JWT token validation",
      "status": "pending"
    },
    {
      "index": 3,
      "description": "Implement OAuth2 integration",
      "status": "pending"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 42,
      "branch_name": "claude-step-my-refactor-1",
      "reviewer": "alice",
      "pr_state": "merged",
      "created_at": "2025-01-10T14:22:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-01-10T14:22:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 8500,
          "tokens_output": 1200,
          "duration_seconds": 12.5
        },
        {
          "type": "PRSummary",
          "model": "claude-sonnet-4",
          "cost_usd": 0.02,
          "created_at": "2025-01-10T14:23:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 1200,
          "tokens_output": 150,
          "duration_seconds": 2.1
        }
      ]
    }
  ]
}
```

**Hybrid Model Design:**
- **Separation of concerns**: Tasks (what) are separate from PullRequests (how)
- **All tasks present**: Even tasks not yet started appear in the `tasks` array
- **Task status**: Derived from associated PR state ("pending", "in_progress", "completed")
- **Multiple PRs per task**: Supports retry scenario where same task has multiple PRs
- **Workflow tracking**: Each AI operation links to specific GitHub Actions workflow run

### Field Definitions

#### Project-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Schema version for future migrations (currently "2.0") |
| `project` | string | Yes | Project name (matches directory and file name) |
| `last_updated` | string (ISO 8601) | Yes | Timestamp of last metadata update |
| `tasks` | array | Yes | List of Task objects (one per task from spec.md) |
| `pull_requests` | array | Yes | List of PullRequest objects (execution history) |

#### Task Fields

Each object in the `tasks` array represents a single task from spec.md:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `index` | integer | Yes | Task number from spec.md (1-based) |
| `description` | string | Yes | Task description text from spec.md |
| `status` | string | Yes | Task status: "pending", "in_progress", or "completed" |

**Task Status Values:**
- `pending`: No PR created yet
- `in_progress`: PR created but not merged (includes open or closed PRs)
- `completed`: PR merged successfully

**Note:** All tasks from spec.md are present in this array, even if not yet started.

#### PullRequest Fields

Each object in the `pull_requests` array represents a single pull request:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_index` | integer | Yes | References Task.index (which task this PR implements) |
| `pr_number` | integer | Yes | GitHub pull request number |
| `branch_name` | string | Yes | Git branch name for this PR |
| `reviewer` | string | Yes | Assigned reviewer GitHub username |
| `pr_state` | string | Yes | PR state: "open", "merged", or "closed" |
| `created_at` | string (ISO 8601) | Yes | When this PR was created |
| `ai_operations` | array | Yes | List of AI operations for this PR |

**Note:** Multiple PRs can reference the same `task_index` in retry scenarios.

#### AIOperation Fields

Each object in the `ai_operations` array represents a single AI operation:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Operation type: "PRCreation", "PRRefinement", "PRSummary", etc. |
| `model` | string | Yes | AI model used (e.g., "claude-sonnet-4", "claude-opus-4") |
| `cost_usd` | float | Yes | Cost in USD for this specific AI operation |
| `created_at` | string (ISO 8601) | Yes | When this AI operation was executed |
| `workflow_run_id` | integer | Yes | GitHub Actions workflow run ID that executed this operation |
| `tokens_input` | integer | No | Input tokens used (default: 0) |
| `tokens_output` | integer | No | Output tokens generated (default: 0) |
| `duration_seconds` | float | No | Time taken for this operation in seconds (default: 0.0) |

**AI Operation Types:**
- `PRCreation`: Initial code generation for the PR
- `PRRefinement`: Code refinement or iteration based on feedback
- `PRSummary`: AI-generated PR description and summary
- `CodeReview`: AI-assisted code review feedback
- `TestGeneration`: Automated test generation

### Timestamp Format

All timestamps use ISO 8601 format with timezone:

- **Format**: `YYYY-MM-DDTHH:MM:SSZ` (UTC)
- **Example**: `2025-01-15T10:30:00Z`
- Python: Use `datetime.isoformat()` for serialization
- Python: Use `datetime.fromisoformat(s.replace("Z", "+00:00"))` for parsing

## PR State Values

The `pr_state` field tracks the lifecycle of each pull request:

| Value | Description | Usage |
|-------|-------------|-------|
| `open` | PR is currently open | Used for reviewer capacity checking |
| `merged` | PR was merged | Used for statistics and completion tracking |
| `closed` | PR was closed without merging | Tracked but typically excluded from statistics |

## Schema Versioning

The `schema_version` field enables future migrations:

- **Current version**: "2.0" (Hybrid model with separated tasks and pull_requests)
- **Previous version**: "1.0" (Legacy model - not implemented, documentation only)
- **Forward compatibility**: New fields can be added with default values
- **Breaking changes**: Increment schema version and implement migration logic
- **Backward compatibility**: Parsers should handle missing optional fields gracefully

## Example: Complete Project File

```json
{
  "schema_version": "2.0",
  "project": "auth-refactor",
  "last_updated": "2025-01-20T15:45:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Extract authentication logic to separate module",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Add JWT token validation",
      "status": "in_progress"
    },
    {
      "index": 3,
      "description": "Implement OAuth2 integration",
      "status": "in_progress"
    },
    {
      "index": 4,
      "description": "Add rate limiting middleware",
      "status": "pending"
    },
    {
      "index": 5,
      "description": "Write integration tests for auth flow",
      "status": "pending"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 101,
      "branch_name": "claude-step-auth-refactor-1",
      "reviewer": "alice",
      "pr_state": "merged",
      "created_at": "2025-01-10T09:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-01-10T09:00:00Z",
          "workflow_run_id": 100001,
          "tokens_input": 7500,
          "tokens_output": 1100,
          "duration_seconds": 10.2
        },
        {
          "type": "PRSummary",
          "model": "claude-sonnet-4",
          "cost_usd": 0.03,
          "created_at": "2025-01-10T09:01:00Z",
          "workflow_run_id": 100001,
          "tokens_input": 1100,
          "tokens_output": 180,
          "duration_seconds": 2.5
        }
      ]
    },
    {
      "task_index": 2,
      "pr_number": 105,
      "branch_name": "claude-step-auth-refactor-2",
      "reviewer": "bob",
      "pr_state": "open",
      "created_at": "2025-01-15T14:30:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.18,
          "created_at": "2025-01-15T14:30:00Z",
          "workflow_run_id": 100025,
          "tokens_input": 9200,
          "tokens_output": 1350,
          "duration_seconds": 14.8
        },
        {
          "type": "PRSummary",
          "model": "claude-sonnet-4",
          "cost_usd": 0.02,
          "created_at": "2025-01-15T14:32:00Z",
          "workflow_run_id": 100025,
          "tokens_input": 1350,
          "tokens_output": 120,
          "duration_seconds": 1.9
        }
      ]
    },
    {
      "task_index": 3,
      "pr_number": 108,
      "branch_name": "claude-step-auth-refactor-3",
      "reviewer": "alice",
      "pr_state": "open",
      "created_at": "2025-01-20T11:15:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-opus-4",
          "cost_usd": 0.22,
          "created_at": "2025-01-20T11:15:00Z",
          "workflow_run_id": 100050,
          "tokens_input": 12000,
          "tokens_output": 1800,
          "duration_seconds": 18.3
        },
        {
          "type": "PRRefinement",
          "model": "claude-opus-4",
          "cost_usd": 0.03,
          "created_at": "2025-01-20T11:20:00Z",
          "workflow_run_id": 100075,
          "tokens_input": 2500,
          "tokens_output": 200,
          "duration_seconds": 3.2
        },
        {
          "type": "PRSummary",
          "model": "claude-sonnet-4",
          "cost_usd": 0.04,
          "created_at": "2025-01-20T11:22:00Z",
          "workflow_run_id": 100075,
          "tokens_input": 1800,
          "tokens_output": 210,
          "duration_seconds": 2.8
        }
      ]
    }
  ]
}
```

**This example demonstrates:**

1. **Separation of Tasks and PRs**:
   - All 5 tasks from spec.md are present in `tasks` array
   - Tasks 1-3 have associated PRs; tasks 4-5 are pending
   - Task status is derived from PR state (single source of truth)

2. **Typical 2-AI-Operation Pattern** (Tasks 1 & 2):
   - `PRCreation`: Claude Code generates the code changes
   - `PRSummary`: AI writes the PR description
   - Both run in same workflow (same `workflow_run_id`)
   - Most PRs follow this pattern

3. **Complex PR with Refinement** (Task 3):
   - `PRCreation`: Initial code generation with Opus 4 (workflow 100050)
   - `PRRefinement`: Additional iteration in a later workflow (100075)
   - `PRSummary`: PR description in same workflow as refinement (100075)
   - **Note**: Different workflow_run_ids show this PR had multiple workflow executions

4. **Pending Tasks** (Tasks 4 & 5):
   - Present in `tasks` array with "pending" status
   - No corresponding entries in `pull_requests` array
   - Shows complete project progress at a glance

5. **Model Flexibility**:
   - Tasks 1-2: Use Sonnet 4 throughout (cost-effective)
   - Task 3: Uses Opus 4 for complex work, Sonnet 4 for summary

6. **Clean Structure**:
   - Clear separation: tasks = "what", pull_requests = "how"
   - `workflow_run_id` in each AI operation (enables tracking multiple workflow runs)
   - Cost/model info encapsulated in AI operations
   - Easy to calculate totals: sum `cost_usd` from all `ai_operations` across all PRs
   - Supports multiple PRs per task (retry scenario)

## Index Strategy Decision

**Decision**: **No separate index file** for initial implementation.

### Rationale

1. **Simple implementation**: Fewer moving parts, less complexity
2. **Acceptable performance**: Reading 5-20 project files via GitHub API takes <2 seconds
3. **Atomic updates**: Each project file can be updated independently
4. **No synchronization issues**: No need to keep index in sync with project files

### Query Performance

- **List all projects**: Single Git Tree API call + parse filenames (instant)
- **Get project metadata**: 1 API call per project (~100ms each)
- **Filter by date**: Read all files, filter in-memory (<2 seconds for 20 projects)
- **Statistics generation**: Target <5 seconds (vs. 30+ seconds with artifacts)

### Future Optimization

If performance becomes an issue (e.g., 100+ projects):
- Add optional `index.json` with summary data (project names, last_updated, counts)
- Rebuild index on-demand or during writes
- Use index for fast filtering, then read individual project files

## Implementation Notes

### Python Models

The schema is implemented in Python using dataclasses (see `src/claudestep/domain/models.py`):

- **`Task`**: Lightweight task reference (index, description, status)
- **`PullRequest`**: PR execution details (task_index, pr_number, branch_name, reviewer, pr_state, created_at, ai_operations)
- **`AIOperation`**: Single AI operation (type, model, cost, tokens, duration, workflow_run_id)
- **`HybridProjectMetadata`**: Project container (schema_version, project, last_updated, tasks, pull_requests)
- All models have `from_dict()` and `to_dict()` methods for JSON serialization

### Key Design Benefits

**Hybrid Model Advantages:**
- **Separation of concerns**: Tasks (spec.md content) are separate from PullRequests (execution)
- **Complete visibility**: All tasks from spec.md are always present, even if not started
- **Single source of truth**: Task status is derived from PR state
- **Retry support**: Multiple PRs can reference the same task (retry scenario)
- **Clean queries**: Easy to find all tasks, all pending tasks, all PRs for a task, etc.

**Model Characteristics:**
- **Task**: Lightweight (just index, description, status)
- **PullRequest**: Contains all execution details and references task by index
- **AIOperation**: Owns all metrics (cost, tokens, duration) and links to workflow
- **Workflow tracking**: Each AI operation has workflow_run_id for precise tracking

### Storage Backend

The schema is stored in GitHub using:
- **Branch**: `claudestep-metadata` (created on first write)
- **API**: GitHub Contents API for file operations
- **Encoding**: JSON with UTF-8 encoding
- **Commits**: One commit per project update (atomic writes)
- **Optimistic locking**: SHA-based conditional updates prevent conflicts

See: `src/claudestep/infrastructure/metadata/github_metadata_store.py`
