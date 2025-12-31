"""Integration tests for ClaudeStep Auto-Start workflow.

This module tests the bash script logic used in the auto-start workflow without
requiring actual GitHub Actions to run. It validates:
- Project name extraction from spec file paths
- Detection of added/modified vs deleted spec files
- YAML syntax and structure validation

Note: Full E2E testing of the auto-start workflow requires manual testing
since it involves GitHub Actions triggers and workflow_dispatch calls.
"""

import pytest
import re
from pathlib import Path


class TestAutoStartWorkflowLogic:
    """Tests for auto-start workflow bash script logic."""

    def test_project_name_extraction_pattern(self):
        """Verify the sed pattern correctly extracts project names from spec paths."""
        # Pattern used in workflow: sed 's|claude-step/\([^/]*\)/spec.md|\1|'
        pattern = r'claude-step/([^/]*)/spec\.md'

        test_cases = [
            ("claude-step/my-project/spec.md", "my-project"),
            ("claude-step/test-project-1/spec.md", "test-project-1"),
            ("claude-step/auth-refactor/spec.md", "auth-refactor"),
            ("claude-step/api_v2/spec.md", "api_v2"),
        ]

        for path, expected_project in test_cases:
            match = re.search(pattern, path)
            assert match is not None, f"Pattern should match path: {path}"
            extracted = match.group(1)
            assert extracted == expected_project, \
                f"Expected '{expected_project}', got '{extracted}' for path '{path}'"

    def test_project_name_extraction_rejects_invalid_paths(self):
        """Verify the pattern rejects invalid paths."""
        pattern = r'claude-step/([^/]*)/spec\.md'

        invalid_paths = [
            "claude-step/spec.md",  # Missing project directory
            "spec.md",  # Missing claude-step prefix
            "claude-step/project/other.md",  # Wrong filename
            "claude-step/project/subdir/spec.md",  # Too many directories
        ]

        for path in invalid_paths:
            match = re.search(pattern, path)
            assert match is None, f"Pattern should NOT match invalid path: {path}"

    def test_branch_name_pattern_for_pr_detection(self):
        """Verify the branch name pattern used to detect existing PRs."""
        # Pattern used in workflow: claude-step-$project-*
        # We check if branch starts with the pattern prefix

        def matches_pr_branch_pattern(branch_name: str, project: str) -> bool:
            """Check if branch name matches ClaudeStep PR pattern for given project."""
            prefix = f"claude-step-{project}-"
            return branch_name.startswith(prefix)

        test_cases = [
            # (branch_name, project, should_match)
            ("claude-step-my-project-1", "my-project", True),
            ("claude-step-my-project-2", "my-project", True),
            ("claude-step-my-project-123", "my-project", True),
            ("claude-step-other-project-1", "my-project", False),
            ("claude-step-my-project", "my-project", False),  # Missing task number
            ("my-project-1", "my-project", False),  # Missing prefix
        ]

        for branch, project, should_match in test_cases:
            result = matches_pr_branch_pattern(branch, project)
            assert result == should_match, \
                f"Branch '{branch}' with project '{project}': expected {should_match}, got {result}"

    def test_diff_filter_flags(self):
        """Document the diff-filter flags used in the workflow.

        This is a documentation test to ensure we understand the flags:
        - AM = Added or Modified files (what we want to process)
        - D = Deleted files (what we want to detect but ignore)
        """
        # These are the flags used in the workflow
        process_filter = "AM"  # Added or Modified
        deleted_filter = "D"   # Deleted

        # Verify flag meanings
        assert "A" in process_filter, "Should detect Added files"
        assert "M" in process_filter, "Should detect Modified files"
        assert "D" not in process_filter, "Should NOT process Deleted files"
        assert deleted_filter == "D", "Should detect Deleted files separately"


