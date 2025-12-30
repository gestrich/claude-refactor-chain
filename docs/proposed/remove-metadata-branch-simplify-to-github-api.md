# Remove Metadata Branch and Simplify to GitHub API Only

## Background

The ClaudeStep project originally used a simple approach: query GitHub API for PRs with ClaudeStep labels and derive all information from PR state, labels, assignees, and branch names. This was straightforward and worked well.

Later, a `claudestep-metadata` branch was added to track additional details like project associations and primary reviewers. However, this added significant complexity:
- Hybrid data model with Tasks and PullRequests
- Need to keep metadata in sync with GitHub state
- Architecture mentions "Future: Metadata Synchronization" indicating known sync problems
- Additional storage layer that duplicates information available in GitHub

**User's insight**: The information we need can be derived from GitHub alone:
- **Project association**: Extract from branch name pattern `claude-step-<project>-<task-number>`
- **Primary reviewer**: Use GitHub's "assignees" field on PRs
- **Task status**: Derive from PR state (open/draft = in progress, merged = completed, closed without merge = failed/abandoned)
- **Statistics**: Query GitHub API directly when statistics are requested, considering all PR states

This plan removes the metadata branch entirely and returns to a simpler GitHub-API-only architecture.

## Goals

1. Remove all metadata branch code and infrastructure
2. Use GitHub PR queries as the single source of truth
3. Extract project name from branch naming convention
4. Use PR assignees field for reviewer tracking
5. Maintain statistics feature by querying GitHub directly
6. Reduce overall code complexity and maintenance burden

## Phases

- [x] Phase 1: Audit current metadata usage

**Objective**: Understand where metadata is currently used and what needs to be replaced with GitHub queries.

**Status**: ✅ Complete

**Audit Findings**:

### Files Using Metadata Infrastructure

**Source Code Files** (11 files):
1. `src/claudestep/services/metadata_service.py` - Core metadata service
2. `src/claudestep/infrastructure/metadata/github_metadata_store.py` - GitHub branch storage implementation
3. `src/claudestep/infrastructure/metadata/operations.py` - MetadataStore interface
4. `src/claudestep/infrastructure/metadata/__init__.py` - Package initialization
5. `src/claudestep/services/task_management_service.py` - Uses metadata to find in-progress tasks
6. `src/claudestep/services/statistics_service.py` - Reads metadata for project stats, team stats, costs
7. `src/claudestep/services/reviewer_management_service.py` - Currently uses artifacts (NOT metadata!) for capacity checking
8. `src/claudestep/cli/commands/prepare.py` - Initializes metadata store/service, updates PR state on merge
9. `src/claudestep/cli/commands/finalize.py` - Writes PR metadata after creation
10. `src/claudestep/cli/commands/statistics.py` - Uses metadata service for statistics
11. `src/claudestep/cli/commands/discover_ready.py` - Uses metadata service

**Test Files** (8 files):
- `tests/unit/services/test_metadata_service.py`
- `tests/unit/services/test_task_management.py`
- `tests/unit/services/test_statistics_service.py`
- `tests/unit/services/test_reviewer_management.py`
- `tests/unit/infrastructure/metadata/test_github_metadata_store.py`
- `tests/integration/cli/commands/test_prepare.py`
- `tests/integration/cli/commands/test_finalize.py`
- `tests/integration/cli/commands/test_discover_ready.py`

### Metadata Read Operations

| Operation | File | Purpose | GitHub API Replacement |
|-----------|------|---------|----------------------|
| `get_project(project_name)` | metadata_service.py | Load project metadata | Query PRs by label + parse branch names |
| `list_project_names()` | statistics_service.py | Discover all projects | Query all PRs with claudestep label, extract project from branch names |
| `find_in_progress_tasks(project)` | task_management_service.py | Find tasks with open PRs | Query open PRs filtered by label + project (from branch name) |
| `get_reviewer_assignments(project)` | metadata_service.py (currently unused!) | Map task → reviewer | Query open PRs, extract from assignees field |
| `get_open_prs_by_reviewer()` | metadata_service.py | Group open PRs by reviewer | Query open PRs filtered by label + assignee |
| `get_reviewer_capacity()` | metadata_service.py | Count open PRs per reviewer | Query open PRs filtered by assignee |
| `get_projects_modified_since(date)` | statistics_service.py | Filter projects by date | Query PRs filtered by updated date |
| `get_project_stats()` | statistics_service.py | Get project progress stats | Parse spec.md from base branch + query PRs for in-progress count |

