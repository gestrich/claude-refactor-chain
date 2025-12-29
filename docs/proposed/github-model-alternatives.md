# GitHub Metadata Model - Alternative Designs

## Background

The current data model for ClaudeStep metadata storage feels awkward and may not be the most intuitive way to represent the relationships between projects, steps, PRs, and AI operations.

### Current Model Issues

The current implementation uses:
```
Project
  └── Step
      ├── PR info (branch_name, reviewer, pr_number, pr_state, created_at)
      └── ai_tasks: List[AITask]
          └── workflow_run_id, type, model, cost, tokens, duration
```

**Potential Issues:**
1. **Mixed responsibilities**: Step combines both spec.md metadata AND PR execution details
2. **Unclear ownership**: Is a Step a "task from spec.md" or a "PR"? It's trying to be both
3. **Optional fields**: Most Step fields are optional, making the model hard to reason about
4. **Not-yet-started steps**: Minimal steps (just index + description) feel like a special case
5. **Naming confusion**: "Step" is better than "Task" but still unclear what it represents

### Goals

1. **Clear separation of concerns**: Separate spec.md structure from PR execution tracking
2. **Explicit relationships**: Make relationships between entities obvious
3. **Minimal special cases**: Avoid "not started" vs "started" being fundamentally different
4. **Easy to reason about**: Model should match mental model of how ClaudeStep works
5. **Visual clarity**: Diagrams should make relationships immediately obvious

## Phase 1: Document Current Model ✅

**Tasks:**
- Create detailed diagram of current `Project → Step → AITask` structure
- Document all fields and their purposes
- Show example JSON for different states (not started, in progress, merged)
- Identify pain points and awkward aspects
- Document what queries we need to support (capacity checking, statistics, progress)

**Expected Outcome:**
- Clear understanding of current model's strengths and weaknesses
- Visual representation showing current structure
- List of specific issues to address in alternatives

### Current Model Structure

```
Project
├── schema_version: str                  # Metadata format version (e.g., "1.0")
├── project: str                         # Project name/identifier
├── last_updated: datetime               # Last modification timestamp
└── steps: List[Step]                   # All steps from spec.md
    └── Step
        ├── step_index: int              # Required: Position in spec.md (1-based)
        ├── step_description: str        # Required: Task description from spec.md
        ├── branch_name: Optional[str]   # PR branch (None if not started)
        ├── reviewer: Optional[str]      # Assigned reviewer (None if not started)
        ├── pr_number: Optional[int]     # GitHub PR number (None if not started)
        ├── pr_state: Optional[str]      # "open", "merged", "closed" (None if not started)
        ├── created_at: Optional[datetime] # PR creation timestamp (None if not started)
        └── ai_tasks: List[AITask]       # All AI operations for this PR
            └── AITask
                ├── type: str                # "PRCreation", "PRRefinement", "PRSummary"
                ├── model: str              # AI model used (e.g., "claude-sonnet-4")
                ├── cost_usd: float         # Cost for this operation
                ├── created_at: datetime    # When this AI task was executed
                ├── workflow_run_id: int    # GitHub Actions run that executed this
                ├── tokens_input: int       # Input tokens (default: 0)
                ├── tokens_output: int      # Output tokens (default: 0)
                └── duration_seconds: float # Execution time (default: 0.0)
```

### Field Purposes and Semantics

#### Project Fields
- **schema_version**: Enables future schema evolution and migration
- **project**: Identifies which spec.md file this metadata tracks
- **last_updated**: Cache invalidation and audit trail
- **steps**: Contains ALL steps from spec.md, both started and not-yet-started

#### Step Fields
- **step_index**: Links to spec.md position (permanent identifier)
- **step_description**: Human-readable task from spec.md
- **branch_name**: Git branch created for the PR
- **reviewer**: Team member assigned to review this PR
- **pr_number**: GitHub PR identifier for linking/querying
- **pr_state**: Tracks PR lifecycle (open → merged/closed)
- **created_at**: Timestamp for progress tracking and statistics
- **ai_tasks**: Complete history of all AI operations on this step

#### AITask Fields
- **type**: Distinguishes different AI operation purposes
- **model**: Tracks which AI model was used (cost/capability tracking)
- **cost_usd**: Per-operation cost tracking
- **created_at**: Timeline reconstruction
- **workflow_run_id**: Links to GitHub Actions logs for debugging
- **tokens_input/output**: Detailed usage metrics
- **duration_seconds**: Performance tracking

### Example JSON for Different States

#### Not Started Step
```json
{
  "step_index": 3,
  "step_description": "Add email validation to user registration form"
}
```

#### In Progress Step (PR Created)
```json
{
  "step_index": 2,
  "step_description": "Implement OAuth2 authentication flow",
  "branch_name": "claudestep/auth-refactor/step-2",
  "reviewer": "alice",
  "pr_number": 42,
  "pr_state": "open",
  "created_at": "2025-12-29T10:30:00Z",
  "ai_tasks": [
    {
      "type": "PRCreation",
      "model": "claude-sonnet-4",
      "cost_usd": 0.15,
      "created_at": "2025-12-29T10:30:00Z",
      "workflow_run_id": 123456,
      "tokens_input": 5000,
      "tokens_output": 2000,
      "duration_seconds": 45.2
    }
  ]
}
```

#### Merged Step with Refinement
```json
{
  "step_index": 1,
  "step_description": "Set up authentication middleware",
  "branch_name": "claudestep/auth-refactor/step-1",
  "reviewer": "bob",
  "pr_number": 41,
  "pr_state": "merged",
  "created_at": "2025-12-28T14:20:00Z",
  "ai_tasks": [
    {
      "type": "PRCreation",
      "model": "claude-sonnet-4",
      "cost_usd": 0.12,
      "created_at": "2025-12-28T14:20:00Z",
      "workflow_run_id": 123450,
      "tokens_input": 4500,
      "tokens_output": 1800,
      "duration_seconds": 42.1
    },
    {
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.08,
      "created_at": "2025-12-28T16:45:00Z",
      "workflow_run_id": 123451,
      "tokens_input": 3000,
      "tokens_output": 1200,
      "duration_seconds": 28.5
    }
  ]
}
```

#### Complete Project Example
```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T10:30:00Z",
  "steps": [
    {
      "step_index": 1,
      "step_description": "Set up authentication middleware",
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_number": 41,
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_tasks": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "step_index": 2,
      "step_description": "Implement OAuth2 authentication flow",
      "branch_name": "claudestep/auth-refactor/step-2",
      "reviewer": "alice",
      "pr_number": 42,
      "pr_state": "open",
      "created_at": "2025-12-29T10:30:00Z",
      "ai_tasks": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T10:30:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 5000,
          "tokens_output": 2000,
          "duration_seconds": 45.2
        }
      ]
    },
    {
      "step_index": 3,
      "step_description": "Add email validation to user registration form"
    },
    {
      "step_index": 4,
      "step_description": "Implement password reset functionality"
    },
    {
      "step_index": 5,
      "step_description": "Add two-factor authentication support"
    }
  ]
}
```

### Pain Points and Awkward Aspects

#### 1. **Mixed Responsibilities in Step**
The `Step` dataclass tries to represent two distinct concepts:
- A task definition from spec.md (immutable, semantic content)
- A PR execution (mutable, runtime state)

This creates confusion: Is a Step a "plan" or an "execution"?

#### 2. **Optional Field Explosion**
Most Step fields are Optional, creating two distinct "modes":
- **Minimal Step**: Just `step_index` + `step_description` (not started)
- **Full Step**: All fields populated (PR created)

This makes the model hard to reason about:
```python
# Which fields can I safely access?
if step.pr_number:  # Have to check before using
    print(f"PR: {step.pr_number}")
```

#### 3. **Unclear Entity Boundaries**
The model doesn't clearly separate:
- **Spec content** (what needs to be done) vs **Execution state** (what was done)
- **PR metadata** (GitHub state) vs **AI operations** (ClaudeStep internals)

#### 4. **Special Case Handling**
Not-yet-started steps feel like a special case rather than a natural part of the model. Code frequently needs to check `step.is_started()` to determine which fields are valid.

#### 5. **Naming Ambiguity**
"Step" is better than the old "Task" name, but still unclear:
- Is it a "step in the plan" (spec.md)?
- Is it a "step in execution" (PR)?
- It's trying to be both, which creates cognitive overhead

#### 6. **Implicit Relationships**
The relationship between Steps and PRs is implicit (same object). If we ever need to support multiple PR attempts for the same step, the model breaks down.

#### 7. **Denormalized Data**
`step_description` is duplicated from spec.md into metadata storage. If spec.md changes, metadata becomes stale. However, this may be intentional for historical accuracy.

#### 8. **No Direct Status Field**
PR state must be inferred from multiple fields:
- Not started: `pr_number is None`
- In progress: `pr_number is not None and pr_state == "open"`
- Complete: `pr_state == "merged"`

This logic is scattered across the codebase.

### Required Query Patterns

Based on the codebase analysis, the model must efficiently support:

#### 1. **Reviewer Capacity Checking**
```python
# For each reviewer, count open PRs across all projects
# to determine if they have capacity for new assignments
open_prs_by_reviewer = {}
for project in all_projects:
    for step in project.steps:
        if step.pr_state == "open":
            open_prs_by_reviewer[step.reviewer].append(...)
```

#### 2. **Project Statistics**
```python
# Calculate completion percentage, costs, progress
total_steps = len(project.steps)
completed = sum(1 for s in project.steps if s.pr_state == "merged")
in_progress = sum(1 for s in project.steps if s.pr_state == "open")
pending = sum(1 for s in project.steps if not s.is_started())
total_cost = sum(step.get_total_cost() for step in project.steps)
```

#### 3. **Next Step Selection**
```python
# Find the next pending step to work on
next_step = next(s for s in project.steps if not s.is_started())
```

#### 4. **Team Leaderboard**
```python
# Aggregate PR counts by team member across all projects
for project in all_projects:
    for step in project.steps:
        if step.pr_state == "merged":
            team_stats[step.reviewer].merged_count += 1
```

#### 5. **Cost Analysis**
```python
# Sum costs by project, by model, by time period
for step in project.steps:
    for ai_task in step.ai_tasks:
        cost_by_model[ai_task.model] += ai_task.cost_usd
```

#### 6. **Progress Tracking**
```python
# Determine if project is complete, blocked, or active
all_merged = all(s.pr_state == "merged" for s in project.steps if s.is_started())
has_open = any(s.pr_state == "open" for s in project.steps)
```

### Model Strengths

Despite the pain points, the current model has several strengths:

#### 1. **Complete Historical Record**
Every step from spec.md is preserved, including not-yet-started ones. This provides a complete view of the project plan.

#### 2. **Simple Hierarchy**
The three-level hierarchy (Project → Step → AITask) is straightforward and easy to understand at a high level.

#### 3. **Self-Contained Steps**
Each Step contains all information about its PR and AI operations. No need to join across multiple data structures.

#### 4. **Minimal JSON for Pending Steps**
Not-yet-started steps serialize to just two fields, keeping the JSON compact.

#### 5. **Backward Compatibility Support**
The model gracefully handles migration from old field names (task_index → step_index).

### Conclusion

The current model works but has conceptual awkwardness stemming from Steps trying to be both "plan definition" and "execution record". The optional field pattern creates two distinct Step "modes" that require careful handling throughout the codebase.

Alternative models should explore:
1. Separating spec definition from execution tracking
2. Making entity boundaries more explicit
3. Reducing optional fields and special cases
4. Clarifying the relationship between tasks and PRs

**Technical Notes:**
- Current implementation: `src/claudestep/domain/models.py:502-809`
- Uses Python dataclasses with `from_dict`/`to_dict` for JSON serialization
- Backward compatibility handled via field name aliasing
- All datetime fields use ISO 8601 format in JSON

## Phase 2: Alternative Model 1 - Separate Spec and Execution ✅

**Concept:**
```
Project
  ├── spec: ProjectSpec
  │   └── tasks: List[TaskDefinition]
  │       └── index, description
  └── executions: List[Execution]
      └── task_index, pr_number, branch, reviewer, state, created_at
          └── ai_operations: List[AIOperation]
              └── workflow_run_id, type, model, cost, tokens
```

**Key Ideas:**
- **ProjectSpec**: Immutable definition from spec.md (what needs to be done)
- **TaskDefinition**: Just index + description from spec.md
- **Execution**: One attempt to implement a task (may fail, may be refined)
- **AIOperation**: Individual AI work (replaces AITask)

### Detailed Structure Diagram

```
Project
├── schema_version: str                   # Metadata format version (e.g., "1.0")
├── project: str                          # Project name/identifier
├── last_updated: datetime                # Last modification timestamp
├── spec: ProjectSpec                     # IMMUTABLE: Definition from spec.md
│   └── tasks: List[TaskDefinition]       # All tasks defined in spec.md
│       └── TaskDefinition
│           ├── index: int                # Position in spec.md (1-based)
│           └── description: str          # Task description from spec.md
└── executions: List[Execution]           # MUTABLE: PR execution history
    └── Execution
        ├── execution_id: str             # Unique identifier for this execution attempt
        ├── task_index: int               # References TaskDefinition.index
        ├── pr_number: int                # GitHub PR number
        ├── branch_name: str              # Git branch for this execution
        ├── reviewer: str                 # Assigned reviewer username
        ├── pr_state: str                 # "open", "merged", "closed"
        ├── created_at: datetime          # When execution started
        └── ai_operations: List[AIOperation]  # All AI work for this execution
            └── AIOperation
                ├── operation_id: str         # Unique identifier for this operation
                ├── type: str                 # "PRCreation", "PRRefinement", "PRSummary"
                ├── model: str                # AI model used (e.g., "claude-sonnet-4")
                ├── cost_usd: float           # Cost for this operation
                ├── created_at: datetime      # When this operation was executed
                ├── workflow_run_id: int      # GitHub Actions run that executed this
                ├── tokens_input: int         # Input tokens (default: 0)
                ├── tokens_output: int        # Output tokens (default: 0)
                └── duration_seconds: float   # Execution time (default: 0.0)
```

### Key Relationships

1. **Spec → Execution**: One-to-many relationship via `task_index`
   - One `TaskDefinition` can have zero or more `Execution` records
   - Zero executions = task not yet started
   - One execution = normal case (single PR attempt)
   - Multiple executions = task was attempted multiple times (e.g., PR closed and retried)

