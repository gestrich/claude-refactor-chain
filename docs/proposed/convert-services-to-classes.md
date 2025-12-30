# Convert Function-Based Services to Class-Based Services

## Background

Currently, ClaudeStep has a mix of function-based and class-based services in `src/claudestep/application/services/`:

**Already class-based:**
- `metadata_service.py` - MetadataService class
- `artifact_operations.py` - ArtifactService class (assumed based on grep)

**Function-based (to be converted):**
- `pr_operations.py` - PR and branch naming utilities
- `project_detection.py` - Project detection from PRs and paths
- `reviewer_management.py` - Reviewer capacity and assignment
- `statistics_service.py` - Statistics collection and aggregation
- `task_management.py` - Task finding, marking, and tracking

### Why Convert to Classes?

1. **Consistency** - All services will follow the same pattern, making the codebase more predictable
2. **Dependency Injection** - Easier to inject dependencies (repo, metadata_service, etc.) instead of passing as parameters
3. **Testability** - Better control over mocking and test setup with constructor injection
4. **Reduce Repetition** - Services currently recreate `GitHubMetadataStore` and `MetadataService` in each function
5. **State Management** - Services can cache configuration and avoid redundant GitHub API calls
6. **Future Flexibility** - Easier to add new methods or refactor without changing function signatures everywhere

### Design Principles

Each service class will:
- Accept dependencies via constructor (e.g., `repo`, `MetadataService`)
- Expose public methods that match current function signatures (for backward compatibility during transition)
- Use instance variables for shared state (repo, metadata_service, etc.)
- Follow single responsibility principle
- Be instantiated once per command execution (in CLI commands)

## Phases

- [x] Phase 1: Convert `task_management.py` to `TaskManagementService` ✅

**Status: COMPLETED**

Successfully converted task management functions to a class-based service with proper dependency injection.

**Changes made:**
- ✅ Converted `task_management.py` to `TaskManagementService` class
- ✅ Updated `prepare.py` to instantiate and use `TaskManagementService`
- ✅ Updated `finalize.py` to use `TaskManagementService.mark_task_complete()` as static method
- ✅ Updated `discover_ready.py` to instantiate and use `TaskManagementService`
- ✅ Updated unit tests (`test_task_management.py`) to use the class-based service
- ✅ Updated integration tests to mock the service class

**Implementation notes:**
- `generate_task_id()` and `mark_task_complete()` are implemented as `@staticmethod` since they don't require instance state
- `find_next_available_task()` and `get_in_progress_task_indices()` are instance methods that use `self.metadata_service`
- Service is instantiated once per command execution in CLI commands
- Eliminated redundant `GitHubMetadataStore` and `MetadataService` creation in `get_in_progress_task_indices()`
- All 18 unit tests passing
- Core integration tests updated and passing

**Technical details:**
- Constructor signature: `__init__(self, repo: str, metadata_service: MetadataService)`
- Instance variables: `self.repo`, `self.metadata_service`
- Methods maintain backward-compatible signatures for smooth transition

- [x] Phase 2: Convert `reviewer_management.py` to `ReviewerManagementService` ✅

**Status: COMPLETED**

Successfully converted reviewer management functions to a class-based service with proper dependency injection.

**Changes made:**
- ✅ Converted `reviewer_management.py` to `ReviewerManagementService` class
- ✅ Updated service to use `find_project_artifacts` from artifact_operations instead of old metadata service approach
- ✅ Updated `prepare.py` to instantiate and use `ReviewerManagementService`
- ✅ Updated `discover_ready.py` to instantiate and use `ReviewerManagementService`
- ✅ Updated unit tests (`test_reviewer_management.py`) to use the class-based service
- ✅ Updated integration tests to mock the service class
- ✅ All 16 unit tests passing
- ✅ All integration tests for prepare and discover_ready passing (58 total)

**Implementation notes:**
- `find_available_reviewer()` is an instance method that uses `self.repo` and `self.metadata_service`
- Service now uses `find_project_artifacts()` API for getting open PR artifacts instead of directly accessing metadata service
- Service is instantiated once per command execution in CLI commands
- Eliminated redundant `GitHubMetadataStore` and `MetadataService` creation
- Method maintains backward-compatible signature for smooth transition