### Metadata Write Operations

| Operation | File | When | Data Written | Notes |
|-----------|------|------|--------------|-------|
| `save_project(project)` | metadata_service.py | After creating/updating PR | Full HybridProjectMetadata | Main write operation |
| `add_pr_to_project()` | finalize.py | After PR creation | PullRequest object with AIOperations | Called from finalize command |
| `update_pr_state()` | prepare.py | When PR is merged | PR state ("merged") | Updates existing PR in metadata |

### Data Model in Metadata

**HybridProjectMetadata** contains:
- `project`: Project name (✅ available from branch name pattern)
- `tasks`: List of Task objects (✅ available from spec.md in base branch)
- `pull_requests`: List of PullRequest objects (✅ available from GitHub PR API)
- `last_updated`: Timestamp (✅ available from GitHub PR updated_at)

**Task** contains:
- `index`: Task number (✅ available from spec.md)
- `description`: Task text (✅ available from spec.md)
- `status`: TaskStatus enum (✅ derivable from PR state: open=in_progress, merged=completed)

**PullRequest** contains:
- `task_index`: Which task this implements (✅ available from branch name pattern)
- `pr_number`: GitHub PR number (✅ available from GitHub PR API)
- `branch_name`: Branch name (✅ available from GitHub PR API)
- `reviewer`: Assigned reviewer (✅ available from PR assignees field)
- `pr_state`: "open", "merged", "closed" (✅ available from GitHub PR API)
- `created_at`: Timestamp (✅ available from GitHub PR API)
- `title`: PR title (✅ available from GitHub PR API)
- `ai_operations`: List of AIOperation objects (❌ **UNIQUE DATA - NOT IN GITHUB**)

**AIOperation** contains:
- `type`: "PRCreation", "PRSummary", etc. (❌ **UNIQUE DATA**)
- `model`: AI model used (❌ **UNIQUE DATA**)
- `cost_usd`: Cost in USD (❌ **UNIQUE DATA**)
- `tokens_input`, `tokens_output`: Token counts (❌ **UNIQUE DATA**)
- `duration_seconds`: Operation duration (❌ **UNIQUE DATA**)
- `created_at`: Timestamp (❌ **UNIQUE DATA**)
- `workflow_run_id`: GitHub Actions run ID (✅ available from workflow context)

### Unique Data Not Available via GitHub API

**AI Operation Costs and Metadata**:
- Cost per operation (USD)
- Token counts (input/output)
- Operation duration
- AI model used
- Operation type

**Replacement Strategy for Unique Data**:
1. **Option A**: Store as PR comment (similar to current cost breakdown comments)
   - Pro: Still queryable via GitHub API
   - Pro: Visible in PR for transparency
   - Con: Requires parsing comments to extract data

2. **Option B**: Drop this data entirely
   - Pro: Simplest approach
   - Con: Lose cost tracking across projects

3. **Option C**: Use GitHub Artifacts (currently exists!)
   - Note: The codebase already has artifact-based metadata in `artifact_operations_service.py`
   - Artifacts contain `TaskMetadata` with costs
   - Pro: Already implemented and working
   - Con: Artifacts expire after 90 days by default

**Recommendation**:
- **For Phase 1-4**: Drop AI operation tracking temporarily to simplify
- **Future Enhancement**: Add cost tracking back via PR comments if needed
- **Note**: Current `reviewer_management_service.py` already uses artifacts instead of metadata branch!

### Important Discovery

**ReviewerManagementService** (line 10-56) currently uses **artifact operations** (`find_project_artifacts`) instead of metadata service! This means:
- Reviewer capacity checking does NOT use metadata branch
- It queries artifacts that are uploaded after PR creation
- The metadata service methods `get_reviewer_assignments()` and `get_open_prs_by_reviewer()` are implemented but **not actually used**

This suggests the project is already partially migrated away from metadata branch for reviewer management.

### Replacement Strategy Summary