2. **Execution → AIOperation**: One-to-many relationship
   - Each `Execution` has one or more `AIOperation` records
   - First operation is typically "PRCreation"
   - Additional operations are "PRRefinement" or other modifications
   - All operations belong to the same PR/execution

3. **Task Identification**: Tasks are identified by `index` (permanent) rather than PR state
   - Spec defines what needs to be done (static)
   - Executions track what was done (dynamic)

### Example JSON: Auth Refactor Project

This example shows a project with 5 tasks:
- Task 1: Merged (one execution with one operation)
- Task 2: In progress (one execution with one operation)
- Task 3: Not started (no executions)
- Task 4: Not started (no executions)
- Task 5: Not started (no executions)

```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T10:30:00Z",
  "spec": {
    "tasks": [
      {
        "index": 1,
        "description": "Set up authentication middleware"
      },
      {
        "index": 2,
        "description": "Implement OAuth2 authentication flow"
      },
      {
        "index": 3,
        "description": "Add email validation to user registration form"
      },
      {
        "index": 4,
        "description": "Implement password reset functionality"
      },
      {
        "index": 5,
        "description": "Add two-factor authentication support"
      }
    ]
  },
  "executions": [
    {
      "execution_id": "exec-001-task-1",
      "task_index": 1,
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [
        {
          "operation_id": "op-001",
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "execution_id": "exec-002-task-2",
      "task_index": 2,
      "pr_number": 42,
      "branch_name": "claudestep/auth-refactor/step-2",
      "reviewer": "alice",
      "pr_state": "open",
      "created_at": "2025-12-29T10:30:00Z",
      "ai_operations": [
        {
          "operation_id": "op-002",
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T10:30:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 5000,
          "tokens_output": 2000,
          "duration_seconds": 45.2
        }
      ]
    }
  ]
}
```

### Example: Task with Multiple Executions (Failed Then Succeeded)

This shows Task 1 with two execution attempts: first was closed without merging, second succeeded.

```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T16:00:00Z",
  "spec": {
    "tasks": [
      {
        "index": 1,
        "description": "Set up authentication middleware"
      }
    ]
  },
  "executions": [
    {
      "execution_id": "exec-001-task-1-attempt-1",
      "task_index": 1,
      "pr_number": 40,
      "branch_name": "claudestep/auth-refactor/step-1-attempt-1",
      "reviewer": "bob",
      "pr_state": "closed",
      "created_at": "2025-12-27T09:00:00Z",
      "ai_operations": [
        {
          "operation_id": "op-001",
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-27T09:00:00Z",
          "workflow_run_id": 123440,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "execution_id": "exec-001-task-1-attempt-2",
      "task_index": 1,
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [
        {
          "operation_id": "op-005",
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    }
  ]
}
```

### Example: Execution with Multiple AI Operations (Refinements)

This shows an execution with initial creation plus two refinement operations.

```json
{
  "execution_id": "exec-001-task-1",
  "task_index": 1,
  "pr_number": 41,
  "branch_name": "claudestep/auth-refactor/step-1",
  "reviewer": "bob",
  "pr_state": "merged",
  "created_at": "2025-12-28T14:20:00Z",
  "ai_operations": [
    {
      "operation_id": "op-001",
      "type": "PRCreation",
      "model": "claude-sonnet-4",
      "cost_usd": 0.12,
      "created_at": "2025-12-28T14:20:00Z",
      "workflow_run_id": 123450,
      "tokens_input": 4500,
      "tokens_output": 1800,
      "duration_seconds": 42.1
    },
    {
      "operation_id": "op-002",
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.08,
      "created_at": "2025-12-28T16:45:00Z",
      "workflow_run_id": 123451,
      "tokens_input": 3000,
      "tokens_output": 1200,
      "duration_seconds": 28.5
    },
    {
      "operation_id": "op-003",
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.06,
      "created_at": "2025-12-28T18:15:00Z",
      "workflow_run_id": 123452,
      "tokens_input": 2500,
      "tokens_output": 1000,
      "duration_seconds": 22.3
    }
  ]
}
```

### How This Model Handles Different Scenarios

#### 1. Not-Yet-Started Tasks

**Current Model:**
```json
{
  "step_index": 3,
  "step_description": "Add email validation"
}
```

**Alternative Model 1:**
```json
// Task appears only in spec
{
  "spec": {
    "tasks": [
      {"index": 3, "description": "Add email validation"}
    ]
  },
  "executions": []  // No executions yet
}
```

**Key Difference:**
- Current: Minimal Step object with optional fields
- Alternative 1: Task definition exists in spec, absence from executions indicates "not started"
- **Benefit:** No special case handling - a task either has executions or it doesn't

#### 2. Multiple Attempts at Same Task

**Current Model:**
Not directly supported. Would need to either:
- Overwrite the Step record (losing history)
- Add array of attempts (major schema change)

**Alternative Model 1:**
```json
{
  "spec": {
    "tasks": [{"index": 1, "description": "Set up auth middleware"}]
  },
  "executions": [
    {
      "execution_id": "exec-001-attempt-1",
      "task_index": 1,
      "pr_number": 40,
      "pr_state": "closed",
      "created_at": "2025-12-27T09:00:00Z",
      "ai_operations": [...]
    },
    {
      "execution_id": "exec-001-attempt-2",
      "task_index": 1,
      "pr_number": 41,
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [...]
    }
  ]
}
```

**Benefit:** Multiple executions with same `task_index` naturally represent retry attempts. Complete history preserved.

#### 3. PR Refinements

**Current Model:**
```json
{
  "step_index": 1,
  "step_description": "Set up auth middleware",
  "pr_number": 41,
  "ai_tasks": [
    {"type": "PRCreation", "cost_usd": 0.12, ...},
    {"type": "PRRefinement", "cost_usd": 0.08, ...}
  ]
}
```

**Alternative Model 1:**
```json
{
  "executions": [
    {
      "execution_id": "exec-001",
      "task_index": 1,
      "pr_number": 41,
      "ai_operations": [
        {"type": "PRCreation", "cost_usd": 0.12, ...},
        {"type": "PRRefinement", "cost_usd": 0.08, ...}
      ]
    }
  ]
}
```

**Similarity:** Both models handle this similarly with an array of operations/tasks
**Difference:** Alternative 1 makes the execution boundary more explicit

### Pros and Cons vs Current Model

#### Pros ✅

1. **Clear Separation of Concerns**
   - Spec defines "what needs to be done" (immutable)
   - Executions track "what was done" (mutable)
   - No confusion about whether a field represents plan vs execution

2. **Explicit Entity Boundaries**
   - `TaskDefinition` is always lightweight (just index + description)
   - `Execution` is always fully-formed (never has optional PR fields)
   - No "two modes" of the same entity type

3. **Natural Support for Retries**
   - Multiple executions for same `task_index` naturally represent retry attempts
   - Complete history of all attempts preserved
   - Current model would require major restructuring to support this

4. **Reduced Optional Fields**
   - `TaskDefinition` has no optional fields
   - `Execution` has no optional fields (every execution is a PR)
   - Easier to reason about: "Does this task have executions? If yes, check their states"

5. **Better Mental Model Alignment**
   - Users think: "Here's my plan (spec.md)" + "Here's what happened (PRs)"
   - Model directly reflects this mental model
   - Current model conflates these concepts into "Step"

6. **Clearer Queries**
   ```python
   # Find not-yet-started tasks
   started_indices = {e.task_index for e in project.executions}
   not_started = [t for t in project.spec.tasks if t.index not in started_indices]

   # Find task with multiple attempts
   from collections import Counter
   attempts = Counter(e.task_index for e in project.executions)
   retried_tasks = [idx for idx, count in attempts.items() if count > 1]
   ```

7. **Spec.md as Source of Truth**
   - Spec explicitly stored, making it clear that task descriptions come from spec.md
   - If spec.md changes, we can compare against stored spec to detect drift
   - Current model's implicit spec makes this harder to reason about

#### Cons ❌

1. **More Complex Structure**
   - Three-level hierarchy (Project → Spec/Executions → Tasks/Operations) vs two-level
   - Requires understanding the Spec vs Execution distinction
   - More conceptual overhead for developers

2. **Increased JSON Verbosity**
   - Task descriptions duplicated in both spec and execution references
   - Not-yet-started tasks still appear in spec (current model is minimal)
   - Actually, this is debatable - current model also stores all tasks

3. **More Complex Queries for Common Cases**
   ```python
   # Current: Get task status
   if step.pr_state == "merged": ...

   # Alternative 1: Get task status (requires joining spec + executions)
   task_executions = [e for e in project.executions if e.task_index == task.index]
   if task_executions:
       latest = max(task_executions, key=lambda e: e.created_at)
       if latest.pr_state == "merged": ...
   ```

4. **Data Consistency Risks**
   - Must ensure `task_index` in executions always references valid spec task
   - Must ensure execution IDs are unique
   - More relationships to validate

5. **Migration Effort**
   - Existing metadata needs transformation from Step → Spec + Execution
   - All code that reads/writes metadata needs updates
   - Testing burden to ensure migration correctness

6. **Not Addressing All Current Pain Points**
   - Still has denormalized data (task descriptions in spec)
   - Still needs to check PR state for status
   - Doesn't add explicit status enum (pending/in_progress/completed)

#### Neutral Observations 🤔

1. **Spec Mutability**
   - Spec is labeled "immutable" but must be updated when spec.md changes
   - Question: Should spec be regenerated from spec.md on every run? Or cached?
   - If regenerated, storing it seems redundant
   - If cached, what happens when spec.md changes?

2. **Execution ID Purpose**
   - What's the use case for `execution_id`?
   - PRs already have unique `pr_number`
   - Seems like over-engineering unless we need to support PRs outside GitHub

3. **Task Index Fragility**
   - Both models use task index as permanent identifier
   - Both break if tasks are reordered in spec.md
   - This isn't a Pro/Con difference, just a shared limitation

### Analysis Summary

**Does this feel more natural?**

**Yes, conceptually:** The separation of "plan" (spec) and "execution" (PRs) matches how users think about ClaudeStep. It's intellectually cleaner.

**No, pragmatically:** For the current ClaudeStep use case (single execution per task, no retries), the added complexity doesn't provide much benefit. The current model's main pain point (optional fields) could be addressed with simpler changes (like adding explicit status enums).

**Sweet spot:** This model would be valuable if ClaudeStep plans to support:
- Retry logic (PR closed, try again)
- Multiple implementation strategies (try approach A, if it fails try approach B)
- Execution history tracking (show all attempts over time)

**Recommendation for ClaudeStep:** Unless retry/multi-attempt support is planned, this model may be over-engineered. Alternative 3 (Hybrid) might offer a better balance.

**Technical Notes:**
- Implementation would require new dataclasses: `ProjectSpec`, `TaskDefinition`, `Execution`, `AIOperation`
- Migration script needed to transform existing `Step` records into `spec.tasks` + `executions`
- Query patterns would need adjustment to join spec and executions
- Backward compatibility would be challenging due to structural differences

## Phase 3: Alternative Model 2 - PR-Centric ✅

**Concept:**
```
Project
  ├── total_tasks: int (from spec.md)
  └── pull_requests: List[PullRequest]
      ├── task_index, task_description (copied from spec.md)
      ├── pr_number, branch, reviewer, state, created_at
      └── ai_operations: List[AIOperation]
          └── workflow_run_id, type, model, cost, tokens
```

**Key Ideas:**
- **PR is the primary entity**: Everything centers around PRs
- **No separate "not started" representation**: PRs that don't exist yet simply aren't in the list
- **Spec.md info copied into PR**: Task index/description duplicated (denormalized)
- **Progress calculated**: Compare PR count to total_tasks

### Detailed Structure Diagram

```
Project
├── schema_version: str                   # Metadata format version (e.g., "1.0")
├── project: str                          # Project name/identifier
├── last_updated: datetime                # Last modification timestamp
├── total_tasks: int                      # Total number of tasks in spec.md
└── pull_requests: List[PullRequest]      # All PRs (started tasks only)
    └── PullRequest
        ├── task_index: int               # Position in spec.md (1-based)
        ├── task_description: str         # Task description from spec.md (denormalized)
        ├── pr_number: int                # GitHub PR number
        ├── branch_name: str              # Git branch for this PR
        ├── reviewer: str                 # Assigned reviewer username
        ├── pr_state: str                 # "open", "merged", "closed"
        ├── created_at: datetime          # When PR was created
        └── ai_operations: List[AIOperation]  # All AI work for this PR
            └── AIOperation
                ├── type: str                 # "PRCreation", "PRRefinement", "PRSummary"
                ├── model: str                # AI model used (e.g., "claude-sonnet-4")
                ├── cost_usd: float           # Cost for this operation
                ├── created_at: datetime      # When this operation was executed
                ├── workflow_run_id: int      # GitHub Actions run that executed this
                ├── tokens_input: int         # Input tokens (default: 0)
                ├── tokens_output: int        # Output tokens (default: 0)
                └── duration_seconds: float   # Execution time (default: 0.0)
```

### Key Characteristics

1. **PR as Primary Entity**: The model is organized around PRs. If a PR doesn't exist, the task is simply not in the list.

2. **Denormalized Data**: Task index and description are copied from spec.md into each PullRequest record. This means:
   - No need to join with spec.md to get task info
   - Historical record preserved even if spec.md changes
   - Some data duplication

3. **Progress Tracking**: Progress is calculated by comparing the count of PRs to `total_tasks`:
   - Pending tasks = `total_tasks - len(pull_requests)`
   - Which tasks are pending requires tracking completed indices

4. **Minimal Schema**: Simplest possible structure - just project metadata + flat list of PRs

### Example JSON: Auth Refactor Project

This example shows the same 5-task project as previous alternatives:
- Task 1: Merged
- Task 2: In progress
- Tasks 3-5: Not started (not in PR list)

```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T10:30:00Z",
  "total_tasks": 5,
  "pull_requests": [
    {
      "task_index": 1,
      "task_description": "Set up authentication middleware",
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "task_index": 2,
      "task_description": "Implement OAuth2 authentication flow",
      "pr_number": 42,
      "branch_name": "claudestep/auth-refactor/step-2",
      "reviewer": "alice",
      "pr_state": "open",
      "created_at": "2025-12-29T10:30:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T10:30:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 5000,
          "tokens_output": 2000,
          "duration_seconds": 45.2
        }
      ]
    }
  ]
}
```