**Technical details:**
- Constructor signature: `__init__(self, repo: str, metadata_service: MetadataService)`
- Instance variables: `self.repo`, `self.metadata_service`
- Method uses artifact metadata for PR tracking instead of project metadata directly

- [x] Phase 3: Convert `pr_operations.py` to `PROperationsService` ✅

**Status: COMPLETED**

Successfully converted PR operations functions to a class-based service with proper dependency injection.

**Changes made:**
- ✅ Converted `pr_operations.py` to `PROperationsService` class
- ✅ Updated `prepare.py` to instantiate and use `PROperationsService`
- ✅ Updated `artifact_operations.py` to use `PROperationsService`
- ✅ Updated `project_detection.py` to use `PROperationsService`
- ✅ Updated unit tests (`test_pr_operations.py`) to use the class-based service
- ✅ Updated unit tests (`test_artifact_operations.py`) to mock the service class
- ✅ All 21 PR operations unit tests passing
- ✅ All 48 artifact operations unit tests passing
- ✅ All 47 project detection unit tests passing
- ✅ All 24 prepare command integration tests passing

**Implementation notes:**
- `format_branch_name()` and `parse_branch_name()` are implemented as `@staticmethod` since they are pure functions
- `get_project_prs()` is an instance method that uses `self.repo`
- Service is instantiated once per command execution in CLI commands
- In `artifact_operations.py`, the service is instantiated within the `find_project_artifacts()` function
- In `project_detection.py`, static method `parse_branch_name()` is called directly on the class

**Technical details:**
- Constructor signature: `__init__(self, repo: str)`
- Instance variables: `self.repo`
- Static methods maintain the same signatures for backward compatibility

- [ ] Phase 4: Convert `project_detection.py` to `ProjectDetectionService`

Convert project detection functions to a class-based service.

**Files to modify:**
- `src/claudestep/application/services/project_detection.py`
- `src/claudestep/cli/commands/prepare.py` (usage)
- `tests/unit/application/services/test_project_detection.py`

**New class structure:**
```python
class ProjectDetectionService:
    """Service for project detection from PRs and paths"""

    def __init__(self, repo: str):
        self.repo = repo

    def detect_project_from_pr(self, pr_number: str) -> Optional[str]:
        # Use self.repo instead of parameter

    @staticmethod
    def detect_project_paths(project_name: str) -> tuple:
        # Pure function, can be static method
```

**Update CLI commands:**
- Instantiate `ProjectDetectionService` with repo
- Update function calls to method calls

**Expected outcome:** Project detection logic centralized in a service.

- [ ] Phase 5: Convert `statistics_service.py` to `StatisticsService`

Convert statistics collection functions to a class-based service. This is the most complex service as it orchestrates multiple operations.

**Files to modify:**
- `src/claudestep/application/services/statistics_service.py`
- `src/claudestep/cli/commands/statistics.py` (usage)
- `tests/unit/application/services/test_statistics_service.py`
- `tests/integration/cli/commands/test_statistics.py`

**New class structure:**
```python
class StatisticsService:
    """Service for collecting and aggregating project statistics"""

    def __init__(self, repo: str, metadata_service: MetadataService):
        self.repo = repo
        self.metadata_service = metadata_service

    @staticmethod
    def extract_cost_from_comment(comment_body: str) -> Optional[float]:
        # Pure function, can be static method

    def collect_project_costs(self, project_name: str, label: str = "claudestep") -> float:
        # Use self.metadata_service instead of creating it

    @staticmethod
    def count_tasks(spec_input: str) -> Tuple[int, int]:
        # Pure function, can be static method

    def collect_team_member_stats(self, reviewers: List[str], days_back: int = 30, label: str = "claudestep") -> Dict[str, TeamMemberStats]:
        # Use self.repo instead of parameter

    def collect_project_stats(self, project_name: str, base_branch: str = "main", label: str = "claudestep") -> ProjectStats:
        # Use self.metadata_service and self.repo

    def collect_all_statistics(self, config_path: Optional[str] = None, days_back: int = 30) -> StatisticsReport:
        # Use self.repo and self.metadata_service
        # Main entry point remains similar signature for backward compatibility
```

