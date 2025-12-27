# Test Coverage Improvement Plan

## Overview

This document outlines a comprehensive plan to improve test coverage in the ClaudeStep project by implementing Python testing best practices. The goal is to achieve robust, maintainable test coverage that enables confident refactoring and prevents regressions.

## Recent Updates (December 2025)

### Architecture Modernization (December 27, 2025)
Following the completion of the architecture modernization (see `docs/completed/architecture-update.md`), this test plan has been updated to reflect:

1. **Layered Architecture** - Code reorganized into domain, infrastructure, application, and CLI layers
2. **Test Structure Reorganized** - Tests now mirror the `src/` structure in `tests/unit/`
3. **All 112 Tests Passing** - Fixed failing `test_prepare_summary.py` tests
4. **CI Workflow Added** - Unit tests run automatically on push and PR
5. **E2E Tests Updated** - Demo repository tests working with new architecture

### Branch Naming Simplification
Following the completion of the branch naming simplification refactoring (see `docs/completed/simplify-branch-naming.md`):

1. **New `pr_operations.py` module** - Centralized PR utilities with comprehensive tests (21 test cases) already implemented
2. **Simplified branch naming** - All tests use the standard format `claude-step-{project}-{index}`
3. **Removed `branchPrefix` configuration** - Tests verify this field is rejected with a helpful error message
4. **Simplified `project_detection.py`** - Uses centralized `parse_branch_name()` utility
5. **Centralized PR fetching** - Multiple modules now use shared `get_project_prs()` utility

These changes reduce code duplication and simplify the testing surface area.

## Current State

### Test Infrastructure ✅
- `pytest.ini` - Pytest configuration
- `.github/workflows/test.yml` - CI workflow for unit tests
- `pyproject.toml` - Package configuration with test dependencies
- Tests run on every push and PR to main branch
- **112 tests passing** with 0 failures

### Existing Tests (Organized by Layer)
**Application Layer:**
- `tests/unit/application/collectors/test_statistics.py` - Statistics models and collectors (44 tests)
- `tests/unit/application/formatters/test_table_formatter.py` - Table formatting utilities (19 tests)
- `tests/unit/application/services/test_pr_operations.py` - PR operations (21 tests)
- `tests/unit/application/services/test_task_management.py` - Task finding and marking (19 tests)

**CLI Layer:**
- `tests/unit/cli/commands/test_prepare_summary.py` - PR summary command (9 tests)

**Integration:**
- Demo repository: `claude-step-demo/tests/integration/test_workflow_e2e.py` - End-to-end workflow

### Coverage Gaps
The following modules lack unit tests:

**Domain Layer:**
- `src/claudestep/domain/models.py` - Core domain models
- `src/claudestep/domain/config.py` - Configuration models and validation
- `src/claudestep/domain/exceptions.py` - Custom exception hierarchy

**Infrastructure Layer:**
- `src/claudestep/infrastructure/git/operations.py` - Git command wrappers
- `src/claudestep/infrastructure/github/operations.py` - GitHub CLI wrappers
- `src/claudestep/infrastructure/github/actions.py` - GitHub Actions helpers
- `src/claudestep/infrastructure/filesystem/operations.py` - File I/O utilities

**Application Layer:**
- `src/claudestep/application/services/reviewer_management.py` - Reviewer capacity management
- `src/claudestep/application/services/project_detection.py` - Project detection
- `src/claudestep/application/services/artifact_operations.py` - Artifact management

**CLI Layer:**
- `src/claudestep/cli/commands/discover.py` - Project discovery
- `src/claudestep/cli/commands/discover_ready.py` - Ready project discovery
- `src/claudestep/cli/commands/prepare.py` - Task preparation
- `src/claudestep/cli/commands/finalize.py` - Task finalization
- `src/claudestep/cli/commands/statistics.py` - Statistics reporting
- `src/claudestep/cli/commands/extract_cost.py` - Cost extraction
- `src/claudestep/cli/commands/add_cost_comment.py` - Cost comment posting
- `src/claudestep/cli/commands/notify_pr.py` - PR notifications

## Testing Principles to Follow

Based on Python testing best practices:

1. **Test Isolation** - Each test is independent with clean state
2. **Fast Execution** - Mock external dependencies (GitHub API, git commands, file system where appropriate)
3. **One Concept Per Test** - Each test validates one specific behavior
4. **Descriptive Names** - Test names explain the scenario being tested
5. **Arrange-Act-Assert** - Clear test structure
6. **Parametrization** - Use pytest.mark.parametrize for similar test cases
7. **Proper Mocking** - Mock external services, not internal logic
8. **Edge Case Coverage** - Test boundary conditions, empty inputs, errors

## Implementation Plan

### Phase 1: Infrastructure & Core Utilities ✅ MOSTLY COMPLETE

- [x] **Set up test infrastructure** ✅
  - ✅ Add `pytest.ini` configuration file
  - ✅ Set up code coverage reporting with `pytest-cov` in CI
  - ✅ Tests run automatically in CI/CD (`.github/workflows/test.yml`)
  - ✅ Package structure supports testing (`pyproject.toml` configured)
  - Pending: Configure coverage thresholds in CI/CD
  - Pending: Add `conftest.py` with common fixtures
  - Pending: Document how to run tests in development

- [ ] **Create common test fixtures** (`tests/conftest.py`)
  - Fixture for temporary git repository
  - Fixture for mock GitHub API responses
  - Fixture for sample project configurations
  - Fixture for spec.md files with various states
  - Fixture for mocked GitHubActionsHelper

- [ ] **Test domain layer** (`tests/unit/domain/`)
  - Test `exceptions.py` - Custom exception classes and inheritance
  - Test `models.py` - Domain model validation and serialization
  - Test `config.py` - Configuration loading, validation, and branchPrefix rejection

### Phase 2: Infrastructure Layer

- [x] **Test pr_operations.py** ✅ COMPLETE (`tests/unit/application/services/test_pr_operations.py`)
  - 21 comprehensive tests covering branch name generation, parsing, and PR fetching
  - Branch name format validation (`claude-step-{project}-{index}`)
  - Complex project names with hyphens, invalid input handling
  - PR fetching with various states (open, merged, all)
  - Error handling for API failures

- [ ] **Test git operations** (`tests/unit/infrastructure/git/test_operations.py`)
  - Mock subprocess calls to git commands
  - Test `create_branch()`, `commit_changes()`, `push_branch()`, `get_current_branch()`
  - Test error handling for git command failures
  - Test proper command construction (quoting, arguments)

- [ ] **Test GitHub operations** (`tests/unit/infrastructure/github/test_operations.py`)
  - Mock GitHub CLI (`gh`) commands
  - Test `create_pull_request()`, `get_open_prs()`, `close_pull_request()`, `add_pr_comment()`, `get_pr_diff()`
  - Test error handling for GitHub API failures, rate limiting, authentication errors

- [ ] **Test GitHub Actions helpers** (`tests/unit/infrastructure/github/test_actions.py`)
  - Mock environment variables (GITHUB_OUTPUT, GITHUB_STEP_SUMMARY)
  - Test `write_output()`, `write_summary()`, `set_failed()`
  - Test output sanitization (special characters, multiline)

- [ ] **Test filesystem operations** (`tests/unit/infrastructure/filesystem/test_operations.py`)
  - Test `read_file()`, `write_file()`, `file_exists()`, `find_file()`
  - Test error handling for missing files, permission errors
  - Test path normalization and validation

### Phase 3: Application Services Layer

- [x] **Test task_management.py** ✅ COMPLETE (`tests/unit/application/services/test_task_management.py`)
  - 19 tests covering task finding, marking, ID generation
  - Tests for in-progress tasks, completed tasks, edge cases

- [x] **Test statistics_collector.py** ✅ COMPLETE (`tests/unit/application/collectors/test_statistics.py`)
  - 44 tests covering progress bars, task counting, team member stats, project stats
  - Leaderboard functionality, cost extraction

- [x] **Test table_formatter.py** ✅ COMPLETE (`tests/unit/application/formatters/test_table_formatter.py`)
  - 19 tests covering visual width calculation, padding, emoji support, table formatting

- [ ] **Test reviewer_management.py** (`tests/unit/application/services/test_reviewer_management.py`)
  - Test `check_reviewer_capacity()`, `find_available_reviewer()`, reviewer rotation
  - Test capacity calculation with various PR states
  - Test edge cases (no reviewers, all at capacity, zero maxOpenPRs)