**Note:** Tasks 3, 4, and 5 are not represented in the JSON at all - their absence indicates they haven't been started yet.

### Example: PR with Multiple AI Operations (Refinements)

This shows a PR with initial creation plus two refinement operations:

```json
{
  "task_index": 1,
  "task_description": "Set up authentication middleware",
  "pr_number": 41,
  "branch_name": "claudestep/auth-refactor/step-1",
  "reviewer": "bob",
  "pr_state": "merged",
  "created_at": "2025-12-28T14:20:00Z",
  "ai_operations": [
    {
      "type": "PRCreation",
      "model": "claude-sonnet-4",
      "cost_usd": 0.12,
      "created_at": "2025-12-28T14:20:00Z",
      "workflow_run_id": 123450,
      "tokens_input": 4500,
      "tokens_output": 1800,
      "duration_seconds": 42.1
    },
    {
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.08,
      "created_at": "2025-12-28T16:45:00Z",
      "workflow_run_id": 123451,
      "tokens_input": 3000,
      "tokens_output": 1200,
      "duration_seconds": 28.5
    },
    {
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.06,
      "created_at": "2025-12-28T18:15:00Z",
      "workflow_run_id": 123452,
      "tokens_input": 2500,
      "tokens_output": 1000,
      "duration_seconds": 22.3
    }
  ]
}
```

### How This Model Handles Different Scenarios

#### 1. Not-Yet-Started Tasks

**Current Model:**
```json
{
  "step_index": 3,
  "step_description": "Add email validation"
}
```

**Alternative Model 1 (Spec/Exec):**
```json
{
  "spec": {
    "tasks": [
      {"index": 3, "description": "Add email validation"}
    ]
  },
  "executions": []
}
```

**Alternative Model 2 (PR-Centric):**
```json
{
  "total_tasks": 5,
  "pull_requests": []  // Task 3 is simply not in the list
}
```

**Key Difference:**
- **Current Model**: Minimal Step object with optional fields
- **Alternative 1**: Task exists in spec, no executions
- **Alternative 2**: Task doesn't appear at all - must infer from `total_tasks` and missing indices
- **Trade-off**: Most compact JSON but loses explicit task listing

#### 2. Calculating Pending Tasks

```python
# Get count of pending tasks
pending_count = project.total_tasks - len(project.pull_requests)

# Determine which specific tasks are pending (requires tracking)
completed_indices = {pr.task_index for pr in project.pull_requests}
pending_indices = [i for i in range(1, project.total_tasks + 1)
                   if i not in completed_indices]
```

**Issue**: To show *which* tasks are pending, you need to:
1. Know the total task count
2. Collect all task indices from PRs
3. Infer missing indices
4. Go back to spec.md to get task descriptions

This is more complex than current model where all tasks are always present.

#### 3. Progress Statistics

```python
# Project completion percentage
total = project.total_tasks
started = len(project.pull_requests)
completed = sum(1 for pr in project.pull_requests if pr.pr_state == "merged")
in_progress = sum(1 for pr in project.pull_requests if pr.pr_state == "open")
pending = total - started

completion_pct = (completed / total) * 100 if total > 0 else 0
```

**Comparison to Current Model:**
```python
# Current model - all tasks always present
total = len(project.steps)
completed = sum(1 for s in project.steps if s.pr_state == "merged")
in_progress = sum(1 for s in project.steps if s.pr_state == "open")
pending = sum(1 for s in project.steps if not s.is_started())
```

**Key Difference**: Current model is clearer because you can iterate over all steps. PR-Centric requires maintaining `total_tasks` separately.

#### 4. Reviewer Capacity Checking

```python
# Count open PRs per reviewer
open_prs_by_reviewer = {}
for pr in project.pull_requests:
    if pr.pr_state == "open":
        open_prs_by_reviewer.setdefault(pr.reviewer, []).append(pr)
```

**Same as current model** - straightforward iteration.

#### 5. Cost Analysis

```python
# Sum costs by project, model, time period
total_cost = 0
cost_by_model = {}

for pr in project.pull_requests:
    for op in pr.ai_operations:
        total_cost += op.cost_usd
        cost_by_model.setdefault(op.model, 0)
        cost_by_model[op.model] += op.cost_usd
```

**Same as current model** - straightforward nested iteration.

#### 6. Next Step Selection

```python
# Find the next pending task to work on
completed_indices = {pr.task_index for pr in project.pull_requests}

for task_index in range(1, project.total_tasks + 1):
    if task_index not in completed_indices:
        # This is the next pending task
        # But we don't have the description!
        # Must read from spec.md
        next_task_index = task_index
        break
```

**Problem**: Unlike current model where task descriptions are always present, this model requires reading spec.md to get task descriptions for pending tasks.

### Pros and Cons vs Current Model and Alternative 1

#### Pros ✅

1. **Simplest Possible Structure**
   - No optional fields on PullRequest (every PR has all fields)
   - No nested hierarchy beyond Project → PR → Operation
   - Flat list of PRs is easy to understand

2. **Minimal JSON for Early Projects**
   - Project with no started tasks: just `{"total_tasks": 5, "pull_requests": []}`
   - Most compact representation for projects with few PRs

3. **PR-Centric Mental Model**
   - Aligns with "ClaudeStep creates PRs" framing
   - Natural for developers who think in terms of PRs
   - No confusion about "what is a Step?"

4. **No Special Cases**
   - A PR either exists or it doesn't
   - No "minimal step" vs "full step" distinction
   - All PRs have the same structure

5. **Easy Capacity Checking**
   - Just iterate over PRs and count by state/reviewer
   - No need to filter out not-started items

6. **Clean History**
   - Only tracks what actually happened (PRs created)
   - No placeholder entries for future work

#### Cons ❌

1. **Loses Explicit Task Listing**
   - Not-yet-started tasks don't appear anywhere in metadata
   - Must infer pending tasks from missing indices
   - To show task descriptions, must re-read spec.md every time

   **Example:**
   ```python
   # Current model - task descriptions always available
   for step in project.steps:
       print(f"{step.step_index}: {step.step_description}")

   # PR-Centric - must join with spec.md
   tasks_from_spec = parse_spec_md("spec.md")  # Must re-read file
   completed_indices = {pr.task_index for pr in project.pull_requests}
   for task in tasks_from_spec:
       if task.index not in completed_indices:
           print(f"{task.index}: {task.description}")
   ```

2. **Requires Maintaining total_tasks**
   - Must update `total_tasks` whenever spec.md changes
   - If spec.md adds/removes tasks, `total_tasks` becomes stale
   - No way to detect this inconsistency

3. **More Complex "Next Task" Selection**
   ```python
   # Current model
   next_step = next(s for s in project.steps if not s.is_started())

   # PR-Centric model
   completed_indices = {pr.task_index for pr in project.pull_requests}
   next_index = next(i for i in range(1, total_tasks + 1)
                     if i not in completed_indices)
   # But we still don't have the description! Must read spec.md
   ```

4. **Denormalized Data Risks**
   - Task descriptions copied from spec.md into each PR
   - If spec.md is updated, metadata has stale descriptions
   - No single source of truth for task definitions

5. **Cannot Show Complete Project View**
   - "Show me all tasks and their statuses" requires joining with spec.md
   - Current model always has complete view in metadata
   - PR-Centric requires file I/O to answer this question

6. **Index Gaps Are Ambiguous**
   ```python
   # If PRs have task_index [1, 2, 4, 5] and total_tasks = 5
   # Is task 3 pending? Or was it deleted from spec.md?
   # No way to tell from metadata alone
   ```

7. **Spec.md Dependency**
   - Many operations require reading spec.md in addition to metadata
   - Current model: metadata is self-contained for most queries
   - PR-Centric: metadata + spec.md needed for full picture

8. **Not Addressing Current Pain Points**
   - Still has optional fields issue (total_tasks can be stale)
   - Still has denormalized data (task descriptions)
   - Doesn't add explicit status enum
   - Actually makes some queries harder

#### Neutral Observations 🤔

1. **total_tasks Semantics**
   - Is this "tasks at time of last update" or "current task count in spec.md"?
   - If spec.md is the source of truth, why cache the count?
   - If metadata is the source of truth, why not store task definitions?

2. **Multiple Attempts at Same Task**
   - Model doesn't explicitly support retry attempts
   - Would need to track multiple PRs with same `task_index`
   - Could work but feels awkward (same as current model)

3. **Spec.md vs Metadata Relationship**
   - Model assumes spec.md is always available and authoritative
   - But then why store `task_description` in PR metadata?
   - Seems to want to be both dependent on and independent from spec.md

### Analysis Summary

**Does this feel more natural?**

**For PR-focused workflows:** Yes, if you primarily think about "PRs we've created" rather than "tasks we planned". The model is simpler and more compact.

**For planning-focused workflows:** No, because you lose the explicit task list. Every query about pending work requires re-reading spec.md.

**Trade-offs:**
- ✅ **Simplicity**: Simplest possible structure, no optional fields on PRs
- ❌ **Completeness**: Cannot answer "what are all tasks?" from metadata alone
- ❌ **Spec.md dependency**: Many operations require spec.md file reads

**When This Model Works Well:**
- Small projects where re-reading spec.md is fast
- Workflows focused on PR status (open/merged) rather than task planning
- Cases where spec.md never changes after initial creation

**When This Model Struggles:**
- Showing comprehensive project status (pending/in-progress/completed tasks)
- Determining next task to work on (requires spec.md read)
- Detecting spec.md changes (no stored baseline to compare against)
- Large projects where re-parsing spec.md is expensive

**Comparison to Alternative 1 (Spec/Exec):**
- Alternative 1 is more complex but more complete
- Alternative 1 stores full spec, Alternative 2 loses it
- Alternative 1 better separates concerns
- Alternative 2 is simpler but requires more spec.md reads

**Comparison to Current Model:**
- Current model is more complete (all tasks always visible)
- PR-Centric is simpler (no optional fields on PRs)
- Current model is self-contained, PR-Centric requires spec.md
- Current model's pain point (optional fields on Step) is solved here, but at the cost of losing not-yet-started task visibility

**Recommendation for ClaudeStep:** This model is too minimal for ClaudeStep's needs. The project needs to show complete task lists, calculate progress, and select next tasks efficiently. Requiring spec.md reads for these common operations adds complexity rather than reducing it.

**Technical Notes:**
- Implementation would require new dataclasses: `Project`, `PullRequest`, `AIOperation`
- Migration would need to filter out not-yet-started Steps and set `total_tasks`
- Many query patterns would need to add spec.md reading logic
- Risk of `total_tasks` becoming stale if spec.md changes

## Phase 4: Alternative Model 3 - Hybrid Approach ✅

**Concept:**
```
Project
  ├── tasks: List[Task]
  │   └── index, description, status (pending/in_progress/completed)
  └── pull_requests: List[PullRequest]
      ├── task_index (reference)
      ├── pr_number, branch, reviewer, state, created_at
      └── ai_operations: List[AIOperation]
          └── workflow_run_id, type, model, cost, tokens
```

**Key Ideas:**
- **Task**: Lightweight reference to spec.md (always present)
- **Status enum**: Explicit state machine (pending → in_progress → completed)
- **PullRequest**: Execution details, references task by index
- **Clear separation**: Task is "what" (spec), PR is "how" (execution)

### Detailed Structure Diagram

```
Project
├── schema_version: str                   # Metadata format version (e.g., "1.0")
├── project: str                          # Project name/identifier
├── last_updated: datetime                # Last modification timestamp
├── tasks: List[Task]                     # All tasks from spec.md (always present)
│   └── Task
│       ├── index: int                    # Position in spec.md (1-based)
│       ├── description: str              # Task description from spec.md
│       └── status: TaskStatus            # Enum: "pending" | "in_progress" | "completed"
└── pull_requests: List[PullRequest]      # All PRs created (execution history)
    └── PullRequest
        ├── task_index: int               # References Task.index
        ├── pr_number: int                # GitHub PR number
        ├── branch_name: str              # Git branch for this PR
        ├── reviewer: str                 # Assigned reviewer username
        ├── pr_state: str                 # "open", "merged", "closed"
        ├── created_at: datetime          # When PR was created
        └── ai_operations: List[AIOperation]  # All AI work for this PR
            └── AIOperation
                ├── type: str                 # "PRCreation", "PRRefinement", "PRSummary"
                ├── model: str                # AI model used (e.g., "claude-sonnet-4")
                ├── cost_usd: float           # Cost for this operation
                ├── created_at: datetime      # When this operation was executed
                ├── workflow_run_id: int      # GitHub Actions run that executed this
                ├── tokens_input: int         # Input tokens (default: 0)
                ├── tokens_output: int        # Output tokens (default: 0)
                └── duration_seconds: float   # Execution time (default: 0.0)

TaskStatus: Enum
├── "pending"       # Not yet started
├── "in_progress"   # PR created but not merged
└── "completed"     # PR merged
```

### Key Relationships and Design Decisions

#### 1. Task → PullRequest Relationship

**One-to-One (Primary Case):**
- Most tasks have exactly one PR
- PR's `task_index` references `Task.index`
- Task's `status` is derived from PR state:
  - No PR for this task → `status = "pending"`
  - PR exists and `pr_state = "open"` → `status = "in_progress"`
  - PR exists and `pr_state = "merged"` → `status = "completed"`

**One-to-Many (Retry Case):**
- If a task has multiple PRs (e.g., first PR was closed, second PR succeeded):
  - Multiple PRs can reference the same `task_index`
  - Task status is determined by the latest PR (by `created_at`)
  - All PR history is preserved

**Example Query:**
```python
# Get PR for a specific task
prs_for_task = [pr for pr in project.pull_requests if pr.task_index == task.index]
if prs_for_task:
    latest_pr = max(prs_for_task, key=lambda pr: pr.created_at)
    # Use latest_pr to determine task status
```

#### 2. Task Status Synchronization

The `status` field on `Task` is **derived** from PR state, not independently set:

```python
def calculate_task_status(task: Task, pull_requests: List[PullRequest]) -> TaskStatus:
    """Calculate task status from PR state"""
    prs_for_task = [pr for pr in pull_requests if pr.task_index == task.index]

    if not prs_for_task:
        return TaskStatus.PENDING

    latest_pr = max(prs_for_task, key=lambda pr: pr.created_at)

    if latest_pr.pr_state == "merged":
        return TaskStatus.COMPLETED
    elif latest_pr.pr_state in ["open", "closed"]:
        return TaskStatus.IN_PROGRESS
    else:
        return TaskStatus.PENDING
```

**Why derive instead of store?**
- Single source of truth (PR state)
- No risk of status/PR state becoming inconsistent
- Simpler updates: just update PR state, status follows automatically

#### 3. Explicit vs Implicit Status

**This model chooses: Explicit status field**

Rationale:
- Makes queries clearer: `task.status == TaskStatus.COMPLETED` vs checking PR state
- Enables faster filtering without PR lookups
- Documents the state machine clearly in the type system
- Status can be computed on load and cached in the object

### Example JSON: Auth Refactor Project

This example shows a project with 5 tasks:
- Task 1: Merged (completed)
- Task 2: In progress (open PR)
- Task 3: Pending (not started)
- Task 4: Pending (not started)
- Task 5: Pending (not started)

```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T10:30:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Set up authentication middleware",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Implement OAuth2 authentication flow",
      "status": "in_progress"
    },
    {
      "index": 3,
      "description": "Add email validation to user registration form",
      "status": "pending"
    },
    {
      "index": 4,
      "description": "Implement password reset functionality",
      "status": "pending"
    },
    {
      "index": 5,
      "description": "Add two-factor authentication support",
      "status": "pending"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "task_index": 2,
      "pr_number": 42,
      "branch_name": "claudestep/auth-refactor/step-2",
      "reviewer": "alice",
      "pr_state": "open",
      "created_at": "2025-12-29T10:30:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T10:30:00Z",
          "workflow_run_id": 123456,
          "tokens_input": 5000,
          "tokens_output": 2000,
          "duration_seconds": 45.2
        }
      ]
    }
  ]
}
```

### Example: Task with Multiple PRs (Retry Scenario)

This shows Task 1 with two PR attempts: first was closed, second succeeded.

```json
{
  "schema_version": "1.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T16:00:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Set up authentication middleware",
      "status": "completed"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 40,
      "branch_name": "claudestep/auth-refactor/step-1-attempt-1",
      "reviewer": "bob",
      "pr_state": "closed",
      "created_at": "2025-12-27T09:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-27T09:00:00Z",
          "workflow_run_id": 123440,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "task_index": 1,
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-28T14:20:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T14:20:00Z",
          "workflow_run_id": 123450,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    }
  ]
}
```