**Update CLI commands:**
- Create `StatisticsService` instance with repo and metadata_service in `cmd_statistics`
- Update `collect_all_statistics()` call to `service.collect_all_statistics()`
- This will eliminate redundant metadata service creation across all statistics functions

**Expected outcome:** Statistics service eliminates redundant object creation and has clear dependencies.

- [ ] Phase 6: Update Service Instantiation Pattern in CLI Commands

Establish a consistent pattern for service instantiation across all CLI commands.

**Files to modify:**
- `src/claudestep/cli/commands/prepare.py`
- `src/claudestep/cli/commands/finalize.py`
- `src/claudestep/cli/commands/statistics.py`
- `src/claudestep/cli/commands/discover_ready.py`
- Any other commands using services

**Pattern to establish:**
```python
def cmd_prepare(args: argparse.Namespace, gh: GitHubActionsHelper) -> int:
    # Get common dependencies
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    # Initialize infrastructure
    metadata_store = GitHubMetadataStore(repo)
    metadata_service = MetadataService(metadata_store)

    # Initialize services
    task_service = TaskManagementService(repo, metadata_service)
    reviewer_service = ReviewerManagementService(repo, metadata_service)
    project_service = ProjectDetectionService(repo)
    pr_service = PROperationsService(repo)

    # Use services throughout command
    project = project_service.detect_project_from_pr(pr_number)
    task = task_service.find_next_available_task(spec_content)
    reviewer = reviewer_service.find_available_reviewer(reviewers, label, project)
    branch = pr_service.format_branch_name(project, task_index)
```

**Expected outcome:** Consistent service initialization pattern across all commands, making code easier to understand and maintain.

- [ ] Phase 7: Update Architecture Documentation

Update documentation to reflect the new class-based service pattern.

**Files to modify:**
- `docs/architecture/architecture.md` - Update "Services" section
- `docs/architecture/testing-guide.md` - Update service testing examples
- Add examples of service instantiation and usage

**Documentation updates:**
- Explain service constructor pattern
- Show how to instantiate services in commands
- Update testing examples to show mocking services
- Add benefits of class-based approach

**Expected outcome:** Documentation accurately reflects the class-based service architecture.

- [ ] Phase 8: Validation and Testing

Comprehensive validation of the refactoring to ensure no regressions.

**Testing approach:**

1. **Unit Tests** - Run all unit tests for services:
   ```bash
   PYTHONPATH=src:scripts pytest tests/unit/application/services/ -v
   ```
   - All tests should pass
   - Coverage should remain at or above current levels

2. **Integration Tests** - Run CLI command integration tests:
   ```bash
   PYTHONPATH=src:scripts pytest tests/integration/cli/commands/ -v
   ```
   - All commands should work with new service classes
   - Test prepare, finalize, statistics, discover_ready commands

3. **Manual Testing** - Test key workflows:
   - Run `prepare` command to verify task finding and reviewer assignment
   - Run `statistics` command to verify stats collection
   - Run `finalize` command to verify task completion

4. **Code Review**:
   - Verify all function calls have been converted to method calls
   - Check for any remaining imports of old function-based APIs
   - Ensure consistent service instantiation across commands
   - Verify no redundant metadata service creation

**Success criteria:**
- ✅ All unit tests pass (506+ tests)
- ✅ All integration tests pass
- ✅ No function-based service APIs remain in `services/` directory
- ✅ All CLI commands instantiate services consistently
- ✅ Documentation updated to reflect new patterns
- ✅ No degradation in test coverage
- ✅ Manual testing confirms all workflows work

**Expected outcome:** Complete confidence that the refactoring is correct and no functionality has been broken.

## Notes

- **Backward Compatibility**: During transition, we could maintain function wrappers that call class methods, but for a clean refactor, we'll update all call sites directly
- **Service Lifespan**: Services are instantiated once per CLI command execution and don't persist across invocations
- **Testing Strategy**: Update tests to instantiate services with mock dependencies rather than mocking individual functions
- **Performance**: Class-based approach should improve performance by reducing redundant object creation (especially GitHubMetadataStore and MetadataService)
