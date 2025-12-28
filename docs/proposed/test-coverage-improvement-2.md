# Test Coverage Improvement Plan - Phase 2

This document outlines the remaining work to further enhance the testing infrastructure for ClaudeStep. All core testing work is complete (493 tests, 85% coverage). These are optional enhancements.

## Current State

- **493 tests passing** (0 failures)
- **85.03% code coverage** (exceeding 70% minimum)
- **All layers tested**: Domain, Infrastructure, Application, CLI
- **CI/CD integrated**: Tests run on every PR with automated coverage reports
- **Documentation complete**: Testing guide and coverage notes documented

## Remaining Work

The following phases outline optional enhancements to the testing infrastructure:

### Phase 1: Document Testing Architecture ✅

- [x] **Create `docs/architecture/tests.md`** with comprehensive testing architecture documentation

**Purpose:** Provide architectural guidance for testing in the ClaudeStep codebase.

**Implementation Notes (Completed 2025-12-27):**

Created comprehensive testing architecture documentation at `docs/architecture/tests.md` covering:

1. **Testing Philosophy** - Explains core beliefs: test behavior not implementation, mock at boundaries, value over coverage
2. **Testing Principles** - Detailed guidance on:
   - Test isolation and independence (no shared state, order-independent)
   - Mocking strategy (mock external systems at boundaries, not internal logic)
   - Arrange-Act-Assert pattern with clear examples
   - One concept per test (focused, single-responsibility tests)

3. **Test Architecture Overview** - Documents:
   - Directory structure mirroring `src/` layout
   - Layer-based testing strategy (Domain → Infrastructure → Application → CLI)
   - Fixture organization in `conftest.py` with automatic discovery
   - Clear boundaries between unit and integration tests

4. **Testing by Layer** - Layer-specific guidance with examples:
   - **Domain Layer** (99% coverage): Direct testing, minimal mocking
   - **Infrastructure Layer** (97% coverage): Mock external systems (subprocess, GitHub API, filesystem)
   - **Application Layer** (95% coverage): Mock infrastructure, test business logic
   - **CLI Layer** (98% coverage): Mock everything below, test orchestration

5. **What to Test vs What Not to Test** - Clear guidance with examples:
   - ✅ Test: Business logic, edge cases, error handling, integration points
   - ❌ Don't test: Python features, third-party libraries, trivial getters, implementation details

6. **Common Patterns** - Practical examples:
   - Using conftest.py fixtures effectively
   - Parametrized tests for boundary conditions
   - Error handling and edge case testing
   - Future async patterns (if needed)

7. **References** - Links to related documentation:
   - Testing Guide (style guide and conventions)
   - Test Coverage Notes (coverage rationale)
   - Test Coverage Improvement Plan (implementation history)
   - Real code examples from the test suite

**Technical Details:**
- Document is 600+ lines with extensive code examples
- Every principle includes both ✅ GOOD and ❌ BAD examples
- Real examples referenced from existing test files
- Quick reference tables for common questions (when to mock, coverage targets)

**Acceptance Criteria Met:**
- ✅ Explains WHY we test the way we do (philosophy section)
- ✅ Clear guidance on testing new features (layer-by-layer guide)
- ✅ Examples from existing codebase (real test file references)
- ✅ References to related documentation (comprehensive links section)
- ✅ All 493 tests still passing after documentation creation

---

### Phase 2: Dynamic Coverage Badge ✅

- [x] **Integrate Codecov or Coveralls for dynamic coverage badge**

**Purpose:** Automatically update coverage badge without manual edits.

**Implementation Notes (Completed 2025-12-27):**

Integrated Codecov for automatic coverage badge updates:

1. **Workflow Changes** (`.github/workflows/test.yml`):
   - Added `coverage xml` to generate coverage.xml file for Codecov
   - Added Codecov action step that uploads coverage data on every test run
   - Used `codecov/codecov-action@v4` with CODECOV_TOKEN secret
   - Set `fail_ci_if_error: false` to prevent CI failures on Codecov issues

2. **README Updates**:
   - Replaced static badge `![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)`
   - With dynamic Codecov badge: `[![codecov](https://codecov.io/gh/gestrich/claude-step/branch/main/graph/badge.svg)](https://codecov.io/gh/gestrich/claude-step)`
   - Badge will auto-update on each commit once CODECOV_TOKEN is set

