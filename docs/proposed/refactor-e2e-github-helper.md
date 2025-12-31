## Background

The E2E test helper (`tests/e2e/helpers/github_helper.py`) currently implements GitHub API access through direct `gh` CLI subprocess calls. This duplicates functionality that already exists in the infrastructure layer (`src/claudestep/infrastructure/github/operations.py`), creating maintenance burden and violating the DRY principle.

The infrastructure layer already provides:
- `run_gh_command()` - Generic GitHub CLI wrapper with error handling
- `gh_api_call()` - REST API calls through GitHub CLI
- Type-safe domain models (`GitHubPullRequest`)
- Consistent error handling with `GitHubAPIError`

This refactoring will consolidate GitHub operations into the infrastructure layer, making the E2E helper thinner and more focused on workflow orchestration and test-specific operations.

## Phases

- [x] Phase 1: Add missing GitHub operations to infrastructure layer

**Status:** Completed

**Technical notes:**
- Added `WorkflowRun` domain model with properties: `database_id`, `status`, `conclusion`, `created_at`, `head_branch`, `url`
- Added `PRComment` domain model with properties: `body`, `author`, `created_at`
- Both models include helper methods: `WorkflowRun.is_completed()`, `is_success()`, `is_failure()` and proper `from_dict()` constructors
- Added workflow operations: `list_workflow_runs()`, `trigger_workflow()`
- Added PR operations: `get_pull_request_by_branch()`, `get_pull_request_comments()`, `close_pull_request()`
- Added branch operations: `delete_branch()`, `list_branches()`
- All functions follow infrastructure layer patterns: use `run_gh_command()` and `gh_api_call()`, return domain models, raise `GitHubAPIError` on failures
- All functions include comprehensive docstrings with usage examples
- Build verified: all modules compile and import successfully

**What to add:**

Add the following generic GitHub operations to `src/claudestep/infrastructure/github/operations.py`:

1. **Workflow operations**:
   - `list_workflow_runs(repo: str, workflow_name: str, branch: str, limit: int) -> List[WorkflowRun]`
   - `trigger_workflow(repo: str, workflow_name: str, inputs: Dict[str, str], ref: str) -> None`
   - Create `WorkflowRun` domain model in `src/claudestep/domain/github_models.py`

2. **Pull request operations** (extend existing):
   - `get_pull_request_by_branch(repo: str, branch: str) -> Optional[GitHubPullRequest]`
   - `get_pull_request_comments(repo: str, pr_number: int) -> List[PRComment]`
   - `close_pull_request(repo: str, pr_number: int) -> None`
   - Create `PRComment` domain model in `src/claudestep/domain/github_models.py`

3. **Branch operations**:
   - `delete_branch(repo: str, branch: str) -> None`
   - `list_branches(repo: str, prefix: Optional[str] = None) -> List[str]`

**Key principles:**
- All functions should be generic (not test-specific)
- Use domain models for return types
- Delegate to `run_gh_command()` for CLI calls
- Delegate to `gh_api_call()` for API calls
- Raise `GitHubAPIError` on failures
- Add comprehensive docstrings with usage examples

**Files to modify:**
- `src/claudestep/domain/github_models.py` - Add `WorkflowRun` and `PRComment` models
- `src/claudestep/infrastructure/github/operations.py` - Add new operations

- [ ] Phase 2: Refactor GitHubHelper to use infrastructure layer

**Refactor these methods:**

Update `tests/e2e/helpers/github_helper.py` to delegate to infrastructure layer:

1. **`trigger_workflow()`** → Use `infrastructure.github.operations.trigger_workflow()`
2. **`get_latest_workflow_run()`** → Use `infrastructure.github.operations.list_workflow_runs(limit=1)`
3. **`get_pull_request()`** → Use `infrastructure.github.operations.get_pull_request_by_branch()`
4. **`get_pr_comments()`** → Use `infrastructure.github.operations.get_pull_request_comments()`
5. **`close_pull_request()`** → Use `infrastructure.github.operations.close_pull_request()`
6. **`delete_branch()`** → Use `infrastructure.github.operations.delete_branch()`
7. **`cleanup_test_branches()`** → Use `infrastructure.github.operations.list_branches()` + `delete_branch()`

**Keep these methods in GitHubHelper:**
- `wait_for_condition()` - Generic polling utility (test-specific)
- `wait_for_workflow_to_start()` - Test-specific workflow polling
- `wait_for_workflow_completion()` - Test-specific workflow polling
- `cleanup_test_prs()` - Test-specific cleanup logic
- `get_pull_requests_for_project()` - Already delegates to infrastructure layer

**Implementation approach:**
- Replace direct `subprocess.run()` calls with infrastructure layer calls
- Convert JSON parsing to use domain models
- Simplify error handling (infrastructure layer handles it)
- Keep test-specific logging and diagnostic messages
- Preserve method signatures to avoid breaking tests

**Files to modify:**
- `tests/e2e/helpers/github_helper.py` - Refactor to use infrastructure layer

- [ ] Phase 3: Update domain models for E2E test needs

**Add test-specific properties if needed:**

Review the `WorkflowRun` and `PRComment` domain models created in Phase 1 and ensure they have all properties needed by E2E tests:

**WorkflowRun properties:**
- `database_id: int` - Used for logging
- `status: str` - Used for polling ("queued", "in_progress", "completed")
- `conclusion: Optional[str]` - Used for success checking ("success", "failure", etc.)
- `created_at: datetime` - Used for detecting new runs
- `head_branch: str` - Used for filtering
- `url: str` - Used for diagnostic logging

**PRComment properties:**
- `body: str` - Comment text
- `author: str` - Comment author
- `created_at: datetime` - When comment was posted

**Files to modify:**
- `src/claudestep/domain/github_models.py` - Add properties if missing

- [ ] Phase 4: Validation and testing

**Validate the refactoring:**

1. **Run E2E tests:**
   ```bash
   pytest tests/e2e/ -v
   ```
   Ensure all tests pass with the refactored helper

2. **Manual verification:**
   - Test workflow triggering works correctly
   - Test PR creation and cleanup work
   - Test branch cleanup works
   - Verify logging and error messages are preserved

3. **Code review:**
   - Verify no duplicate GitHub logic remains
   - Ensure infrastructure layer is generic (not test-specific)
   - Check that GitHubHelper is now focused on test orchestration
   - Confirm domain models are properly used

**Success criteria:**
- All E2E tests pass
- No direct `subprocess.run()` calls to `gh` in GitHubHelper (except through infrastructure layer)
- GitHubHelper is significantly shorter and simpler
- Infrastructure layer has reusable GitHub operations
- Code follows architecture patterns (layered, domain models, error handling)