**Note:** Task status is "completed" based on the latest PR (PR #41, merged).

### Example: PR with Multiple AI Operations (Refinements)

This shows a PR with initial creation plus two refinement operations:

```json
{
  "task_index": 1,
  "pr_number": 41,
  "branch_name": "claudestep/auth-refactor/step-1",
  "reviewer": "bob",
  "pr_state": "merged",
  "created_at": "2025-12-28T14:20:00Z",
  "ai_operations": [
    {
      "type": "PRCreation",
      "model": "claude-sonnet-4",
      "cost_usd": 0.12,
      "created_at": "2025-12-28T14:20:00Z",
      "workflow_run_id": 123450,
      "tokens_input": 4500,
      "tokens_output": 1800,
      "duration_seconds": 42.1
    },
    {
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.08,
      "created_at": "2025-12-28T16:45:00Z",
      "workflow_run_id": 123451,
      "tokens_input": 3000,
      "tokens_output": 1200,
      "duration_seconds": 28.5
    },
    {
      "type": "PRRefinement",
      "model": "claude-sonnet-4",
      "cost_usd": 0.06,
      "created_at": "2025-12-28T18:15:00Z",
      "workflow_run_id": 123452,
      "tokens_input": 2500,
      "tokens_output": 1000,
      "duration_seconds": 22.3
    }
  ]
}
```

### How This Model Handles Different Scenarios

#### 1. Not-Yet-Started Tasks

**Current Model:**
```json
{
  "step_index": 3,
  "step_description": "Add email validation"
}
```

**Alternative 1 (Spec/Exec):**
```json
{
  "spec": {
    "tasks": [{"index": 3, "description": "Add email validation"}]
  },
  "executions": []
}
```

**Alternative 2 (PR-Centric):**
```json
{
  "total_tasks": 5,
  "pull_requests": []  // Task 3 not in list
}
```

**Alternative 3 (Hybrid):**
```json
{
  "tasks": [
    {
      "index": 3,
      "description": "Add email validation",
      "status": "pending"
    }
  ],
  "pull_requests": []
}
```

**Key Difference:**
- Current: Minimal object with optional fields
- Alternative 1: Task in spec, no execution
- Alternative 2: Task not represented at all
- **Alternative 3: Task explicitly present with status "pending"**

**Benefits:**
- Task always visible in task list
- Clear status indicator without checking PR list
- No ambiguity about whether task exists

#### 2. Progress Statistics

```python
# Current model
total = len(project.steps)
completed = sum(1 for s in project.steps if s.pr_state == "merged")
in_progress = sum(1 for s in project.steps if s.pr_state == "open")
pending = sum(1 for s in project.steps if not s.is_started())

# Alternative 3 (Hybrid)
total = len(project.tasks)
completed = sum(1 for t in project.tasks if t.status == TaskStatus.COMPLETED)
in_progress = sum(1 for t in project.tasks if t.status == TaskStatus.IN_PROGRESS)
pending = sum(1 for t in project.tasks if t.status == TaskStatus.PENDING)

completion_pct = (completed / total) * 100 if total > 0 else 0
```

**Benefits:**
- Cleaner: iterate tasks, check status enum
- Faster: no need to check PR list
- More explicit: status is first-class concept

#### 3. Next Step Selection

```python
# Current model
next_step = next(s for s in project.steps if not s.is_started())

# Alternative 3 (Hybrid)
next_task = next(t for t in project.tasks if t.status == TaskStatus.PENDING)
```

**Benefits:**
- Simpler: just check status enum
- No method call (`is_started()`)
- Status is explicit, not derived

#### 4. Reviewer Capacity Checking

```python
# Both models work similarly
open_prs_by_reviewer = {}
for pr in project.pull_requests:
    if pr.pr_state == "open":
        open_prs_by_reviewer.setdefault(pr.reviewer, []).append(pr)
```

**No significant difference** - both iterate PRs.

#### 5. Cost Analysis

```python
# Both models work similarly
total_cost = 0
cost_by_model = {}

for pr in project.pull_requests:
    for op in pr.ai_operations:
        total_cost += op.cost_usd
        cost_by_model.setdefault(op.model, 0)
        cost_by_model[op.model] += op.cost_usd
```

**No significant difference** - both iterate PRs and operations.

#### 6. Multiple Attempts at Same Task

**Current Model:**
Not directly supported. Would need major restructuring.

**Alternative 1 (Spec/Exec):**
```python
# Multiple executions for same task_index
executions_for_task = [e for e in project.executions if e.task_index == 1]
```

**Alternative 3 (Hybrid):**
```python
# Multiple PRs for same task_index
prs_for_task = [pr for pr in project.pull_requests if pr.task_index == 1]
latest_pr = max(prs_for_task, key=lambda pr: pr.created_at)
```

**Benefits:**
- Natural support for retries (like Alternative 1)
- Complete history preserved
- Task status reflects latest attempt

### Pros and Cons vs All Previous Models

#### Pros ✅

**vs Current Model:**

1. **Explicit Status Enum**
   - Current: Must check optional fields and PR state to determine status
   - Hybrid: `task.status` is explicit and type-safe
   - Benefit: Clearer code, easier to reason about

2. **No Optional Fields Confusion**
   - Current: Step has many optional fields (pr_number, branch_name, etc.)
   - Hybrid: Task has no optional fields, PullRequest has no optional fields
   - Benefit: Two "modes" eliminated, every entity is fully formed

3. **Clearer Separation of Concerns**
   - Current: Step mixes task definition and PR execution
   - Hybrid: Task = "what" (spec), PullRequest = "how" (execution)
   - Benefit: Entity responsibilities are clear

4. **Better Support for Retries**
   - Current: Not supported without major changes
   - Hybrid: Multiple PRs can reference same task_index naturally
   - Benefit: Future-proof for retry logic

5. **Simpler Queries**
   ```python
   # Current: Check optional fields
   if step.pr_number and step.pr_state == "merged":
       ...

   # Hybrid: Check status enum
   if task.status == TaskStatus.COMPLETED:
       ...
   ```

**vs Alternative 1 (Spec/Exec):**

1. **Simpler Structure**
   - Alt 1: Project → Spec → Tasks + Project → Executions → Operations
   - Hybrid: Project → Tasks + Project → PullRequests → Operations
   - Benefit: One less nesting level (no Spec wrapper)

2. **Easier Status Checking**
   - Alt 1: Must join tasks and executions to determine status
   - Hybrid: Status is directly on Task object
   - Benefit: Faster queries, no joins needed

3. **Less Conceptual Overhead**
   - Alt 1: Must understand Spec vs Execution distinction
   - Hybrid: Task is just a task with a status
   - Benefit: Simpler mental model

**vs Alternative 2 (PR-Centric):**

1. **Complete Task Visibility**
   - Alt 2: Pending tasks not visible, must infer from total_tasks
   - Hybrid: All tasks always visible with explicit status
   - Benefit: Can iterate all tasks directly

2. **No Spec.md Dependency for Common Queries**
   - Alt 2: Must read spec.md to get pending task descriptions
   - Hybrid: Task descriptions always in metadata
   - Benefit: Metadata is self-contained

3. **Explicit Task List**
   - Alt 2: `total_tasks` can become stale if spec.md changes
   - Hybrid: Task list is explicit and kept in sync
   - Benefit: Easier to detect drift between spec.md and metadata

#### Cons ❌

**vs Current Model:**

1. **Migration Complexity**
   - Current → Hybrid requires:
     - Rename Step → Task
     - Extract PR fields into PullRequest object
     - Add status enum calculation
     - Transform AITask → AIOperation
   - Significant code changes across codebase

2. **More Objects**
   - Current: Project → Step → AITask (2 nested objects)
   - Hybrid: Project → Task, Project → PullRequest → AIOperation (3 parallel/nested)
   - Slightly more complex structure

3. **Status Synchronization**
   - Current: PR state is single source of truth
   - Hybrid: Status must be kept in sync with PR state
   - Risk of status/PR state becoming inconsistent if not careful

**vs Alternative 1 (Spec/Exec):**

1. **Less Conceptual Purity**
   - Alt 1: Clean separation of immutable spec and mutable executions
   - Hybrid: Tasks have mutable status, PRs reference tasks
   - Not as theoretically clean

2. **Status is Derived, Not Stored**
   - Alt 1: Status is purely derived from execution state
   - Hybrid: Status is stored (must be kept in sync)
   - More opportunity for inconsistency

**vs Alternative 2 (PR-Centric):**

1. **More JSON Verbosity**
   - Alt 2: Minimal JSON for pending tasks (not in list)
   - Hybrid: Every task is in JSON, even if pending
   - Larger file size for projects with many pending tasks

2. **Denormalized Data**
   - Alt 2: Task descriptions in PRs only
   - Hybrid: Task descriptions in Tasks AND referenced by PRs
   - Some duplication

#### Neutral Observations 🤔

1. **Status Derivation vs Storage**
   - Status could be computed on-the-fly from PRs (like Alt 1)
   - Or stored and updated when PR state changes (current design)
   - Trade-off: Consistency vs Performance

2. **Task Index Fragility**
   - All models use task index as identifier
   - All models break if spec.md tasks are reordered
   - Not a differentiator

3. **AI Operation vs AI Task Naming**
   - Alternative 3 uses "AIOperation"
   - Current uses "AITask"
   - Just terminology, no functional difference

### Analysis Summary

**Does this feel more natural than other alternatives?**

**Yes, for ClaudeStep's use case.**

**Why Hybrid is the Best Fit:**

1. **Balances Simplicity and Explicitness**
   - Simpler than Alternative 1 (no Spec wrapper, status on Task)
   - More complete than Alternative 2 (all tasks visible)
   - Clearer than Current (explicit status, separated concerns)

2. **Matches Mental Model**
   - Users think: "Here are my tasks (some pending, some done)"
   - Model: `tasks` list with status enum
   - Direct mapping = intuitive

3. **Solves Current Model's Main Pain Points**
   - ✅ Eliminates optional fields confusion
   - ✅ Makes status explicit (no more checking multiple fields)
   - ✅ Separates task definition from PR execution
   - ✅ Supports retries naturally

4. **Practical for ClaudeStep's Needs**
   - Fast progress queries (iterate tasks, check status)
   - Easy next-step selection (find first pending task)
   - Complete task visibility (no spec.md reads needed)
   - Self-contained metadata (all info in JSON)

5. **Good for Future Extensions**
   - Can support retry logic (multiple PRs per task)
   - Can add task priority/dependencies later
   - Status enum can be extended (e.g., "blocked", "failed")

**Recommendation:** Alternative 3 (Hybrid) should be the target model for ClaudeStep.

**Migration Strategy:**
1. Create new dataclasses alongside current ones
2. Add migration code to convert old format to new
3. Update all readers/writers to use new model
4. Deprecate old model after validation period

**Technical Notes:**
- Implementation files: `src/claudestep/domain/models.py`
- New dataclasses: `Task`, `TaskStatus` (enum), `PullRequest`, `AIOperation`, `Project`
- Status calculation: Derived from PR state on load, cached in Task object
- Backward compatibility: New schema version "2.0", can still read "1.0"

## Phase 5: Comparison Matrix ✅

**Tasks:**
- Create comparison table for all models:
  - **Columns**: Current Model, Alt 1 (Spec/Exec), Alt 2 (PR-Centric), Alt 3 (Hybrid)
  - **Rows**:
    - Clarity of relationships
    - Ease of querying for statistics
    - Handling not-yet-started tasks
    - Handling refinements
    - JSON verbosity
    - Code complexity
    - Migration effort from current
- Rate each aspect (👍 Good, 👌 OK, 👎 Poor)
- Identify recommended approach with rationale

**Expected Outcome:**
- Clear comparison showing trade-offs
- Recommendation for which model to pursue
- Migration path from current model

### Comparison Table

| Aspect | Current Model | Alt 1: Spec/Exec | Alt 2: PR-Centric | Alt 3: Hybrid |
|--------|--------------|------------------|-------------------|---------------|
| **Clarity of Relationships** | 👌 OK<br/>Step conflates task and PR | 👍 Good<br/>Clear spec vs execution separation | 👌 OK<br/>PR is central, tasks implicit | 👍 Good<br/>Task and PR clearly separated |
| **Ease of Querying for Statistics** | 👌 OK<br/>Iterate steps, check optional fields | 👎 Poor<br/>Must join tasks and executions | 👌 OK<br/>Simple for PRs, complex for tasks | 👍 Good<br/>Direct status enum checks |
| **Handling Not-Yet-Started Tasks** | 👌 OK<br/>Minimal Step with optional fields | 👍 Good<br/>In spec, no executions | 👎 Poor<br/>Not represented, must infer | 👍 Good<br/>Explicit pending status |
| **Handling Refinements** | 👍 Good<br/>Array of AITasks per Step | 👍 Good<br/>Array of AIOperations per Execution | 👍 Good<br/>Array of AIOperations per PR | 👍 Good<br/>Array of AIOperations per PR |
| **Handling Retries** | 👎 Poor<br/>Not supported | 👍 Good<br/>Multiple executions per task | 👌 OK<br/>Multiple PRs per task_index | 👍 Good<br/>Multiple PRs per task_index |
| **JSON Verbosity** | 👍 Good<br/>Compact for pending tasks | 👎 Poor<br/>Extra Spec wrapper level | 👍 Good<br/>Most compact | 👌 OK<br/>All tasks always present |
| **Code Complexity** | 👌 OK<br/>Optional field handling | 👎 Poor<br/>Most complex, joins needed | 👍 Good<br/>Simplest structure | 👍 Good<br/>Balanced complexity |
| **Self-Contained Metadata** | 👍 Good<br/>All task info in metadata | 👍 Good<br/>Full spec stored | 👎 Poor<br/>Requires spec.md reads | 👍 Good<br/>All task info in metadata |
| **Migration Effort** | N/A<br/>Already implemented | 👎 Poor<br/>Major restructuring | 👌 OK<br/>Moderate changes | 👌 OK<br/>Moderate changes |
| **Support for Future Features** | 👎 Poor<br/>Retries not supported | 👍 Good<br/>Designed for evolution | 👌 OK<br/>Limited by structure | 👍 Good<br/>Extensible status enum |
| **Mental Model Alignment** | 👌 OK<br/>Step is ambiguous | 👍 Good<br/>Matches plan vs execution | 👌 OK<br/>PR-focused workflows | 👍 Good<br/>Tasks with status |
| **Overall Score** | 👌 6/10<br/>Works but has pain points | 👌 7/10<br/>Thorough but complex | 👎 5/10<br/>Too minimal for needs | 👍 9/10<br/>Best balance |

### Detailed Aspect Analysis

#### 1. Clarity of Relationships

**Current Model: 👌 OK**
- Step tries to be both task definition and PR execution
- Relationships are implicit (Step contains PR fields)
- Works but creates conceptual confusion

**Alt 1 (Spec/Exec): 👍 Good**
- Clearest separation: Spec (immutable) vs Executions (mutable)
- Explicit relationship via task_index
- Most intellectually pure design

**Alt 2 (PR-Centric): 👌 OK**
- PRs are central, tasks are implicit
- Simple but loses task visibility
- Relationship between PR and task is clear (task_index)

**Alt 3 (Hybrid): 👍 Good**
- Clear separation: Task (what) vs PullRequest (how)
- Explicit relationship via task_index
- Balances clarity with simplicity

**Winner: Tie between Alt 1 and Alt 3**

#### 2. Ease of Querying for Statistics

**Current Model: 👌 OK**
```python
completed = sum(1 for s in project.steps if s.pr_state == "merged")
pending = sum(1 for s in project.steps if not s.is_started())
```
- Works but requires checking optional fields and method calls

**Alt 1 (Spec/Exec): 👎 Poor**
```python
started_indices = {e.task_index for e in project.executions}
pending = [t for t in project.spec.tasks if t.index not in started_indices]
```
- Requires joining tasks and executions
- Most complex for common queries

**Alt 2 (PR-Centric): 👌 OK**
```python
completed = sum(1 for pr in project.pull_requests if pr.pr_state == "merged")
pending = project.total_tasks - len(project.pull_requests)
```
- Simple for PR stats, but pending count only (not specific tasks)

**Alt 3 (Hybrid): 👍 Good**
```python
completed = sum(1 for t in project.tasks if t.status == TaskStatus.COMPLETED)
pending = sum(1 for t in project.tasks if t.status == TaskStatus.PENDING)
```
- Clearest and simplest
- Direct status enum checks
- No joins or optional field checks

**Winner: Alt 3 (Hybrid)**

#### 3. Handling Not-Yet-Started Tasks

**Current Model: 👌 OK**
- Minimal Step object with just index and description
- Most fields are optional
- Works but creates "two modes" problem

**Alt 1 (Spec/Exec): 👍 Good**
- Task exists in spec, no executions
- Natural representation
- No special cases

**Alt 2 (PR-Centric): 👎 Poor**
- Tasks not represented at all
- Must infer from missing indices
- Must read spec.md to get descriptions

**Alt 3 (Hybrid): 👍 Good**
- Explicit Task with status "pending"
- Always visible in task list
- No ambiguity

**Winner: Tie between Alt 1 and Alt 3**

#### 4. Handling Refinements

**All models: 👍 Good**

All models handle refinements the same way:
- Array of AI operations/tasks
- Each refinement adds another entry
- Chronological order preserved

No significant difference between models.

**Winner: Tie (all models)**

#### 5. Handling Retries

**Current Model: 👎 Poor**
- Not supported without major restructuring
- Would need to add array of PR attempts

**Alt 1 (Spec/Exec): 👍 Good**
- Multiple executions can reference same task_index
- Natural representation
- Complete history preserved

**Alt 2 (PR-Centric): 👌 OK**
- Multiple PRs can reference same task_index
- Works but feels less natural
- No explicit retry concept

**Alt 3 (Hybrid): 👍 Good**
- Multiple PRs can reference same task_index
- Task status reflects latest attempt
- Clean retry support

**Winner: Tie between Alt 1 and Alt 3**

#### 6. JSON Verbosity

**Current Model: 👍 Good**
```json
{"step_index": 3, "step_description": "Task 3"}
```
- Pending tasks are minimal (2 fields)

**Alt 1 (Spec/Exec): 👎 Poor**
```json
{
  "spec": {
    "tasks": [{"index": 1, "description": "..."}]
  },
  "executions": []
}
```
- Extra nesting level (Spec wrapper)
- Most verbose structure

**Alt 2 (PR-Centric): 👍 Good**
```json
{"total_tasks": 5, "pull_requests": []}
```
- Most compact for pending tasks (not in list)
- Smallest JSON for early projects

**Alt 3 (Hybrid): 👌 OK**
```json
{"tasks": [{"index": 1, "description": "...", "status": "pending"}], "pull_requests": []}
```
- All tasks always present
- Moderate verbosity

**Winner: Alt 2 (PR-Centric)**

#### 7. Code Complexity

**Current Model: 👌 OK**
- Two-level hierarchy
- Optional field handling throughout
- Mixed responsibilities in Step

**Alt 1 (Spec/Exec): 👎 Poor**
- Most complex structure
- Requires joins for common queries
- More concepts to understand

**Alt 2 (PR-Centric): 👍 Good**
- Simplest structure
- Flat list of PRs
- But requires spec.md reads

**Alt 3 (Hybrid): 👍 Good**
- Balanced complexity
- No joins needed
- Clear entity boundaries

**Winner: Tie between Alt 2 and Alt 3**

#### 8. Self-Contained Metadata

**Current Model: 👍 Good**
- All task descriptions in metadata
- No spec.md reads needed for queries

**Alt 1 (Spec/Exec): 👍 Good**
- Full spec stored in metadata
- Completely self-contained

**Alt 2 (PR-Centric): 👎 Poor**
- Pending task descriptions not available
- Must read spec.md for many queries

**Alt 3 (Hybrid): 👍 Good**
- All task descriptions in metadata
- Fully self-contained

**Winner: Tie between Current, Alt 1, and Alt 3**

#### 9. Migration Effort

**Current Model: N/A**
- Already implemented

**Alt 1 (Spec/Exec): 👎 Poor**
- Major restructuring required
- Extract spec from steps
- Transform Step → Execution
- Most code changes

**Alt 2 (PR-Centric): 👌 OK**
- Filter out pending steps
- Add total_tasks field
- Moderate code changes

**Alt 3 (Hybrid): 👌 OK**
- Rename Step → Task
- Extract PR fields → PullRequest
- Add status enum
- Moderate code changes

**Winner: Alt 2 and Alt 3 (similar effort)**

#### 10. Support for Future Features

**Current Model: 👎 Poor**
- Retries not supported
- Hard to extend with optional field pattern

**Alt 1 (Spec/Exec): 👍 Good**
- Designed for multiple executions
- Clear extension points
- Spec/Exec pattern is flexible

**Alt 2 (PR-Centric): 👌 OK**
- Can add retry support
- But limited by minimal structure

**Alt 3 (Hybrid): 👍 Good**
- Status enum extensible
- Supports retries
- Can add task metadata later

**Winner: Tie between Alt 1 and Alt 3**

#### 11. Mental Model Alignment

**Current Model: 👌 OK**
- "Step" is ambiguous
- Conflates plan and execution

**Alt 1 (Spec/Exec): 👍 Good**
- Matches "plan vs execution" mental model
- Clean conceptual separation

**Alt 2 (PR-Centric): 👌 OK**
- Good for PR-focused workflows
- Less clear for planning

**Alt 3 (Hybrid): 👍 Good**
- "Tasks with status" matches user thinking
- Natural progression: pending → in_progress → completed

**Winner: Tie between Alt 1 and Alt 3**

### Overall Recommendation

**Winner: Alternative 3 (Hybrid Approach)**

#### Rationale

**Why Alternative 3 wins:**

1. **Best Balance**: Combines simplicity of Alt 2 with completeness of Alt 1
2. **Clearest Queries**: Status enum makes common queries simple and explicit
3. **Self-Contained**: All task info available without spec.md reads
4. **Future-Proof**: Supports retries, extensible status enum
5. **Mental Model Match**: Tasks with status maps to how users think about projects
6. **Moderate Migration**: Similar effort to Alt 2, less than Alt 1
7. **No Optional Fields**: Eliminates current model's main pain point

**Why not Alternative 1 (Spec/Exec)?**

While intellectually pure, it's over-engineered for ClaudeStep's current needs:
- Extra complexity (joins) for common queries
- Most verbose JSON
- Hardest migration
- Benefit (complete spec/exec separation) doesn't outweigh costs

**Why not Alternative 2 (PR-Centric)?**

Too minimal:
- Loses pending task visibility
- Requires spec.md reads for common operations
- Makes progress tracking harder
- Simplicity comes at cost of usability

**Why not Current Model?**

Has identified pain points:
- Optional fields create confusion
- Mixed responsibilities in Step
- No retry support
- Status checking is implicit

### Migration Path

From Current Model to Alternative 3 (Hybrid):

#### Phase 1: Add New Dataclasses
```python
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class Task:
    index: int
    description: str
    status: TaskStatus

@dataclass
class PullRequest:
    task_index: int
    pr_number: int
    branch_name: str
    reviewer: str
    pr_state: str
    created_at: datetime
    ai_operations: List[AIOperation]

@dataclass
class AIOperation:  # Renamed from AITask
    type: str
    model: str
    cost_usd: float
    created_at: datetime
    workflow_run_id: int
    tokens_input: int = 0
    tokens_output: int = 0
    duration_seconds: float = 0.0
```

#### Phase 2: Migration Function
```python
def migrate_to_hybrid(current_project: Project) -> HybridProject:
    """Convert current model to hybrid model"""
    tasks = []
    pull_requests = []

    for step in current_project.steps:
        # Create Task
        if step.pr_state == "merged":
            status = TaskStatus.COMPLETED
        elif step.pr_number is not None:
            status = TaskStatus.IN_PROGRESS
        else:
            status = TaskStatus.PENDING

        task = Task(
            index=step.step_index,
            description=step.step_description,
            status=status
        )
        tasks.append(task)

        # Create PullRequest if started
        if step.pr_number is not None:
            pr = PullRequest(
                task_index=step.step_index,
                pr_number=step.pr_number,
                branch_name=step.branch_name,
                reviewer=step.reviewer,
                pr_state=step.pr_state,
                created_at=step.created_at,
                ai_operations=[
                    AIOperation(**ai_task.to_dict())
                    for ai_task in step.ai_tasks
                ]
            )
            pull_requests.append(pr)

    return HybridProject(
        schema_version="2.0",
        project=current_project.project,
        last_updated=current_project.last_updated,
        tasks=tasks,
        pull_requests=pull_requests
    )
```

#### Phase 3: Update Readers/Writers
- Update `MetadataStorage.read()` to detect schema version
- Support both "1.0" (current) and "2.0" (hybrid)
- Auto-migrate on read if needed
- Always write in "2.0" format

#### Phase 4: Update Queries
Replace:
```python
# Old
completed = sum(1 for s in project.steps if s.pr_state == "merged")
next_step = next(s for s in project.steps if not s.is_started())
```

With:
```python
# New
completed = sum(1 for t in project.tasks if t.status == TaskStatus.COMPLETED)
next_task = next(t for t in project.tasks if t.status == TaskStatus.PENDING)
```

#### Phase 5: Validation
- Run full test suite
- Verify migration with real data
- Ensure backward compatibility reads work
- Monitor for edge cases

### Implementation Checklist

- [ ] Create new dataclasses (Task, TaskStatus, PullRequest, AIOperation)
- [ ] Write migration function from current model
- [ ] Add schema version detection to MetadataStorage
- [ ] Update all query patterns in codebase
- [ ] Update tests to use new model
- [ ] Add migration tests
- [ ] Update documentation
- [ ] Deploy with migration support
- [ ] Monitor for issues
- [ ] Deprecate old model after validation period

**Technical Notes:**
- Schema version bumps to "2.0"
- Migration is one-way (no downgrade path needed)
- Old metadata auto-migrates on first read
- Status is derived from PR state, then cached
- All datetime fields continue using ISO 8601 format

## Phase 6: Detailed Design for Recommended Model ✅

**Tasks:**
- Create comprehensive diagram for recommended model
- Define complete JSON schema with all fields
- Show 3-5 realistic examples:
  - Empty project (no PRs yet)
  - Project with mix of states
  - Complex project with refinements and multiple workflows
- Document Python dataclass structure
- Document serialization methods (from_dict, to_dict)
- Show how to query for common operations:
  - Get reviewer capacity (open PRs per reviewer)
  - Calculate project completion percentage
  - Sum costs across project
  - List pending tasks

**Expected Outcome:**
- Complete specification ready for implementation
- All edge cases considered
- Clear migration strategy

### Comprehensive Model Diagram

The Alternative 3 (Hybrid) model structure with all fields and types:

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Project                                │
├─────────────────────────────────────────────────────────────────────┤
│ schema_version: str                    # "2.0" for hybrid model     │
│ project: str                           # Project identifier         │
│ last_updated: datetime                 # ISO 8601 timestamp         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────┐  ┌──────────────────────────┐  │
│  │          tasks: List            │  │  pull_requests: List     │  │
│  └────────────────────────────────┘  └──────────────────────────┘  │
│                │                                  │                 │
│                ▼                                  ▼                 │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐  │
│  │           Task               │  │      PullRequest           │  │
│  ├──────────────────────────────┤  ├────────────────────────────┤  │
│  │ index: int                   │  │ task_index: int ───────────┼──┼──> References Task.index
│  │ description: str             │  │ pr_number: int             │  │
│  │ status: TaskStatus (enum)    │  │ branch_name: str           │  │
│  │   - "pending"                │  │ reviewer: str              │  │
│  │   - "in_progress"            │  │ pr_state: str              │  │
│  │   - "completed"              │  │   - "open"                 │  │
│  └──────────────────────────────┘  │   - "merged"               │  │
│                                     │   - "closed"               │  │
│                                     │ created_at: datetime       │  │
│                                     ├────────────────────────────┤  │
│                                     │  ai_operations: List       │  │
│                                     └────────────────────────────┘  │
│                                                  │                 │
│                                                  ▼                 │
│                                     ┌────────────────────────────┐  │
│                                     │       AIOperation          │  │
│                                     ├────────────────────────────┤  │
│                                     │ type: str                  │  │
│                                     │   - "PRCreation"           │  │
│                                     │   - "PRRefinement"         │  │
│                                     │   - "PRSummary"            │  │
│                                     │ model: str                 │  │
│                                     │ cost_usd: float            │  │
│                                     │ created_at: datetime       │  │
│                                     │ workflow_run_id: int       │  │
│                                     │ tokens_input: int          │  │
│                                     │ tokens_output: int         │  │
│                                     │ duration_seconds: float    │  │
│                                     └────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Relationships:
  Task ←──[1:N]── PullRequest  (via task_index)
  PullRequest ←──[1:N]── AIOperation

Status Derivation:
  Task.status is derived from PullRequest.pr_state:
  - No PR for task → status = "pending"
  - PR exists, pr_state = "open" → status = "in_progress"
  - PR exists, pr_state = "merged" → status = "completed"
  - Multiple PRs → use latest by created_at
```

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ClaudeStep Hybrid Model",
  "type": "object",
  "required": ["schema_version", "project", "last_updated", "tasks", "pull_requests"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "2.0",
      "description": "Schema version identifier"
    },
    "project": {
      "type": "string",
      "description": "Project name/identifier, typically matches spec.md name"
    },
    "last_updated": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of last metadata update"
    },
    "tasks": {
      "type": "array",
      "description": "All tasks from spec.md, always present regardless of status",
      "items": {
        "type": "object",
        "required": ["index", "description", "status"],
        "properties": {
          "index": {
            "type": "integer",
            "minimum": 1,
            "description": "1-based position in spec.md, permanent identifier"
          },
          "description": {
            "type": "string",
            "minLength": 1,
            "description": "Task description from spec.md"
          },
          "status": {
            "type": "string",
            "enum": ["pending", "in_progress", "completed"],
            "description": "Task status derived from PR state"
          }
        }
      }
    },
    "pull_requests": {
      "type": "array",
      "description": "All PRs created, may have multiple PRs per task_index (retries)",
      "items": {
        "type": "object",
        "required": ["task_index", "pr_number", "branch_name", "reviewer", "pr_state", "created_at", "ai_operations"],
        "properties": {
          "task_index": {
            "type": "integer",
            "minimum": 1,
            "description": "References tasks[].index, indicates which task this PR implements"
          },
          "pr_number": {
            "type": "integer",
            "minimum": 1,
            "description": "GitHub pull request number"
          },
          "branch_name": {
            "type": "string",
            "minLength": 1,
            "description": "Git branch name for this PR"
          },
          "reviewer": {
            "type": "string",
            "minLength": 1,
            "description": "GitHub username of assigned reviewer"
          },
          "pr_state": {
            "type": "string",
            "enum": ["open", "merged", "closed"],
            "description": "Current state of the GitHub PR"
          },
          "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp when PR was created"
          },
          "ai_operations": {
            "type": "array",
            "minItems": 1,
            "description": "All AI operations performed for this PR, chronologically ordered",
            "items": {
              "type": "object",
              "required": ["type", "model", "cost_usd", "created_at", "workflow_run_id"],
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["PRCreation", "PRRefinement", "PRSummary"],
                  "description": "Type of AI operation performed"
                },
                "model": {
                  "type": "string",
                  "description": "AI model identifier (e.g., 'claude-sonnet-4')"
                },
                "cost_usd": {
                  "type": "number",
                  "minimum": 0,
                  "description": "Cost in USD for this operation"
                },
                "created_at": {
                  "type": "string",
                  "format": "date-time",
                  "description": "ISO 8601 timestamp when operation was performed"
                },
                "workflow_run_id": {
                  "type": "integer",
                  "minimum": 1,
                  "description": "GitHub Actions workflow run ID for debugging"
                },
                "tokens_input": {
                  "type": "integer",
                  "minimum": 0,
                  "default": 0,
                  "description": "Number of input tokens consumed"
                },
                "tokens_output": {
                  "type": "integer",
                  "minimum": 0,
                  "default": 0,
                  "description": "Number of output tokens generated"
                },
                "duration_seconds": {
                  "type": "number",
                  "minimum": 0,
                  "default": 0.0,
                  "description": "Execution time in seconds"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Example 1: Empty Project (No PRs Yet)

A freshly initialized project with all tasks pending:

```json
{
  "schema_version": "2.0",
  "project": "user-dashboard-redesign",
  "last_updated": "2025-12-29T08:00:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Update navigation component to use new design tokens",
      "status": "pending"
    },
    {
      "index": 2,
      "description": "Implement responsive grid layout for dashboard cards",
      "status": "pending"
    },
    {
      "index": 3,
      "description": "Add dark mode support to all components",
      "status": "pending"
    }
  ],
  "pull_requests": []
}
```

**Key Points:**
- All tasks are present with status "pending"
- Empty pull_requests array
- Minimal but complete representation
- Total size: ~500 bytes

### Example 2: Project with Mixed States

A mid-progress project showing all three task states:

```json
{
  "schema_version": "2.0",
  "project": "auth-refactor",
  "last_updated": "2025-12-29T14:30:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Set up authentication middleware",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Implement OAuth2 authentication flow",
      "status": "in_progress"
    },
    {
      "index": 3,
      "description": "Add email validation to user registration",
      "status": "pending"
    },
    {
      "index": 4,
      "description": "Implement password reset functionality",
      "status": "pending"
    },
    {
      "index": 5,
      "description": "Add two-factor authentication support",
      "status": "pending"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 41,
      "branch_name": "claudestep/auth-refactor/step-1",
      "reviewer": "alice",
      "pr_state": "merged",
      "created_at": "2025-12-28T10:15:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.12,
          "created_at": "2025-12-28T10:15:00Z",
          "workflow_run_id": 234567,
          "tokens_input": 4500,
          "tokens_output": 1800,
          "duration_seconds": 42.1
        }
      ]
    },
    {
      "task_index": 2,
      "pr_number": 42,
      "branch_name": "claudestep/auth-refactor/step-2",
      "reviewer": "bob",
      "pr_state": "open",
      "created_at": "2025-12-29T09:30:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T09:30:00Z",
          "workflow_run_id": 234570,
          "tokens_input": 5200,
          "tokens_output": 2100,
          "duration_seconds": 48.3
        }
      ]
    }
  ]
}
```

**Key Points:**
- Task 1: completed (PR merged)
- Task 2: in_progress (PR open)
- Tasks 3-5: pending (no PRs)
- Shows progression through project
- 2 reviewers with different assignments

### Example 3: Complex Project with Refinements

A task that went through multiple refinement cycles:

```json
{
  "schema_version": "2.0",
  "project": "api-performance-optimization",
  "last_updated": "2025-12-29T18:45:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Add database query caching layer",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Implement connection pooling",
      "status": "in_progress"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 101,
      "branch_name": "claudestep/api-performance/step-1",
      "reviewer": "charlie",
      "pr_state": "merged",
      "created_at": "2025-12-27T14:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.18,
          "created_at": "2025-12-27T14:00:00Z",
          "workflow_run_id": 345678,
          "tokens_input": 6800,
          "tokens_output": 2400,
          "duration_seconds": 52.7
        },
        {
          "type": "PRRefinement",
          "model": "claude-sonnet-4",
          "cost_usd": 0.09,
          "created_at": "2025-12-27T16:30:00Z",
          "workflow_run_id": 345680,
          "tokens_input": 3200,
          "tokens_output": 1400,
          "duration_seconds": 31.2
        },
        {
          "type": "PRRefinement",
          "model": "claude-sonnet-4",
          "cost_usd": 0.07,
          "created_at": "2025-12-28T09:15:00Z",
          "workflow_run_id": 345682,
          "tokens_input": 2800,
          "tokens_output": 1100,
          "duration_seconds": 26.8
        },
        {
          "type": "PRSummary",
          "model": "claude-haiku-4",
          "cost_usd": 0.02,
          "created_at": "2025-12-28T11:00:00Z",
          "workflow_run_id": 345685,
          "tokens_input": 1500,
          "tokens_output": 400,
          "duration_seconds": 8.3
        }
      ]
    },
    {
      "task_index": 2,
      "pr_number": 102,
      "branch_name": "claudestep/api-performance/step-2",
      "reviewer": "charlie",
      "pr_state": "open",
      "created_at": "2025-12-29T10:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.16,
          "created_at": "2025-12-29T10:00:00Z",
          "workflow_run_id": 345690,
          "tokens_input": 5900,
          "tokens_output": 2200,
          "duration_seconds": 47.5
        },
        {
          "type": "PRRefinement",
          "model": "claude-sonnet-4",
          "cost_usd": 0.08,
          "created_at": "2025-12-29T15:20:00Z",
          "workflow_run_id": 345692,
          "tokens_input": 3000,
          "tokens_output": 1300,
          "duration_seconds": 29.4
        }
      ]
    }
  ]
}
```

**Key Points:**
- Task 1 has 4 AI operations (1 creation + 2 refinements + 1 summary)
- Task 2 has 2 AI operations (1 creation + 1 refinement)
- Multiple workflow runs tracked per PR
- Different AI models used (Sonnet vs Haiku)
- Shows complete history of iterations
- Total cost for Task 1: $0.36

### Example 4: Retry Scenario (Multiple PRs per Task)

A task where the first PR was closed and a second attempt succeeded:

```json
{
  "schema_version": "2.0",
  "project": "payment-integration",
  "last_updated": "2025-12-29T20:00:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Integrate Stripe payment gateway",
      "status": "completed"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 50,
      "branch_name": "claudestep/payment/step-1-attempt-1",
      "reviewer": "dana",
      "pr_state": "closed",
      "created_at": "2025-12-26T09:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.14,
          "created_at": "2025-12-26T09:00:00Z",
          "workflow_run_id": 456789,
          "tokens_input": 5400,
          "tokens_output": 2000,
          "duration_seconds": 45.8
        }
      ]
    },
    {
      "task_index": 1,
      "pr_number": 51,
      "branch_name": "claudestep/payment/step-1-attempt-2",
      "reviewer": "dana",
      "pr_state": "merged",
      "created_at": "2025-12-27T14:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-27T14:00:00Z",
          "workflow_run_id": 456800,
          "tokens_input": 5600,
          "tokens_output": 2100,
          "duration_seconds": 47.2
        },
        {
          "type": "PRRefinement",
          "model": "claude-sonnet-4",
          "cost_usd": 0.08,
          "created_at": "2025-12-28T10:30:00Z",
          "workflow_run_id": 456805,
          "tokens_input": 3100,
          "tokens_output": 1250,
          "duration_seconds": 28.9
        }
      ]
    }
  ]
}
```

**Key Points:**
- Two PRs with same task_index (1)
- First PR closed without merging (failed attempt)
- Second PR merged (successful attempt)
- Task status is "completed" (derived from latest PR)
- Complete history preserved (both attempts visible)
- Total cost across both attempts: $0.37

### Example 5: Multi-Reviewer Large Project

A larger project showing team distribution:

```json
{
  "schema_version": "2.0",
  "project": "e-commerce-checkout",
  "last_updated": "2025-12-29T22:15:00Z",
  "tasks": [
    {
      "index": 1,
      "description": "Add shopping cart persistence",
      "status": "completed"
    },
    {
      "index": 2,
      "description": "Implement guest checkout flow",
      "status": "completed"
    },
    {
      "index": 3,
      "description": "Add payment method selection",
      "status": "in_progress"
    },
    {
      "index": 4,
      "description": "Implement order confirmation email",
      "status": "in_progress"
    },
    {
      "index": 5,
      "description": "Add shipping address validation",
      "status": "pending"
    },
    {
      "index": 6,
      "description": "Implement discount code system",
      "status": "pending"
    },
    {
      "index": 7,
      "description": "Add order history page",
      "status": "pending"
    }
  ],
  "pull_requests": [
    {
      "task_index": 1,
      "pr_number": 200,
      "branch_name": "claudestep/checkout/step-1",
      "reviewer": "alice",
      "pr_state": "merged",
      "created_at": "2025-12-25T09:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.13,
          "created_at": "2025-12-25T09:00:00Z",
          "workflow_run_id": 567890,
          "tokens_input": 5000,
          "tokens_output": 1900,
          "duration_seconds": 44.2
        }
      ]
    },
    {
      "task_index": 2,
      "pr_number": 201,
      "branch_name": "claudestep/checkout/step-2",
      "reviewer": "bob",
      "pr_state": "merged",
      "created_at": "2025-12-26T11:30:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.16,
          "created_at": "2025-12-26T11:30:00Z",
          "workflow_run_id": 567900,
          "tokens_input": 6100,
          "tokens_output": 2300,
          "duration_seconds": 50.1
        }
      ]
    },
    {
      "task_index": 3,
      "pr_number": 202,
      "branch_name": "claudestep/checkout/step-3",
      "reviewer": "alice",
      "pr_state": "open",
      "created_at": "2025-12-28T14:00:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.14,
          "created_at": "2025-12-28T14:00:00Z",
          "workflow_run_id": 567910,
          "tokens_input": 5300,
          "tokens_output": 2000,
          "duration_seconds": 46.3
        }
      ]
    },
    {
      "task_index": 4,
      "pr_number": 203,
      "branch_name": "claudestep/checkout/step-4",
      "reviewer": "charlie",
      "pr_state": "open",
      "created_at": "2025-12-29T10:15:00Z",
      "ai_operations": [
        {
          "type": "PRCreation",
          "model": "claude-sonnet-4",
          "cost_usd": 0.15,
          "created_at": "2025-12-29T10:15:00Z",
          "workflow_run_id": 567920,
          "tokens_input": 5700,
          "tokens_output": 2150,
          "duration_seconds": 48.7
        }
      ]
    }
  ]
}
```

**Key Points:**
- 7 tasks total, showing scalability
- 3 different reviewers (alice, bob, charlie)
- Alice has 2 PRs (1 merged, 1 open)
- Bob has 1 PR (merged)
- Charlie has 1 PR (open)
- 2 completed, 2 in-progress, 3 pending
- Shows how capacity checking would work

### Python Dataclass Structure

Complete Python implementation with type hints and validation:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class TaskStatus(Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PRState(Enum):
    """GitHub PR states."""
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class AIOperationType(Enum):
    """Types of AI operations."""
    PR_CREATION = "PRCreation"
    PR_REFINEMENT = "PRRefinement"
    PR_SUMMARY = "PRSummary"


@dataclass
class AIOperation:
    """Represents a single AI operation (creation, refinement, summary)."""

    type: str  # AIOperationType enum value
    model: str
    cost_usd: float
    created_at: datetime
    workflow_run_id: int
    tokens_input: int = 0
    tokens_output: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "model": self.model,
            "cost_usd": self.cost_usd,
            "created_at": self.created_at.isoformat(),
            "workflow_run_id": self.workflow_run_id,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIOperation":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            type=data["type"],
            model=data["model"],
            cost_usd=float(data["cost_usd"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            workflow_run_id=int(data["workflow_run_id"]),
            tokens_input=int(data.get("tokens_input", 0)),
            tokens_output=int(data.get("tokens_output", 0)),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
        )


@dataclass
class PullRequest:
    """Represents a GitHub PR created for a task."""

    task_index: int
    pr_number: int
    branch_name: str
    reviewer: str
    pr_state: str  # PRState enum value
    created_at: datetime
    ai_operations: List[AIOperation] = field(default_factory=list)

    def get_total_cost(self) -> float:
        """Calculate total cost of all AI operations for this PR."""
        return sum(op.cost_usd for op in self.ai_operations)

    def get_total_tokens(self) -> tuple[int, int]:
        """Get total input and output tokens.

        Returns:
            Tuple of (total_input_tokens, total_output_tokens)
        """
        total_input = sum(op.tokens_input for op in self.ai_operations)
        total_output = sum(op.tokens_output for op in self.ai_operations)
        return (total_input, total_output)

    def get_total_duration(self) -> float:
        """Calculate total duration of all AI operations in seconds."""
        return sum(op.duration_seconds for op in self.ai_operations)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_index": self.task_index,
            "pr_number": self.pr_number,
            "branch_name": self.branch_name,
            "reviewer": self.reviewer,
            "pr_state": self.pr_state,
            "created_at": self.created_at.isoformat(),
            "ai_operations": [op.to_dict() for op in self.ai_operations],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            task_index=int(data["task_index"]),
            pr_number=int(data["pr_number"]),
            branch_name=data["branch_name"],
            reviewer=data["reviewer"],
            pr_state=data["pr_state"],
            created_at=datetime.fromisoformat(data["created_at"]),
            ai_operations=[
                AIOperation.from_dict(op) for op in data.get("ai_operations", [])
            ],
        )


@dataclass
class Task:
    """Represents a task from spec.md with its current status."""

    index: int
    description: str
    status: str  # TaskStatus enum value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "index": self.index,
            "description": self.description,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            index=int(data["index"]),
            description=data["description"],
            status=data["status"],
        )


@dataclass
class Project:
    """Top-level project metadata container."""

    schema_version: str
    project: str
    last_updated: datetime
    tasks: List[Task] = field(default_factory=list)
    pull_requests: List[PullRequest] = field(default_factory=list)

    def get_task_by_index(self, index: int) -> Optional[Task]:
        """Get task by its index."""
        for task in self.tasks:
            if task.index == index:
                return task
        return None

    def get_prs_for_task(self, task_index: int) -> List[PullRequest]:
        """Get all PRs for a given task (supports retry scenario)."""
        return [pr for pr in self.pull_requests if pr.task_index == task_index]

    def get_latest_pr_for_task(self, task_index: int) -> Optional[PullRequest]:
        """Get the most recent PR for a task (by created_at)."""
        prs = self.get_prs_for_task(task_index)
        if not prs:
            return None
        return max(prs, key=lambda pr: pr.created_at)

    def calculate_task_status(self, task_index: int) -> TaskStatus:
        """Calculate task status from PR state.

        This is the core logic that derives task status:
        - No PR → pending
        - PR open → in_progress
        - PR merged → completed
        - Multiple PRs → use latest by created_at
        """
        latest_pr = self.get_latest_pr_for_task(task_index)

        if latest_pr is None:
            return TaskStatus.PENDING

        if latest_pr.pr_state == PRState.MERGED.value:
            return TaskStatus.COMPLETED
        elif latest_pr.pr_state in [PRState.OPEN.value, PRState.CLOSED.value]:
            return TaskStatus.IN_PROGRESS
        else:
            return TaskStatus.PENDING

    def update_all_task_statuses(self) -> None:
        """Update all task statuses based on current PR states.

        Call this after loading from JSON to ensure consistency.
        """
        for task in self.tasks:
            task.status = self.calculate_task_status(task.index).value

    def get_total_cost(self) -> float:
        """Calculate total cost across all PRs."""
        return sum(pr.get_total_cost() for pr in self.pull_requests)

    def get_cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by AI model."""
        costs: Dict[str, float] = {}
        for pr in self.pull_requests:
            for op in pr.ai_operations:
                costs[op.model] = costs.get(op.model, 0.0) + op.cost_usd
        return costs

    def get_progress_stats(self) -> Dict[str, int]:
        """Get task counts by status."""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
        }
        for task in self.tasks:
            if task.status == TaskStatus.PENDING.value:
                stats["pending"] += 1
            elif task.status == TaskStatus.IN_PROGRESS.value:
                stats["in_progress"] += 1
            elif task.status == TaskStatus.COMPLETED.value:
                stats["completed"] += 1
        return stats

    def get_completion_percentage(self) -> float:
        """Calculate project completion percentage."""
        if not self.tasks:
            return 0.0
        stats = self.get_progress_stats()
        return (stats["completed"] / stats["total"]) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "project": self.project,
            "last_updated": self.last_updated.isoformat(),
            "tasks": [task.to_dict() for task in self.tasks],
            "pull_requests": [pr.to_dict() for pr in self.pull_requests],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create from dictionary (JSON deserialization)."""
        project = cls(
            schema_version=data["schema_version"],
            project=data["project"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
            pull_requests=[
                PullRequest.from_dict(pr) for pr in data.get("pull_requests", [])
            ],
        )
        # Ensure task statuses are consistent with PR states
        project.update_all_task_statuses()
        return project
```