- [ ] **Test project_detection.py** (`tests/unit/application/services/test_project_detection.py`)
  - Test detecting project from environment variable and PR branch name using `parse_branch_name()`
  - Test project path resolution, spec.md/configuration.yml file discovery
  - Test error cases (project not found, missing files, invalid branch names)
  - Test simplified branch format parsing (`claude-step-{project}-{index}`)

- [ ] **Test artifact_operations.py** (`tests/unit/application/services/test_artifact_operations.py`)
  - Test artifact creation, reading, writing, metadata handling
  - Test error cases (missing artifacts, malformed JSON)

### Phase 4: CLI Commands Layer

- [x] **Test prepare_summary.py** ✅ COMPLETE (`tests/unit/cli/commands/test_prepare_summary.py`)
  - 9 tests covering prompt template loading, variable substitution, output formatting
  - Tests for missing inputs, error handling, workflow URL construction

- [ ] **Test prepare.py** (`tests/unit/cli/commands/test_prepare.py`)
  - Mock all external dependencies (git, GitHub, file system)
  - Test successful preparation workflow, reviewer capacity check, task discovery
  - Test branch creation using `format_branch_name()` utility with format `claude-step-{project}-{index}`
  - Test prompt generation, output variable setting
  - Test failure scenarios (no capacity, no tasks, missing files)
  - Test skip_indices handling for in-progress tasks

- [ ] **Test finalize.py** (`tests/unit/cli/commands/test_finalize.py`)
  - Mock git and GitHub operations
  - Test commit creation, spec.md task marking, PR creation with template substitution
  - Test metadata artifact creation
  - Test handling no changes scenario and error recovery

- [ ] **Test discover.py** (`tests/unit/cli/commands/test_discover.py`)
  - Mock file system operations
  - Test finding all projects in claude-step/, filtering valid projects (must have spec.md)
  - Test output formatting (JSON), empty directory and invalid project structure handling

- [ ] **Test discover_ready.py** (`tests/unit/cli/commands/test_discover_ready.py`)
  - Mock GitHub API for PR queries
  - Test finding projects with available capacity, filtering by reviewer capacity
  - Test output formatting, all reviewers at capacity scenario, projects with no reviewers

- [ ] **Test statistics.py** (`tests/unit/cli/commands/test_statistics.py`)
  - Mock statistics collector
  - Test report generation workflow, output formatting (JSON, Slack)
  - Test GitHub Actions output writing, handling projects with no tasks, date range filtering

- [ ] **Test add_cost_comment.py** (`tests/unit/cli/commands/test_add_cost_comment.py`)
  - Mock GitHub API for comment posting
  - Test cost extraction and formatting, comment creation on PR
  - Test handling missing cost data and invalid PR numbers

- [ ] **Test extract_cost.py** (`tests/unit/cli/commands/test_extract_cost.py`)
  - Mock artifact reading
  - Test cost data extraction from metadata, parsing various cost formats
  - Test handling missing artifacts and output formatting

- [ ] **Test notify_pr.py** (`tests/unit/cli/commands/test_notify_pr.py`)
  - Mock Slack webhook calls
  - Test notification message formatting, webhook request construction
  - Test error handling (webhook failures) and optional notification (when webhook not configured)

### Phase 5: Integration & Quality

- [ ] **Improve existing tests**
  - Review existing tests for additional edge cases and parametrization opportunities
  - Consider adding more boundary condition tests
  - Add tests for error scenarios not currently covered

- [ ] **Add integration test coverage**
  - Test full prepare → finalize workflow (mocked)
  - Test error propagation through command chain
  - Test state management across commands
  - Test concurrent PR handling scenarios

- [ ] **Set up coverage reporting**
  - Configure pytest-cov to track coverage (already in CI)
  - Add coverage report to CI/CD pipeline
  - Set minimum coverage threshold (start at 70%, target 80%+)
  - Generate HTML coverage reports for local development
  - Add coverage badge to README.md
  - Identify and document intentionally untested code

- [ ] **Add property-based testing** (optional, for critical paths)
  - Install `hypothesis` library
  - Add property tests for task ID generation
  - Add property tests for spec.md parsing
  - Add property tests for configuration validation

### Phase 6: Documentation & CI/CD

- [ ] **Document testing practices**
  - Create `docs/testing-guide.md`
  - Document how to run tests locally (`PYTHONPATH=src:scripts pytest tests/unit/ -v`)
  - Document how to write new tests
  - Document mocking strategies
  - Document common fixtures and their usage (once conftest.py is created)
  - Add examples of well-written tests