| Feature | Current Source | Replacement |
|---------|---------------|-------------|
| Project detection | Metadata branch | Branch name parsing (`claude-step-<project>-<task>`) |
| In-progress tasks | Metadata branch | GitHub API: open PRs with label filter |
| Reviewer assignment | Artifacts (already!) | GitHub API: PR assignees field |
| Reviewer capacity | Artifacts (already!) | GitHub API: count open PRs per assignee |
| Project statistics | Metadata + spec.md | Spec.md (base branch) + GitHub API PR queries |
| Team statistics | Metadata | GitHub API: PR queries filtered by assignee |
| Cost tracking | Metadata | Drop temporarily (or use PR comments/artifacts) |

**Deliverable**: ✅ Complete - Comprehensive audit with replacement strategy documented above.

---

- [x] Phase 2: Implement GitHub-based project detection

**Objective**: Replace metadata-based project association with branch name parsing.

**Status**: ✅ Complete

**Branch naming convention** (already exists): `claude-step-<project>-<task-number>`

**Tasks**:
- Verify `PROperationsService.parse_branch_name()` exists and works correctly
- Ensure it extracts both project name and task number from branch names
- Update any code that queries metadata for project association to use branch name parsing instead
- Add tests for edge cases (malformed branch names, missing parts)

**Key changes**:
- `src/claudestep/application/services/pr_operations.py` - verify static methods
- Any services using metadata to get project name should use `parse_branch_name()` instead

**Success criteria**: Project name can be reliably extracted from any ClaudeStep PR branch.

**Technical Notes**:
- ✅ `PROperationsService.parse_branch_name()` verified at `src/claudestep/services/pr_operations_service.py:131-164`
- ✅ Method correctly extracts both project name and task index from branch names
- ✅ Already integrated and used by `ProjectDetectionService.detect_project_from_pr()` at `src/claudestep/services/project_detection_service.py:61`
- ✅ Added 8 additional edge case tests to cover:
  - Index 0 handling
  - Non-numeric indices (rejected)
  - Negative indices (handled as project name with trailing hyphen)
  - Single character project names
  - Numeric characters in project names
  - Whitespace in project names (accepted by regex, though not recommended)
  - Case sensitivity of prefix (must be lowercase "claude-step")
- ✅ All 28 tests in test_pr_operations.py pass
- ✅ All 17 project detection integration tests pass
- ✅ Regex pattern `^claude-step-(.+)-(\d+)$` correctly handles complex project names with hyphens

---

- [ ] Phase 3: Implement GitHub-based reviewer tracking

**Objective**: Use GitHub's PR assignees field instead of metadata for reviewer tracking.

**Tasks**:
- Update `ReviewerManagementService` to query PR assignees via GitHub API instead of metadata
- Modify reviewer capacity checking to count open PRs via GitHub API query with assignee filter
- Update PR creation to set assignee field when creating PRs
- Remove metadata service dependency from `ReviewerManagementService`

**Key changes**:
- `src/claudestep/application/services/reviewer_management.py`
  - Replace metadata queries with GitHub PR list queries filtered by assignee
  - Use `infrastructure/github/operations.py` functions like `list_pull_requests()`
- `src/claudestep/cli/commands/finalize.py` or PR creation code
  - Ensure assignee is set when PR is created via `gh pr create --assignee`

**GitHub query approach**:
```python
# Count open PRs for a reviewer
open_prs = list_pull_requests(
    repo=repo,
    state="open",
    label="claudestep",
    assignee=reviewer_username
)
pr_count = len(open_prs)
at_capacity = pr_count >= reviewer.max_open_prs
```

**Success criteria**: Reviewer capacity checking works entirely through GitHub API queries.

---

- [ ] Phase 4: Implement GitHub-based statistics collection

**Objective**: Rewrite statistics service to query GitHub API directly instead of metadata.

**Tasks**:
- Update `StatisticsService` to remove metadata service dependency
- Implement GitHub-based statistics collection:
  - Query all ClaudeStep PRs (`label="claudestep"`)
  - Extract project name from branch name for each PR
  - Group by project, count total/merged/open
  - Extract reviewer from PR assignees field
  - Group by reviewer, count PRs per reviewer
- Handle pagination for repositories with many PRs
- Add caching or rate limit handling if needed