### Serialization Methods

#### JSON Serialization (to_dict)

Each dataclass implements `to_dict()` for converting to JSON-serializable dictionaries:

**Key Behaviors:**
- DateTime objects converted to ISO 8601 strings using `.isoformat()`
- Nested objects recursively converted (e.g., `ai_operations` list)
- Enum values converted to their string values
- All numeric types preserved as-is

**Example Usage:**
```python
import json

project = Project(
    schema_version="2.0",
    project="my-project",
    last_updated=datetime.now(),
    tasks=[...],
    pull_requests=[...]
)

# Convert to JSON
json_str = json.dumps(project.to_dict(), indent=2)

# Write to file
with open("metadata.json", "w") as f:
    json.dump(project.to_dict(), f, indent=2)
```

#### JSON Deserialization (from_dict)

Each dataclass implements `from_dict()` classmethod for loading from JSON:

**Key Behaviors:**
- DateTime strings parsed using `datetime.fromisoformat()`
- Nested objects recursively constructed
- Default values applied for optional fields
- Type coercion (e.g., ensuring ints and floats)
- **Automatic status synchronization**: `update_all_task_statuses()` called after loading

**Example Usage:**
```python
# Load from JSON file
with open("metadata.json", "r") as f:
    data = json.load(f)

project = Project.from_dict(data)

# Task statuses automatically synchronized with PR states
print(f"Project: {project.project}")
print(f"Completion: {project.get_completion_percentage():.1f}%")
```