- [x] **Set up CI/CD testing** ✅ MOSTLY COMPLETE
  - ✅ Add GitHub Actions workflow for running tests on PR (`.github/workflows/test.yml`)
  - ✅ Tests run on every push and PR to main branch
  - Pending: Run tests on multiple Python versions (currently 3.11 only, add 3.12, 3.13)
  - Pending: Add test status badge to README.md
  - Pending: Configure PR merge requirements (tests must pass)
  - Pending: Add coverage reporting to PR comments

- [ ] **Performance testing** (optional)
  - Ensure test suite runs in under 10 seconds (currently ~0.7s in CI, excellent!)
  - Identify and optimize slow tests if any emerge
  - Consider splitting unit vs integration test runs as suite grows
  - Add `pytest-benchmark` for performance-critical code if needed

## Success Criteria

- [ ] **Coverage Goals**
  - [ ] Overall coverage > 80%
  - [ ] All business logic modules > 90% coverage
  - [ ] All command modules tested
  - [ ] All operations modules tested

- [ ] **Quality Goals**
  - [ ] All tests are isolated and independent
  - [ ] Test suite runs in < 10 seconds
  - [ ] No flaky tests
  - [ ] Clear test names and documentation
  - [ ] Proper use of fixtures and parametrization

- [ ] **Process Goals**
  - [ ] Tests run automatically on every PR
  - [ ] Coverage reports visible in PR reviews
  - [ ] Testing guide documented and accessible
  - [ ] New code requires tests (enforced in PR reviews)

## Testing Tools & Dependencies

```bash
# Core testing framework
pytest>=7.0.0

# Coverage reporting
pytest-cov>=4.0.0

# Mocking (built-in to Python 3.3+)
# unittest.mock

# Property-based testing (optional)
hypothesis>=6.0.0

# Performance benchmarking (optional)
pytest-benchmark>=4.0.0
```

## Example Test Structure

```python
# tests/test_reviewer_management.py
import pytest
from unittest.mock import Mock, patch

from claudestep.reviewer_management import check_reviewer_capacity
from claudestep.models import ReviewerConfig


class TestCheckReviewerCapacity:
    """Tests for reviewer capacity checking"""

    @pytest.fixture
    def reviewer_config(self):
        """Fixture providing a sample reviewer configuration"""
        return ReviewerConfig(username="alice", maxOpenPRs=2)

    @pytest.fixture
    def mock_github_api(self):
        """Fixture providing mocked GitHub API"""
        with patch('claudestep.github_operations.get_open_prs') as mock:
            yield mock

    def test_reviewer_under_capacity(self, reviewer_config, mock_github_api):
        """Should return True when reviewer has capacity"""
        # Arrange
        mock_github_api.return_value = [{"number": 1}]  # 1 open PR

        # Act
        result = check_reviewer_capacity(reviewer_config)

        # Assert
        assert result is True
        mock_github_api.assert_called_once_with("alice", label="claude-step")

    def test_reviewer_at_capacity(self, reviewer_config, mock_github_api):
        """Should return False when reviewer is at capacity"""
        # Arrange
        mock_github_api.return_value = [{"number": 1}, {"number": 2}]  # 2 open PRs

        # Act
        result = check_reviewer_capacity(reviewer_config)

        # Assert
        assert result is False

    @pytest.mark.parametrize("open_pr_count,expected", [
        (0, True),   # Under capacity
        (1, True),   # Under capacity
        (2, False),  # At capacity
        (3, False),  # Over capacity
    ])
    def test_capacity_boundaries(self, reviewer_config, mock_github_api, open_pr_count, expected):
        """Should correctly handle various capacity levels"""
        # Arrange
        mock_github_api.return_value = [{"number": i} for i in range(open_pr_count)]

        # Act
        result = check_reviewer_capacity(reviewer_config)

        # Assert
        assert result == expected
```

## Migration Strategy

### Approach: Incremental Implementation

1. **Start with infrastructure** (Phase 1) to establish testing patterns
2. **Test operations layer** (Phase 2) to enable mocking in higher layers
3. **Test business logic** (Phase 3) with operations mocked
4. **Test commands** (Phase 4) with full dependency mocking
5. **Improve quality** (Phase 5) through iteration
6. **Document and automate** (Phase 6) for long-term sustainability