**Key changes**:
- `src/claudestep/application/services/statistics_service.py`
  - Remove `metadata_service` from constructor
  - Replace all metadata queries with GitHub PR list queries
  - Use `list_pull_requests()`, `list_merged_pull_requests()`, `list_open_pull_requests()`
  - Parse project from branch names using `PROperationsService.parse_branch_name()`

**Data flow**:
```
GitHub API → list_pull_requests(label="claudestep")
         → parse branch names → extract project
         → group by project → count by state
         → extract assignees → count by reviewer
         → format statistics report
```

**Note**: This may be slower than metadata-based approach but eliminates sync issues.

**Success criteria**: Statistics command generates accurate reports from GitHub data alone.

---

- [ ] Phase 5: Remove metadata infrastructure

**Objective**: Delete all metadata-related code that is no longer used.

**Tasks**:
- Remove `src/claudestep/application/services/metadata_service.py`
- Remove `src/claudestep/infrastructure/metadata/github_metadata_store.py`
- Remove `src/claudestep/domain/models.py` classes specific to metadata (keep GitHub models)
  - Remove: `Task`, `PullRequest` (metadata versions), `AIOperation`, `HybridProjectMetadata`
  - Keep: `GitHubPullRequest`, `GitHubUser`, domain models still in use
- Remove metadata-related tests:
  - `tests/unit/services/test_metadata_service.py`
  - `tests/unit/infrastructure/test_github_metadata_store.py` (if exists)
- Update architecture documentation to remove metadata branch references
- Remove metadata schema documentation (`docs/architecture/metadata-schema.md`)

**Files to delete**:
- `src/claudestep/application/services/metadata_service.py`
- `src/claudestep/infrastructure/metadata/github_metadata_store.py`
- `src/claudestep/infrastructure/metadata/__init__.py` (if empty)
- `tests/unit/services/test_metadata_service.py`
- `docs/architecture/metadata-schema.md`

**Documentation updates**:
- `docs/architecture/architecture.md` - Remove "Metadata Synchronization" section
- Update any references to "metadata as source of truth" to "GitHub as source of truth"

**Success criteria**: No metadata-related code remains, all references removed.

---

- [ ] Phase 6: Update CLI commands to remove metadata dependencies

**Objective**: Remove metadata service initialization and usage from all CLI commands.

**Tasks**:
- Audit all commands in `src/claudestep/cli/commands/`
- Remove `metadata_store` and `metadata_service` initialization from commands
- Remove metadata service parameters from service constructors where needed
- Update command orchestration to use GitHub-based approaches

**Commands to update**:
- `prepare.py` - Remove metadata service, use GitHub queries for project/reviewer info
- `finalize.py` - Remove metadata writing, ensure assignee is set on PR creation
- `statistics.py` - Already updated in Phase 4
- `discover.py` - Remove metadata, use GitHub PR queries
- `discover_ready.py` - Remove metadata, use GitHub PR queries

**Pattern to remove**:
```python
# OLD - Don't use this
metadata_store = GitHubMetadataStore(repo)
metadata_service = MetadataService(metadata_store)
```

**Pattern to use**:
```python
# NEW - Services get dependencies they need directly
statistics_service = StatisticsService(repo, base_branch)
reviewer_service = ReviewerManagementService(repo)
```

**Success criteria**: All CLI commands work without metadata infrastructure.

---

- [ ] Phase 7: Update service constructors

**Objective**: Remove metadata service parameters from service class constructors.

**Tasks**:
- Update `ReviewerManagementService.__init__()` to remove `metadata_service` parameter
- Update `TaskManagementService.__init__()` to remove `metadata_service` parameter (if it has one)
- Update `StatisticsService.__init__()` to remove `metadata_service` parameter
- Update any other services that depend on metadata
- Ensure services receive only the dependencies they actually need (repo, base_branch, etc.)

**Example change**:
```python
# OLD
class ReviewerManagementService:
    def __init__(self, repo: str, metadata_service: MetadataService):
        self.repo = repo
        self.metadata_service = metadata_service

# NEW
class ReviewerManagementService:
    def __init__(self, repo: str):
        self.repo = repo
```

**Success criteria**: No service constructors reference metadata service.

---

- [ ] Phase 8: Clean up GitHub operations infrastructure