#### Status Synchronization

The `update_all_task_statuses()` method ensures task statuses match PR states:

```python
def update_all_task_statuses(self) -> None:
    """Update all task statuses based on current PR states."""
    for task in self.tasks:
        task.status = self.calculate_task_status(task.index).value
```

This is automatically called in `from_dict()` to handle:
- JSON files with stale status values
- Manual JSON edits
- Migration from old schema versions

### Common Query Operations

#### 1. Get Reviewer Capacity (Open PRs per Reviewer)

Find which reviewers have capacity for new PR assignments:

```python
def get_reviewer_capacity(projects: List[Project], max_open_prs: int = 3) -> Dict[str, Dict[str, Any]]:
    """Get open PR count and capacity for each reviewer.

    Args:
        projects: List of all projects
        max_open_prs: Maximum open PRs per reviewer

    Returns:
        Dict mapping reviewer username to capacity info
    """
    reviewer_stats: Dict[str, Dict[str, Any]] = {}

    for project in projects:
        for pr in project.pull_requests:
            if pr.pr_state == PRState.OPEN.value:
                if pr.reviewer not in reviewer_stats:
                    reviewer_stats[pr.reviewer] = {
                        "open_prs": 0,
                        "pr_numbers": [],
                        "projects": set()
                    }
                reviewer_stats[pr.reviewer]["open_prs"] += 1
                reviewer_stats[pr.reviewer]["pr_numbers"].append(pr.pr_number)
                reviewer_stats[pr.reviewer]["projects"].add(project.project)

    # Add capacity info
    for reviewer, stats in reviewer_stats.items():
        stats["has_capacity"] = stats["open_prs"] < max_open_prs
        stats["available_slots"] = max(0, max_open_prs - stats["open_prs"])
        stats["projects"] = list(stats["projects"])  # Convert set to list

    return reviewer_stats

# Example usage
capacity = get_reviewer_capacity(all_projects, max_open_prs=3)

for reviewer, stats in capacity.items():
    print(f"{reviewer}:")
    print(f"  Open PRs: {stats['open_prs']}")
    print(f"  Has capacity: {stats['has_capacity']}")
    print(f"  Available slots: {stats['available_slots']}")
    print(f"  Projects: {', '.join(stats['projects'])}")
```

**Output Example:**
```
alice:
  Open PRs: 2
  Has capacity: True
  Available slots: 1
  Projects: auth-refactor, checkout
bob:
  Open PRs: 3
  Has capacity: False
  Available slots: 0
  Projects: auth-refactor, api-performance
charlie:
  Open PRs: 1
  Has capacity: True
  Available slots: 2
  Projects: checkout
```

#### 2. Calculate Project Completion Percentage

Get completion status for a single project or across all projects:

```python
def get_project_completion(project: Project) -> Dict[str, Any]:
    """Get detailed completion stats for a project."""
    stats = project.get_progress_stats()

    return {
        "project": project.project,
        "total_tasks": stats["total"],
        "completed": stats["completed"],
        "in_progress": stats["in_progress"],
        "pending": stats["pending"],
        "completion_percentage": project.get_completion_percentage(),
        "is_complete": stats["completed"] == stats["total"],
        "has_work_in_progress": stats["in_progress"] > 0,
    }

# Example usage
completion = get_project_completion(project)
print(f"Project: {completion['project']}")
print(f"Progress: {completion['completed']}/{completion['total_tasks']} tasks")
print(f"Completion: {completion['completion_percentage']:.1f}%")
print(f"In Progress: {completion['in_progress']}")
print(f"Pending: {completion['pending']}")
```

**Output Example:**
```
Project: auth-refactor
Progress: 2/5 tasks
Completion: 40.0%
In Progress: 1
Pending: 2
```

**Aggregate Across All Projects:**
```python
def get_aggregate_completion(projects: List[Project]) -> Dict[str, Any]:
    """Get completion stats across all projects."""
    total_tasks = sum(len(p.tasks) for p in projects)
    all_stats = [p.get_progress_stats() for p in projects]

    total_completed = sum(s["completed"] for s in all_stats)
    total_in_progress = sum(s["in_progress"] for s in all_stats)
    total_pending = sum(s["pending"] for s in all_stats)

    return {
        "total_projects": len(projects),
        "total_tasks": total_tasks,
        "completed": total_completed,
        "in_progress": total_in_progress,
        "pending": total_pending,
        "overall_completion_percentage": (
            (total_completed / total_tasks * 100) if total_tasks > 0 else 0.0
        ),
    }

# Example usage
aggregate = get_aggregate_completion(all_projects)
print(f"Overall Progress: {aggregate['completed']}/{aggregate['total_tasks']} tasks")
print(f"Completion: {aggregate['overall_completion_percentage']:.1f}%")
```

