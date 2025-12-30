## Background

The service classes in `src/claudestep/application/services/` currently have methods organized in various orders without a consistent structure. To improve code readability and maintainability, we should reorganize all methods following Python best practices:

1. **Public before private**: Public methods (part of the API) should appear before private/internal methods (prefixed with `_`)
2. **High-level before low-level**: More abstract, higher-level operations should come before detailed implementation helpers
3. **Logical grouping**: Related methods should be grouped together with clear section comments
4. **Standard order**: Special methods, class methods, static methods, then instance methods

This reorganization will make it easier for developers to:
- Understand the public API of each service at a glance
- Navigate the codebase more intuitively
- Distinguish between public interfaces and internal implementation details

The services to reorganize are:
- `TaskManagementService` (task_management.py)
- `ReviewerManagementService` (reviewer_management.py)
- `PROperationsService` (pr_operations.py)
- `ProjectDetectionService` (project_detection.py)
- `MetadataService` (metadata_service.py)
- `StatisticsService` (statistics_service.py)
- `artifact_operations.py` (module-level functions and classes)

## Phases

- [ ] Phase 1: Reorganize TaskManagementService

Reorganize methods in `src/claudestep/application/services/task_management.py` following this order:

1. `__init__()` - Constructor
2. **Public API methods** (high-level operations first):
   - `find_next_available_task()` - High-level: Find next available task
   - `get_in_progress_task_indices()` - High-level: Query in-progress tasks
   - `mark_task_complete()` - High-level: Mark task complete
3. **Static/utility methods**:
   - `generate_task_id()` - Utility: Generate task IDs

Current issues:
- Static method `generate_task_id()` is placed between constructor and main methods
- Methods are not clearly grouped by abstraction level

Expected result: Methods ordered from highest-level public API to lowest-level utilities, making the service's purpose immediately clear.

- [ ] Phase 2: Reorganize ReviewerManagementService

Reorganize methods in `src/claudestep/application/services/reviewer_management.py`:

1. `__init__()` - Constructor
2. **Public API methods**:
   - `find_available_reviewer()` - Main public method for finding reviewers

Current status: This service is already well-organized with only one public method.

Expected result: Minimal changes needed, possibly add section comments for clarity.

- [ ] Phase 3: Reorganize PROperationsService

Reorganize methods in `src/claudestep/application/services/pr_operations.py` following this order:

1. `__init__()` - Constructor
2. **Public API methods** (high-level first):
   - `get_project_prs()` - High-level: Fetch all PRs for a project
3. **Static utility methods** (high to low level):
   - `format_branch_name()` - Format branch names
   - `parse_branch_name()` - Parse branch names

Current issues:
- Static methods appear before the main public API method `get_project_prs()`
- Branch naming utilities should be after main operations

Expected result: Main PR operations first, then naming utilities.

- [ ] Phase 4: Reorganize ProjectDetectionService

Reorganize methods in `src/claudestep/application/services/project_detection.py`:

1. `__init__()` - Constructor
2. **Public API methods** (instance methods first):
   - `detect_project_from_pr()` - Detect project from PR
3. **Static utility methods**:
   - `detect_project_paths()` - Utility: Determine project paths

Current status: Methods are reasonably ordered but could benefit from clearer grouping.

Expected result: Instance methods before static utilities, with section comments.

- [ ] Phase 5: Reorganize MetadataService

Reorganize methods in `src/claudestep/application/services/metadata_service.py` following this order:

1. `__init__()` - Constructor
2. **Section: Core CRUD Operations** (already well-organized):
   - `get_project()`
   - `save_project()`
   - `list_all_projects()`
   - `get_or_create_project()`
3. **Section: Query Operations** (already well-organized):
   - `find_in_progress_tasks()`
   - `get_reviewer_assignments()`
   - `get_open_prs_by_reviewer()`
4. **Section: PR Workflow Operations** (already well-organized):
   - `add_pr_to_project()`
   - `update_pr_state()`
   - `update_task_status()`
5. **Section: Statistics and Reporting Operations** (already well-organized):
   - `get_projects_modified_since()`
   - `get_project_stats()`
   - `get_reviewer_capacity()`
6. **Section: Utility Operations** (already well-organized):
   - `project_exists()`
   - `list_project_names()`

Current status: This service is already excellently organized with clear sections and comments.

Expected result: Verify organization is optimal, possibly minor adjustments to section comments for consistency.

- [ ] Phase 6: Reorganize StatisticsService

Reorganize methods in `src/claudestep/application/services/statistics_service.py` following this order:

1. `__init__()` - Constructor
2. **Public API methods** (high-level first):
   - `collect_all_statistics()` - Highest level: Collect everything
   - `collect_project_stats()` - Mid-level: Single project stats
   - `collect_team_member_stats()` - Mid-level: Team member stats
   - `collect_project_costs()` - Mid-level: Project costs
3. **Static utility methods**:
   - `count_tasks()` - Low-level: Count tasks from spec
   - `extract_cost_from_comment()` - Low-level: Parse cost from text

Current issues:
- Static utilities (`extract_cost_from_comment`, `count_tasks`) are mixed between high-level methods
- Not organized from high to low abstraction level

Expected result: Clear progression from highest-level "collect all" down through specific collectors to parsing utilities.

- [ ] Phase 7: Reorganize artifact_operations.py

Reorganize module-level code in `src/claudestep/application/services/artifact_operations.py`:

1. **Classes** (public before private):
   - `TaskMetadata` (dataclass) - Public model
   - `ProjectArtifact` (dataclass) - Public model
2. **Public API functions** (high to low level):
   - `find_project_artifacts()` - Highest level: Main API
   - `get_artifact_metadata()` - Mid-level: Get specific artifact
   - `find_in_progress_tasks()` - Mid-level: Convenience wrapper
   - `get_reviewer_assignments()` - Mid-level: Convenience wrapper
3. **Module utilities**:
   - `parse_task_index_from_name()` - Utility: Parse task index
4. **Private helper functions** (prefix with `_`):
   - `_get_workflow_runs_for_branch()`
   - `_get_artifacts_for_run()`
   - `_filter_project_artifacts()`

Current issues:
- Private helper functions are not prefixed with `_` but should be
- Utility function `parse_task_index_from_name()` appears before main API
- Not organized by abstraction level

Expected result: Clear separation of public API, utilities, and private helpers, with consistent naming.

- [ ] Phase 8: Update imports and verify functionality

After reorganizing all services:

1. Run all unit tests to ensure no functionality broken:
   ```bash
   pytest tests/unit/application/services/
   ```

2. Check for any import issues or circular dependencies

3. Verify that the reorganization doesn't affect the public API contracts

Expected result: All tests pass with no regression in functionality.

- [ ] Phase 9: Validation

Run the full test suite to ensure all reorganizations maintain correct behavior:

```bash
# Run all unit tests
pytest tests/unit/

# Run integration tests if available
pytest tests/integration/ || echo "No integration tests"

# Verify no regressions
git diff --stat
```

Success criteria:
- All tests pass
- No changes to public API behavior
- Code is more readable and follows consistent organization
- Private methods are clearly distinguished from public API
- Methods are ordered from high-level to low-level within each section
