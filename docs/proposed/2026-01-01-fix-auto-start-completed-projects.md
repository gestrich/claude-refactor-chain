## Background

Currently, the auto-start workflow has a bug where it doesn't trigger for projects that have completed all their tasks and then have new tasks added. This happens because the auto-start logic checks if **any** PRs exist for a project (using `state="all"`), not just **open** PRs.

**The Problem:**
- User completes all tasks for a project (e.g., 3 PRs merged, all closed)
- User adds a new task to spec.md and pushes to the branch
- Auto-start workflow triggers but skips the project because it has existing PRs
- Result: New task never gets processed

**Why This Happens:**
In [src/claudestep/services/composite/auto_start_service.py:120](../../src/claudestep/services/composite/auto_start_service.py#L120), the `determine_new_projects()` method queries:
```python
prs = self.pr_service.get_project_prs(project.name, state="all")
```

This returns ALL PRs (open + closed). If any exist, the project is skipped.

**Correct Behavior:**
Auto-start should only skip projects with **open** PRs. Projects with only closed PRs should be treated as "ready for new work" and trigger normally.

**Use Cases That Should Work:**
1. ✅ **New project** (no PRs at all) → Should trigger
2. ✅ **Completed project with new task** (only closed PRs) → Should trigger
3. ✅ **Active project** (has open PRs) → Should skip (prevents duplicates)

**Architecture Principles:**
- This is a **Service Layer bug** - fix should be in `AutoStartService`
- Follow **Test-Driven Development** - write failing test first, then fix
- Use **unit or integration tests** - E2E tests are too slow/expensive for this
- Follow **testing philosophy** - test behavior, not implementation details

## Phases

- [ ] Phase 1: Write failing unit test

**Goal**: Create unit test that demonstrates the bug - auto-start should trigger for completed projects with new tasks.

**Tasks**:
1. Create new test in [tests/unit/services/composite/test_auto_start_service.py](../../../tests/unit/services/composite/test_auto_start_service.py):
   ```python
   def test_determine_new_projects_treats_completed_projects_as_new(mock_pr_service):
       """Completed projects (only closed PRs) should be treated as new projects.

       This tests the scenario where:
       1. User completes all tasks (all PRs are closed)
       2. User adds new task to spec.md
       3. Auto-start should trigger (not skip the project)
       """
       # Setup: Mock PR service to return 2 CLOSED PRs
       closed_pr_1 = PR(number=1, state="closed", ...)
       closed_pr_2 = PR(number=2, state="closed", ...)
       mock_pr_service.get_project_prs.return_value = [closed_pr_1, closed_pr_2]

       # Create auto-start service
       service = AutoStartService(repo="owner/repo", pr_service=mock_pr_service)

       # Create a changed project
       changed_projects = [
           AutoStartProject(
               name="my-project",
               change_type=ProjectChangeType.MODIFIED,
               spec_path="claude-step/my-project/spec.md"
           )
       ]

       # Act: Determine new projects
       new_projects = service.determine_new_projects(changed_projects)

       # Assert: Should treat as NEW because all PRs are closed
       assert len(new_projects) == 1
       assert new_projects[0].name == "my-project"

       # Verify it queried for OPEN PRs only (not "all")
       mock_pr_service.get_project_prs.assert_called_once_with("my-project", state="open")
   ```

2. Also update the existing test `test_determine_new_projects_skips_projects_with_existing_prs`:
   - Rename to `test_determine_new_projects_skips_projects_with_open_prs`
   - Verify it mocks **open** PRs, not just any PRs
   - Update assertion message to clarify it's checking for open PRs

3. Run the test and verify it **fails** (demonstrating the bug):
   ```bash
   pytest tests/unit/services/composite/test_auto_start_service.py::test_determine_new_projects_treats_completed_projects_as_new -v
   ```

**Expected outcome**: Test fails because current code checks `state="all"` instead of `state="open"`.

---

- [ ] Phase 2: Fix the bug in AutoStartService

**Goal**: Update `determine_new_projects()` to check for open PRs instead of all PRs.

**Tasks**:
1. Update [src/claudestep/services/composite/auto_start_service.py:120](../../src/claudestep/services/composite/auto_start_service.py#L120):

   **Before:**
   ```python
   # Use PRService to get all PRs for this project
   prs = self.pr_service.get_project_prs(project.name, state="all")

   # If no PRs exist, this is a new project
   if len(prs) == 0:
       new_projects.append(project)
       print(f"  ✓ {project.name} is a new project (no existing PRs)")
   else:
       print(f"  ✗ {project.name} has {len(prs)} existing PR(s), skipping")
   ```

   **After:**
   ```python
   # Use PRService to get OPEN PRs for this project
   # Projects with only closed PRs are treated as "ready for new work"
   prs = self.pr_service.get_project_prs(project.name, state="open")

   # If no open PRs exist, this project is ready for work
   if len(prs) == 0:
       new_projects.append(project)
       print(f"  ✓ {project.name} has no open PRs, ready for auto-start")
   else:
       print(f"  ✗ {project.name} has {len(prs)} open PR(s), skipping")
   ```

2. Update the method docstring to clarify the behavior:
   ```python
   def determine_new_projects(self, projects: List[AutoStartProject]) -> List[AutoStartProject]:
       """Check which projects have no open PRs (are ready for work)

       A project is considered "ready for work" if it has no OPEN PRs.
       This includes:
       - Brand new projects (no PRs at all)
       - Completed projects (all PRs are closed)

       Projects with open PRs are skipped to prevent duplicate PR creation.

       Args:
           projects: List of AutoStartProject instances to check

       Returns:
           List of projects that have no open PRs (ready for work)
       ```

3. Apply the same fix to `should_auto_trigger()` method at [line 172](../../src/claudestep/services/composite/auto_start_service.py#L172):

   **Before:**
   ```python
   prs = self.pr_service.get_project_prs(project.name, state="all")

   if len(prs) == 0:
       # New project - should trigger
       return AutoStartDecision(
           project=project,
           should_trigger=True,
           reason="New project detected"
       )
   else:
       # Existing project - should not trigger
       return AutoStartDecision(
           project=project,
           should_trigger=False,
           reason=f"Project has {len(prs)} existing PR(s)"
       )
   ```

   **After:**
   ```python
   prs = self.pr_service.get_project_prs(project.name, state="open")

   if len(prs) == 0:
       # No open PRs - ready for work
       return AutoStartDecision(
           project=project,
           should_trigger=True,
           reason="No open PRs, ready for work"
       )
   else:
       # Has open PRs - should not trigger
       return AutoStartDecision(
           project=project,
           should_trigger=False,
           reason=f"Project has {len(prs)} open PR(s)"
       )
   ```

**Expected outcome**: Both methods now check for `state="open"` instead of `state="all"`.

---

- [ ] Phase 3: Add comprehensive unit tests

**Goal**: Add unit tests covering all scenarios to prevent regression.

**Tasks**:
1. Add test for `should_auto_trigger()` with completed project:
   ```python
   def test_should_auto_trigger_approves_completed_projects(mock_pr_service):
       """Completed projects (only closed PRs) should be approved for triggering."""
       # Mock: Return closed PRs when checking for open PRs
       mock_pr_service.get_project_prs.return_value = []  # No OPEN PRs

       service = AutoStartService(repo="owner/repo", pr_service=mock_pr_service, auto_start_enabled=True)
       project = AutoStartProject(name="my-project", change_type=ProjectChangeType.MODIFIED, spec_path="path")

       decision = service.should_auto_trigger(project)

       assert decision.should_trigger is True
       assert "ready for work" in decision.reason.lower()
       mock_pr_service.get_project_prs.assert_called_once_with("my-project", state="open")
   ```

2. Add test for `should_auto_trigger()` with active project (has open PRs):
   ```python
   def test_should_auto_trigger_skips_projects_with_open_prs(mock_pr_service):
       """Projects with open PRs should be skipped to prevent duplicates."""
       # Mock: Return 1 open PR
       open_pr = PR(number=1, state="open", ...)
       mock_pr_service.get_project_prs.return_value = [open_pr]

       service = AutoStartService(repo="owner/repo", pr_service=mock_pr_service, auto_start_enabled=True)
       project = AutoStartProject(name="my-project", change_type=ProjectChangeType.MODIFIED, spec_path="path")

       decision = service.should_auto_trigger(project)

       assert decision.should_trigger is False
       assert "1 open PR(s)" in decision.reason
       mock_pr_service.get_project_prs.assert_called_once_with("my-project", state="open")
   ```

3. Verify existing tests still pass and update any that relied on `state="all"` behavior

**Expected outcome**: Comprehensive test coverage for all auto-start scenarios.

---

- [ ] Phase 4: Update integration tests if needed

**Goal**: Verify integration between AutoStartService and PRService works correctly.

**Tasks**:
1. Check if [tests/integration/](../../../tests/integration/) has any tests for auto-start workflow

2. If integration tests exist, update them to verify:
   - Auto-start triggers for new projects (no PRs)
   - Auto-start triggers for completed projects (only closed PRs)
   - Auto-start skips active projects (has open PRs)

3. If no integration tests exist, consider adding one that tests the full flow:
   ```python
   def test_auto_start_integration_with_completed_project(github_api_mock):
       """Integration test: Auto-start triggers for completed projects with new tasks."""
       # Setup GitHub API mock to return closed PRs
       github_api_mock.list_pull_requests.return_value = [
           {"number": 1, "state": "closed"},
           {"number": 2, "state": "closed"}
       ]

       # Create real PRService and AutoStartService instances
       pr_service = PRService(repo="owner/repo")
       auto_start_service = AutoStartService(repo="owner/repo", pr_service=pr_service)

       # Detect changed project
       changed_projects = [
           AutoStartProject(name="my-project", change_type=ProjectChangeType.MODIFIED, spec_path="path")
       ]

       # Should identify as new project (ready for work)
       new_projects = auto_start_service.determine_new_projects(changed_projects)

       assert len(new_projects) == 1
   ```

**Expected outcome**: Integration tests verify correct interaction between services.

---

- [ ] Phase 5: Validation

**Goal**: Ensure the bug is fixed and no regressions were introduced.

**Tasks**:
1. Run all unit tests for AutoStartService:
   ```bash
   pytest tests/unit/services/composite/test_auto_start_service.py -v
   ```

2. Run all unit tests to ensure no regressions:
   ```bash
   pytest tests/unit/ -v
   ```

3. Run integration tests if they exist:
   ```bash
   pytest tests/integration/ -v
   ```

4. Manually verify the fix logic:
   - Review code changes in auto_start_service.py
   - Confirm both `determine_new_projects()` and `should_auto_trigger()` use `state="open"`
   - Verify log messages are updated to reflect new behavior

5. Consider testing manually with a real GitHub repo (optional):
   - Create a test project with 2 tasks
   - Complete both tasks (merge both PRs)
   - Add a 3rd task to spec.md and push
   - Verify auto-start triggers (creates PR for task 3)

**Success criteria**:
- All unit tests pass (including new test for completed projects)
- Integration tests pass (if they exist)
- Code correctly checks for `state="open"` instead of `state="all"`
- Log messages accurately describe the behavior
- No regressions in existing functionality

**Notes**:
- This fix does NOT require E2E tests - unit/integration tests are sufficient
- The bug is in the Service Layer, so tests should focus on that layer
- Manual testing is optional - automated tests provide sufficient confidence