### Prioritization

**High Priority** (implement first):
- ✅ ~~Test infrastructure and fixtures~~ - Partially complete (CI set up, need conftest.py)
- ✅ ~~pr_operations.py~~ - Complete (21 tests)
- Domain layer tests (config.py, models.py, exceptions.py)
- Infrastructure layer tests (git_operations.py, github_operations.py, github_actions.py, filesystem operations)
- reviewer_management.py (business logic)
- commands/prepare.py and commands/finalize.py (main workflows)

**Medium Priority** (implement second):
- ✅ ~~task_management.py~~ - Complete (19 tests)
- ✅ ~~statistics_collector.py~~ - Complete (44 tests)
- ✅ ~~table_formatter.py~~ - Complete (19 tests)
- project_detection.py (simplified after branch naming refactoring)
- artifact_operations.py
- commands/discover.py and commands/discover_ready.py
- ✅ ~~commands/prepare_summary.py~~ - Complete (9 tests)
- commands/statistics.py

**Low Priority** (implement as time allows):
- commands/notify_pr.py (nice-to-have feature)
- commands/add_cost_comment.py (optional feature)
- commands/extract_cost.py (utility)
- Property-based testing
- Performance benchmarking

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Tests become slow due to excessive mocking | Use fixtures efficiently, minimize I/O operations |
| Mocking makes tests brittle | Mock at system boundaries only, not internal functions |
| Coverage metrics without quality | Require code review of tests, enforce best practices |
| Tests don't catch real bugs | Combine unit tests with integration tests, use E2E tests for critical paths |
| Tests become outdated | Run tests in CI/CD, require tests for new features |

## Timeline Estimate

**Current Progress**:
- ✅ Phase 1: ~80% complete (test infrastructure set up, CI running, need conftest.py and domain tests)
- ✅ Phase 2: ~20% complete (pr_operations.py done, need infrastructure layer tests)
- ✅ Phase 3: ~75% complete (task_management, statistics, table_formatter done, need reviewer/project/artifact)
- ✅ Phase 4: ~11% complete (prepare_summary done, need 8 more commands)
- Phase 5: Not started (integration tests and quality improvements)
- ✅ Phase 6: ~40% complete (CI set up, need documentation and enhancements)

**Remaining Effort**:
- **Phase 1**: 0.5 days (conftest.py fixtures, domain layer tests)
- **Phase 2**: 2-3 days (git, github, filesystem infrastructure tests)
- **Phase 3**: 1 day (reviewer_management, project_detection, artifact_operations)
- **Phase 4**: 4-5 days (8 remaining command modules)
- **Phase 5**: 2-3 days (integration tests, coverage reporting)
- **Phase 6**: 1 day (documentation, CI enhancements)

**Total Remaining: 10.5-13.5 days** (can be parallelized or spread over multiple contributors)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Testing Best Practices (Python Guide)](https://docs.python-guide.org/writing/tests/)

## Next Steps

1. ~~Review and approve this proposal~~ ✅ Approved
2. ~~Set up initial testing infrastructure (Phase 1)~~ ✅ In Progress
3. Continue implementing tests following the prioritization order (see below)
4. Review and iterate based on learnings
5. Update this document with progress and adjustments

**Recommended Next Actions** (in priority order):
1. Create `tests/conftest.py` with common fixtures (Phase 1)
2. Add domain layer tests for config.py with branchPrefix rejection validation (Phase 1)
3. Add infrastructure tests for git and github operations (Phase 2)
4. Add application service tests for reviewer_management.py (Phase 3)
5. Add CLI command tests for prepare.py and finalize.py (Phase 4)

## Progress Summary

**Completed (December 2025)**:
- ✅ Architecture modernization with layered structure
- ✅ Test structure reorganized to mirror src/ layout
- ✅ CI workflow added for automated testing
- ✅ All 112 existing tests passing (0 failures)
- ✅ E2E tests updated and working
- ✅ Comprehensive tests for `pr_operations.py` (21 test cases)
- ✅ Comprehensive tests for `task_management.py` (19 test cases)
- ✅ Comprehensive tests for `statistics_collector.py` (44 test cases)
- ✅ Comprehensive tests for `table_formatter.py` (19 test cases)
- ✅ Comprehensive tests for `prepare_summary.py` (9 test cases)