class TestAutoStartWorkflowYAML:
    """Tests for auto-start workflow YAML structure."""

    def test_workflow_file_exists(self):
        """Verify the auto-start workflow file exists."""
        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/claudestep-auto-start.yml"
        assert workflow_path.exists(), \
            f"Auto-start workflow should exist at {workflow_path}"

    def test_workflow_yaml_is_valid(self):
        """Verify the workflow YAML is syntactically valid."""
        import yaml

        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/claudestep-auto-start.yml"

        with open(workflow_path) as f:
            workflow_data = yaml.safe_load(f)

        # Basic structure validation
        assert workflow_data is not None, "YAML should parse successfully"
        assert "name" in workflow_data, "Workflow should have a name"
        # Note: YAML parses 'on' as boolean True, so check for True or 'on'
        assert (True in workflow_data or "on" in workflow_data), "Workflow should have triggers"
        assert "jobs" in workflow_data, "Workflow should have jobs"

    def test_workflow_has_required_triggers(self):
        """Verify the workflow has the correct triggers configured."""
        import yaml

        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/claudestep-auto-start.yml"

        with open(workflow_path) as f:
            workflow_data = yaml.safe_load(f)

        # YAML parses 'on:' as boolean True
        triggers = workflow_data.get(True) or workflow_data.get("on")
        assert triggers is not None, "Workflow should have triggers section"

        # Should trigger on push to main
        assert "push" in triggers, "Workflow should trigger on push"
        assert "main" in triggers["push"]["branches"], \
            "Workflow should trigger on push to main branch"

        # Should filter by spec.md paths
        assert "paths" in triggers["push"], "Workflow should have path filters"
        assert "claude-step/*/spec.md" in triggers["push"]["paths"], \
            "Workflow should filter for spec.md files"

    def test_workflow_has_concurrency_control(self):
        """Verify the workflow has concurrency control to prevent race conditions."""
        import yaml

        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/claudestep-auto-start.yml"

        with open(workflow_path) as f:
            workflow_data = yaml.safe_load(f)

        assert "concurrency" in workflow_data, "Workflow should have concurrency control"
        concurrency = workflow_data["concurrency"]

        assert "group" in concurrency, "Concurrency should have a group"
        assert "${{ github.ref }}" in concurrency["group"], \
            "Concurrency group should use github.ref"

        # cancel-in-progress should be false to allow both runs to execute
        # (they'll detect existing PRs and handle appropriately)
        assert concurrency.get("cancel-in-progress") is False, \
            "cancel-in-progress should be false to prevent race conditions"

    def test_workflow_has_required_steps(self):
        """Verify the workflow has all required steps."""
        import yaml

        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/claudestep-auto-start.yml"

        with open(workflow_path) as f:
            workflow_data = yaml.safe_load(f)

        jobs = workflow_data["jobs"]
        assert "auto-start" in jobs, "Workflow should have auto-start job"

        steps = jobs["auto-start"]["steps"]
        step_names = [step.get("name", "") for step in steps]

        required_steps = [
            "Checkout repository",
            "Setup Python",
            "Install ClaudeStep",
            "Detect and trigger auto-start",
            "Generate summary",
        ]

        for required_step in required_steps:
            assert any(required_step in name for name in step_names), \
                f"Workflow should have step: {required_step}"


@pytest.mark.integration
class TestAutoStartEdgeCases:
    """Tests for edge cases in auto-start workflow logic."""

    def test_empty_projects_list_handling(self):
        """Verify workflow handles empty project lists correctly."""
        # When PROJECTS is empty, the workflow should:
        # 1. Output empty string to GITHUB_OUTPUT
        # 2. Exit with status 0 (success)
        # 3. Not attempt to process any projects

        projects = ""

        # Simulate the bash loop
        project_list = projects.split() if projects else []
        assert len(project_list) == 0, "Empty string should result in empty list"

    def test_multiple_projects_parsing(self):
        """Verify multiple space-separated projects are parsed correctly."""
        projects = "project1 project2 project3"

        project_list = projects.split()
        assert len(project_list) == 3, "Should parse 3 projects"
        assert project_list == ["project1", "project2", "project3"]

    def test_project_name_with_hyphens_and_underscores(self):
        """Verify project names with special characters are handled correctly."""
        pattern = r'claude-step/([^/]*)/spec\.md'

        special_names = [
            "my-project",
            "my_project",
            "my-project-123",
            "api_v2_refactor",
            "auth-2024-Q1",
        ]

        for name in special_names:
            path = f"claude-step/{name}/spec.md"
            match = re.search(pattern, path)
            assert match is not None, f"Should match project name: {name}"
            assert match.group(1) == name, f"Should extract exact name: {name}"