**Objective**: Ensure GitHub operations layer has all needed query functions.

**Tasks**:
- Verify `list_pull_requests()` supports filtering by:
  - `state` (open, closed, merged)
  - `label` (e.g., "claudestep")
  - `assignee` (reviewer username)
- Add any missing query parameters needed for statistics or reviewer management
- Ensure return types use `GitHubPullRequest` domain models (not raw dicts)
- Add pagination support if needed for repos with 100+ PRs

**Key file**:
- `src/claudestep/infrastructure/github/operations.py`

**Success criteria**: All GitHub PR queries needed by services are available and tested.

---

- [ ] Phase 9: Update tests

**Objective**: Update all tests to remove metadata mocking and use GitHub API mocking instead.

**Tasks**:
- Update service tests to mock GitHub API calls instead of metadata service
- Remove metadata service fixtures from `tests/conftest.py`
- Update CLI integration tests to mock GitHub operations instead of metadata
- Add new tests for branch name parsing and project extraction
- Ensure all tests pass with new architecture

**Key test files to update**:
- `tests/unit/services/test_reviewer_management.py`
- `tests/unit/services/test_statistics_service.py`
- `tests/integration/cli/commands/test_prepare.py`
- `tests/integration/cli/commands/test_finalize.py`
- `tests/integration/cli/commands/test_statistics.py`
- `tests/conftest.py` - Remove metadata-related fixtures

**Pattern change**:
```python
# OLD - Mock metadata
mock_metadata_service = Mock()
mock_metadata_service.get_project.return_value = project_data

# NEW - Mock GitHub API
mock_list_prs = Mock(return_value=[
    GitHubPullRequest(number=123, state="open", assignee="alice", ...)
])
```

**Success criteria**: All unit and integration tests pass without metadata dependencies.

---

- [ ] Phase 10: Validation

**Objective**: Ensure the simplified architecture works correctly and nothing was broken.

**Testing approach**:
1. **Unit tests**: Run all unit tests to verify individual components
   ```bash
   PYTHONPATH=src:scripts pytest tests/unit/ -v
   ```

2. **Integration tests**: Run all integration tests to verify command orchestration
   ```bash
   PYTHONPATH=src:scripts pytest tests/integration/ -v
   ```

3. **Coverage check**: Ensure coverage remains above 70% threshold
   ```bash
   PYTHONPATH=src:scripts pytest tests/unit/ tests/integration/ --cov=src/claudestep --cov-report=term-missing --cov-fail-under=70
   ```

4. **Manual verification** (optional):
   - Create a test project with spec.md
   - Run prepare command → verify it creates PR with correct assignee
   - Run statistics command → verify it generates report from GitHub data
   - Check PR branch name follows `claude-step-<project>-<task>` pattern
   - Verify reviewer capacity checking works by querying GitHub

**Success criteria**:
- All tests pass (unit + integration)
- Coverage >= 70%
- No errors when running CLI commands
- Statistics accurately reflect GitHub PR data
- Reviewer assignment works based on GitHub assignees

**Rollback plan** (if validation fails):
- Git history preserves all metadata code
- Can revert commits phase by phase if needed
- Identify specific failures and fix before proceeding

---

## Benefits After Completion

1. **Simplicity**: GitHub is the only source of truth - no sync issues
2. **Fewer moving parts**: No metadata branch to manage, no complex schema
3. **Lower maintenance**: Less code to maintain, test, and debug
4. **Clearer architecture**: Direct GitHub queries, no abstraction layers
5. **More reliable**: No risk of metadata diverging from GitHub reality
6. **Easier to understand**: New developers see GitHub API usage, not metadata indirection

## Trade-offs

1. **Performance**: Statistics may be slower due to GitHub API queries (acceptable for infrequent use)
2. **Rate limits**: More API calls may hit rate limits in extreme cases (can add caching if needed)
3. **Historical data**: Lose any metadata-specific tracking like AI operation costs (can add back as PR comments if needed later)

## Notes

- The architecture documentation mentions GitHub PR operations infrastructure already exists in `infrastructure/github/operations.py` with functions like `list_pull_requests()` - we'll leverage this existing code
- Branch naming convention `claude-step-<project>-<task>` is already established
- This aligns with the original simple architecture that worked well