3. **Next Steps for Repo Owner**:
   - Sign up at codecov.io and link the gestrich/claude-step repository
   - Add `CODECOV_TOKEN` secret to GitHub repository settings
   - Configure Codecov project settings with 70% minimum threshold
   - Badge will start updating automatically once token is configured

**Technical Details:**
- Coverage data is uploaded on every test run (including PRs)
- XML format is the standard Codecov input format
- Existing HTML and text coverage reports remain unchanged
- All 493 tests pass with the new configuration

**Acceptance Criteria Met:**
- ✅ Badge will update automatically on each commit (once token configured)
- ✅ Badge shows current coverage percentage
- ✅ Ready for 70% minimum threshold configuration in Codecov settings

---

### Phase 6: Test Performance Monitoring

- [ ] **Add pytest-benchmark for performance-critical code**

**Purpose:** Ensure tests remain fast as codebase grows.

**Tasks:**
1. Add `pytest-benchmark` to test dependencies
2. Identify slow tests (if any) using `pytest --durations=10`
3. Add benchmarks for:
   - File parsing operations (spec.md, config.yml)
   - Task searching algorithms
   - Large fixture setup
4. Set performance thresholds
5. Track performance over time in CI

**Dependencies:**
- None (optional enhancement)

**Estimated Effort:** 2-3 hours

**Acceptance Criteria:**
- Benchmark suite runs in CI
- Performance regressions detected
- Documentation for adding benchmarks

---

### Phase 7: Coverage Improvement for Integration Code

- [ ] **Increase coverage of `statistics_collector.py` to 50%+**

**Purpose:** Reduce large coverage gap (currently 15%).

**Current State:**
- 164/193 lines missed
- Tested via integration but not unit tests
- Complex orchestration module

**Approach:**
1. Review `tests/unit/cli/commands/test_statistics.py` (already mocks the collector)
2. Add direct unit tests for `statistics_collector.py` functions:
   - `collect_project_statistics()`
   - `collect_team_member_statistics()`
   - `collect_all_statistics()`
3. Mock dependencies: `get_project_prs()`, `find_project_artifacts()`, etc.
4. Test edge cases: empty data, API failures, parsing errors

**Dependencies:**
- Understanding of statistics collection workflow
- Review `docs/testing-coverage-notes.md` for why this is currently low

**Estimated Effort:** 4-6 hours

**Acceptance Criteria:**
- statistics_collector.py coverage > 50%
- Edge cases tested
- Integration tests still pass

---

### Phase 9: Test Data Builders

- [ ] **Create builder pattern helpers for complex test data**

**Purpose:** Simplify test setup and improve readability.

**Tasks:**
1. Create `tests/builders/` directory with builder classes:
   - `ConfigBuilder` - Fluent interface for creating test configs
   - `PRDataBuilder` - Build PR data with defaults
   - `ArtifactBuilder` - Build artifact metadata
   - `SpecFileBuilder` - Build spec.md content

2. Example:
   ```python
   config = ConfigBuilder()
       .with_reviewer("alice", max_prs=2)
       .with_reviewer("bob", max_prs=1)
       .build()
   ```

3. Refactor existing tests to use builders
4. Document builder pattern in architecture docs

**Dependencies:**
- Phase 1 (architecture docs should mention builders)

**Estimated Effort:** 6-8 hours

**Acceptance Criteria:**
- Builder classes created for main data types
- At least 20% of tests refactored to use builders
- Tests are more readable
- Documentation updated


## Prioritization

**High Priority (Completed):**
1. ✅ Phase 1: Document Testing Architecture (provides foundation for other work)
2. ✅ Phase 2: Dynamic Coverage Badge (professional polish)

**Medium Priority (Good to Have):**
6. Phase 7: Coverage Improvement (addresses known gap)

**Low Priority (Nice to Have):**
7. Phase 6: Test Performance Monitoring (suite is already fast)
8. Phase 9: Test Data Builders (refactoring, not new tests)


## Notes

- All phases are optional enhancements
- Core testing work is complete (85% coverage, 493 tests)
- Focus on phases that provide most value for effort
- Document decisions as you go

## References

- Current test documentation: `docs/testing-guide.md`
- Coverage analysis: `docs/testing-coverage-notes.md`
- Implementation history: `docs/proposed/test-coverage-improvement-plan.md`
- Test fixtures: `tests/conftest.py`