#### 3. Sum Costs Across Project

Calculate costs with various breakdowns:

```python
def get_cost_analysis(project: Project) -> Dict[str, Any]:
    """Get comprehensive cost analysis for a project."""

    # Cost by model
    cost_by_model = project.get_cost_by_model()

    # Cost by operation type
    cost_by_type: Dict[str, float] = {}
    for pr in project.pull_requests:
        for op in pr.ai_operations:
            cost_by_type[op.type] = cost_by_type.get(op.type, 0.0) + op.cost_usd

    # Cost by reviewer (total cost of PRs assigned to them)
    cost_by_reviewer: Dict[str, float] = {}
    for pr in project.pull_requests:
        cost = pr.get_total_cost()
        cost_by_reviewer[pr.reviewer] = cost_by_reviewer.get(pr.reviewer, 0.0) + cost

    # Token usage
    total_input_tokens = 0
    total_output_tokens = 0
    for pr in project.pull_requests:
        input_tok, output_tok = pr.get_total_tokens()
        total_input_tokens += input_tok
        total_output_tokens += output_tok

    return {
        "project": project.project,
        "total_cost": project.get_total_cost(),
        "cost_by_model": cost_by_model,
        "cost_by_operation_type": cost_by_type,
        "cost_by_reviewer": cost_by_reviewer,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "average_cost_per_task": (
            project.get_total_cost() / len(project.tasks) if project.tasks else 0.0
        ),
    }

# Example usage
costs = get_cost_analysis(project)
print(f"Total Cost: ${costs['total_cost']:.2f}")
print(f"Average per Task: ${costs['average_cost_per_task']:.2f}")
print("\nCost by Model:")
for model, cost in costs['cost_by_model'].items():
    print(f"  {model}: ${cost:.2f}")
print("\nCost by Operation Type:")
for op_type, cost in costs['cost_by_operation_type'].items():
    print(f"  {op_type}: ${cost:.2f}")
```

**Output Example:**
```
Total Cost: $0.72
Average per Task: $0.36

Cost by Model:
  claude-sonnet-4: $0.68
  claude-haiku-4: $0.04

Cost by Operation Type:
  PRCreation: $0.45
  PRRefinement: $0.24
  PRSummary: $0.03
```

#### 4. List Pending Tasks

Find the next task(s) to work on:

```python
def get_pending_tasks(project: Project, limit: Optional[int] = None) -> List[Task]:
    """Get all pending tasks, optionally limited to first N."""
    pending = [
        task for task in project.tasks
        if task.status == TaskStatus.PENDING.value
    ]

    if limit is not None:
        return pending[:limit]
    return pending

def get_next_task(project: Project) -> Optional[Task]:
    """Get the next task to work on (first pending task)."""
    pending = get_pending_tasks(project, limit=1)
    return pending[0] if pending else None

# Example usage
next_task = get_next_task(project)
if next_task:
    print(f"Next task: #{next_task.index} - {next_task.description}")
else:
    print("No pending tasks - project complete!")

all_pending = get_pending_tasks(project)
print(f"\nRemaining tasks: {len(all_pending)}")
for task in all_pending:
    print(f"  #{task.index}: {task.description}")
```

**Output Example:**
```
Next task: #3 - Add email validation to user registration

Remaining tasks: 3
  #3: Add email validation to user registration
  #4: Implement password reset functionality
  #5: Add two-factor authentication support
```

#### 5. Team Leaderboard

Aggregate PR statistics across all projects by team member:

```python
def get_team_leaderboard(projects: List[Project]) -> List[Dict[str, Any]]:
    """Generate team leaderboard with PR and cost statistics.

    Returns list sorted by merged PRs (descending).
    """
    reviewer_stats: Dict[str, Dict[str, Any]] = {}

    for project in projects:
        for pr in project.pull_requests:
            if pr.reviewer not in reviewer_stats:
                reviewer_stats[pr.reviewer] = {
                    "reviewer": pr.reviewer,
                    "total_prs": 0,
                    "merged_prs": 0,
                    "open_prs": 0,
                    "closed_prs": 0,
                    "total_cost": 0.0,
                    "total_operations": 0,
                    "projects": set(),
                }

            stats = reviewer_stats[pr.reviewer]
            stats["total_prs"] += 1
            stats["total_cost"] += pr.get_total_cost()
            stats["total_operations"] += len(pr.ai_operations)
            stats["projects"].add(project.project)

            if pr.pr_state == PRState.MERGED.value:
                stats["merged_prs"] += 1
            elif pr.pr_state == PRState.OPEN.value:
                stats["open_prs"] += 1
            elif pr.pr_state == PRState.CLOSED.value:
                stats["closed_prs"] += 1

    # Convert to list and sort by merged PRs
    leaderboard = []
    for stats in reviewer_stats.values():
        stats["projects"] = list(stats["projects"])
        stats["project_count"] = len(stats["projects"])
        leaderboard.append(stats)

    leaderboard.sort(key=lambda x: x["merged_prs"], reverse=True)
    return leaderboard

# Example usage
leaderboard = get_team_leaderboard(all_projects)

print("Team Leaderboard")
print("-" * 80)
print(f"{'Reviewer':<15} {'Merged':<10} {'Open':<10} {'Total':<10} {'Cost':<12} {'Projects'}")
print("-" * 80)

for stats in leaderboard:
    print(
        f"{stats['reviewer']:<15} "
        f"{stats['merged_prs']:<10} "
        f"{stats['open_prs']:<10} "
        f"{stats['total_prs']:<10} "
        f"${stats['total_cost']:<11.2f} "
        f"{', '.join(stats['projects'])}"
    )
```

**Output Example:**
```
Team Leaderboard
--------------------------------------------------------------------------------
Reviewer        Merged     Open       Total      Cost         Projects
--------------------------------------------------------------------------------
alice           4          2          6          $1.23        auth-refactor, checkout, dashboard
bob             3          1          4          $0.89        auth-refactor, api-performance
charlie         2          1          3          $0.67        checkout, payments
dana            1          0          1          $0.29        payments
```

### Edge Cases and Validation

#### 1. Orphaned PRs (PR references non-existent task)

**Detection:**
```python
def validate_pr_references(project: Project) -> List[str]:
    """Validate that all PRs reference valid tasks.

    Returns list of error messages.
    """
    errors = []
    task_indices = {task.index for task in project.tasks}

    for pr in project.pull_requests:
        if pr.task_index not in task_indices:
            errors.append(
                f"PR #{pr.pr_number} references non-existent task index {pr.task_index}"
            )

    return errors
```

#### 2. Duplicate Task Indices

**Detection:**
```python
def validate_unique_task_indices(project: Project) -> List[str]:
    """Validate that task indices are unique.

    Returns list of error messages.
    """
    errors = []
    seen_indices = set()

    for task in project.tasks:
        if task.index in seen_indices:
            errors.append(f"Duplicate task index: {task.index}")
        seen_indices.add(task.index)

    return errors
```

#### 3. Status Inconsistency (Status doesn't match PR state)

**Detection and Auto-Fix:**
```python
def validate_and_fix_task_statuses(project: Project) -> List[str]:
    """Validate task statuses match PR states, fix if needed.

    Returns list of warning messages about fixed statuses.
    """
    warnings = []

    for task in project.tasks:
        expected_status = project.calculate_task_status(task.index)
        if task.status != expected_status.value:
            warnings.append(
                f"Task {task.index} status mismatch: "
                f"was '{task.status}', should be '{expected_status.value}' - FIXED"
            )
            task.status = expected_status.value

    return warnings
```

#### 4. Empty AI Operations (PR with no operations)

**Detection:**
```python
def validate_pr_has_operations(project: Project) -> List[str]:
    """Validate that all PRs have at least one AI operation.

    Returns list of error messages.
    """
    errors = []

    for pr in project.pull_requests:
        if not pr.ai_operations:
            errors.append(
                f"PR #{pr.pr_number} has no AI operations (task {pr.task_index})"
            )

    return errors
```

#### 5. Future Timestamp (created_at in the future)

**Detection:**
```python
from datetime import datetime, timezone

def validate_timestamps(project: Project) -> List[str]:
    """Validate that timestamps are not in the future.

    Returns list of warning messages.
    """
    warnings = []
    now = datetime.now(timezone.utc)

    for pr in project.pull_requests:
        if pr.created_at > now:
            warnings.append(
                f"PR #{pr.pr_number} has future timestamp: {pr.created_at.isoformat()}"
            )

        for op in pr.ai_operations:
            if op.created_at > now:
                warnings.append(
                    f"PR #{pr.pr_number} operation '{op.type}' has future timestamp: "
                    f"{op.created_at.isoformat()}"
                )

    return warnings
```

#### Complete Validation Suite

```python
def validate_project(project: Project, auto_fix: bool = True) -> Dict[str, List[str]]:
    """Run all validations on a project.

    Args:
        project: Project to validate
        auto_fix: If True, automatically fix issues where possible

    Returns:
        Dict with 'errors' and 'warnings' lists
    """
    result = {
        "errors": [],
        "warnings": [],
    }

    # Critical errors (data inconsistency)
    result["errors"].extend(validate_pr_references(project))
    result["errors"].extend(validate_unique_task_indices(project))
    result["errors"].extend(validate_pr_has_operations(project))

    # Warnings (fixable issues)
    result["warnings"].extend(validate_timestamps(project))

    if auto_fix:
        result["warnings"].extend(validate_and_fix_task_statuses(project))
    else:
        # Just detect, don't fix
        for task in project.tasks:
            expected = project.calculate_task_status(task.index)
            if task.status != expected.value:
                result["warnings"].append(
                    f"Task {task.index} status mismatch: "
                    f"is '{task.status}', should be '{expected.value}'"
                )

    return result

# Example usage
validation = validate_project(project, auto_fix=True)

if validation["errors"]:
    print("ERRORS:")
    for error in validation["errors"]:
        print(f"  ❌ {error}")

if validation["warnings"]:
    print("WARNINGS:")
    for warning in validation["warnings"]:
        print(f"  ⚠️  {warning}")

if not validation["errors"] and not validation["warnings"]:
    print("✅ Project validation passed")
```

### Migration Strategy Details

#### Step 1: Schema Version Detection

```python
def detect_schema_version(data: Dict[str, Any]) -> str:
    """Detect schema version from JSON data."""
    return data.get("schema_version", "1.0")

def load_project_with_migration(json_path: str) -> Project:
    """Load project from JSON, auto-migrating if needed."""
    with open(json_path, "r") as f:
        data = json.load(f)

    version = detect_schema_version(data)

    if version == "1.0":
        # Migrate from old format
        data = migrate_v1_to_v2(data)
    elif version == "2.0":
        # Already new format
        pass
    else:
        raise ValueError(f"Unknown schema version: {version}")

    return Project.from_dict(data)
```

#### Step 2: V1 → V2 Migration Function

```python
def migrate_v1_to_v2(v1_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate schema version 1.0 to 2.0.

    V1 Structure:
        Project → steps → [Step with optional PR fields] → ai_tasks

    V2 Structure:
        Project → tasks → [Task with status]
        Project → pull_requests → [PullRequest] → ai_operations
    """
    tasks = []
    pull_requests = []

    for step in v1_data.get("steps", []):
        # Extract task info
        task_index = step.get("step_index") or step.get("task_index")  # Handle old field name
        task_description = step.get("step_description") or step.get("task_description")

        # Determine status from PR fields
        if step.get("pr_state") == "merged":
            status = "completed"
        elif step.get("pr_number") is not None:
            status = "in_progress"
        else:
            status = "pending"

        tasks.append({
            "index": task_index,
            "description": task_description,
            "status": status,
        })

        # Extract PR info if present
        if step.get("pr_number") is not None:
            pull_requests.append({
                "task_index": task_index,
                "pr_number": step["pr_number"],
                "branch_name": step["branch_name"],
                "reviewer": step["reviewer"],
                "pr_state": step["pr_state"],
                "created_at": step["created_at"],
                "ai_operations": step.get("ai_tasks", []),  # Rename ai_tasks → ai_operations
            })

    return {
        "schema_version": "2.0",
        "project": v1_data["project"],
        "last_updated": v1_data["last_updated"],
        "tasks": tasks,
        "pull_requests": pull_requests,
    }
```

#### Step 3: Backward Compatibility Wrapper

```python
class MetadataStorage:
    """Handle reading/writing project metadata with auto-migration."""

    @staticmethod
    def load(json_path: str) -> Project:
        """Load project, auto-migrating old versions."""
        return load_project_with_migration(json_path)

    @staticmethod
    def save(project: Project, json_path: str) -> None:
        """Save project in latest format (v2.0)."""
        with open(json_path, "w") as f:
            json.dump(project.to_dict(), f, indent=2)

    @staticmethod
    def save_with_backup(project: Project, json_path: str) -> None:
        """Save with backup of old version."""
        import shutil
        from pathlib import Path

        # Create backup if file exists
        if Path(json_path).exists():
            backup_path = f"{json_path}.backup"
            shutil.copy2(json_path, backup_path)

        # Save new version
        MetadataStorage.save(project, json_path)
```

**Technical Notes:**
- Phase 6 specification complete and ready for implementation
- All examples tested for JSON validity
- Dataclass structure includes full type hints for static analysis
- Query operations optimized for common use cases
- Validation suite covers all known edge cases
- Migration path handles backward compatibility with v1.0 schema

## Phase 8: User Review and Decision

**Tasks:**
- Present all alternatives with diagrams
- Get user feedback on preferred approach
- Refine based on feedback
- Get final approval before implementation

**Expected Outcome:**
- Clear decision on which model to implement
- User buy-in on approach
- Ready to proceed with implementation

## Notes

- **Diagrams**: Use ASCII art or mermaid-style notation for clarity in markdown
- **Examples**: Use the same 5-task auth-refactor project across all alternatives for consistency
- **Verbosity**: Balance between thorough analysis and decision paralysis - 3-4 alternatives is enough
- **User input**: Pause after each alternative for user feedback before proceeding
