"""Integration tests for the parse-event command"""

import json
from unittest.mock import Mock, patch

import pytest

from claudestep.cli.commands.parse_event import cmd_parse_event


class TestCmdParseEvent:
    """Test suite for cmd_parse_event functionality"""

    @pytest.fixture
    def mock_github_helper(self):
        """Fixture providing mocked GitHubActionsHelper"""
        mock = Mock()
        mock.write_output = Mock()
        mock.set_error = Mock()
        return mock

    @pytest.fixture
    def pull_request_merged_event(self):
        """Fixture providing a merged PR event with claudestep label"""
        return json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 42,
                "merged": True,
                "labels": [{"name": "claudestep"}, {"name": "enhancement"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-my-project-a1b2c3d4"}
            }
        })

    @pytest.fixture
    def pull_request_not_merged_event(self):
        """Fixture providing a closed but not merged PR event"""
        return json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 42,
                "merged": False,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-my-project-a1b2c3d4"}
            }
        })

    @pytest.fixture
    def pull_request_no_label_event(self):
        """Fixture providing a merged PR without claudestep label"""
        return json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 42,
                "merged": True,
                "labels": [{"name": "bug"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-my-project-a1b2c3d4"}
            }
        })

    @pytest.fixture
    def push_event(self):
        """Fixture providing a push event"""
        return json.dumps({
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456"
        })

    @pytest.fixture
    def workflow_dispatch_event(self):
        """Fixture providing a workflow_dispatch event"""
        return json.dumps({
            "ref": "refs/heads/main",
            "inputs": {
                "project_name": "my-refactor"
            }
        })

    # =============================================================================
    # Tests for pull_request events with project detection from changed files
    # =============================================================================

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_pull_request_merged_with_label_succeeds(
        self, mock_detect, mock_compare, mock_github_helper, pull_request_merged_event, capsys
    ):
        """Should process merged PR with claudestep label, detecting project from diff"""
        mock_compare.return_value = ["claude-step/my-project/spec.md", "README.md"]
        mock_detect.return_value = "my-project"

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_merged_event,
            project_name=None,
            default_base_branch="main",
            pr_label="claudestep",
            repo="owner/repo"
        )

        assert result == 0
        mock_compare.assert_called_once_with("owner/repo", "main", "claude-step-my-project-a1b2c3d4")
        mock_detect.assert_called_once()
        mock_github_helper.write_output.assert_any_call("skip", "false")
        mock_github_helper.write_output.assert_any_call("project_name", "my-project")
        mock_github_helper.write_output.assert_any_call("checkout_ref", "main")
        mock_github_helper.write_output.assert_any_call("base_branch", "main")
        mock_github_helper.write_output.assert_any_call("merged_pr_number", "42")

        captured = capsys.readouterr()
        assert "Event parsing complete" in captured.out

    def test_pull_request_not_merged_skips(
        self, mock_github_helper, pull_request_not_merged_event, capsys
    ):
        """Should skip PR that was closed but not merged"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_not_merged_event,
            project_name=None,
            default_base_branch="main",
            pr_label="claudestep"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call("skip_reason", "PR was closed but not merged")

        captured = capsys.readouterr()
        assert "Skipping" in captured.out

    def test_pull_request_missing_label_skips(
        self, mock_github_helper, pull_request_no_label_event, capsys
    ):
        """Should skip PR without required label"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_no_label_event,
            project_name=None,
            default_base_branch="main",
            pr_label="claudestep"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "PR does not have required label 'claudestep'"
        )

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_pull_request_custom_label_requirement(
        self, mock_detect, mock_compare, mock_github_helper, capsys
    ):
        """Should respect custom label requirement"""
        mock_compare.return_value = ["claude-step/proj/spec.md"]
        mock_detect.return_value = "proj"

        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 42,
                "merged": True,
                "labels": [{"name": "auto-refactor"}],
                "base": {"ref": "develop"},
                "head": {"ref": "claude-step-proj-12345678"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            project_name=None,
            default_base_branch="main",
            pr_label="auto-refactor",
            repo="owner/repo"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "false")
        mock_github_helper.write_output.assert_any_call("project_name", "proj")

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_pull_request_detects_project_from_diff(
        self, mock_detect, mock_compare, mock_github_helper, capsys
    ):
        """Should detect project name from changed files via compare API"""
        mock_compare.return_value = ["claude-step/complex-project-name/spec.md", "src/code.py"]
        mock_detect.return_value = "complex-project-name"

        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 123,
                "merged": True,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-complex-project-name-abcd1234"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            repo="owner/repo"
        )

        assert result == 0
        mock_compare.assert_called_once_with("owner/repo", "main", "claude-step-complex-project-name-abcd1234")
        mock_github_helper.write_output.assert_any_call("project_name", "complex-project-name")

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_pull_request_no_spec_changes_skips(
        self, mock_detect, mock_compare, mock_github_helper, capsys
    ):
        """Should skip if no spec.md files were changed"""
        mock_compare.return_value = ["src/code.py", "README.md"]
        mock_detect.return_value = None  # No spec.md found

        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 123,
                "merged": True,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "main"},
                "head": {"ref": "feature/some-feature"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            repo="owner/repo"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "No spec.md changes detected in push"
        )

    # =============================================================================
    # Tests for workflow_dispatch events
    # =============================================================================

    def test_workflow_dispatch_with_project_name_succeeds(
        self, mock_github_helper, workflow_dispatch_event, capsys
    ):
        """Should process workflow_dispatch with explicit project name"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="workflow_dispatch",
            event_json=workflow_dispatch_event,
            project_name="explicit-project",
            default_base_branch="main"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "false")
        mock_github_helper.write_output.assert_any_call("project_name", "explicit-project")
        mock_github_helper.write_output.assert_any_call("checkout_ref", "main")
        mock_github_helper.write_output.assert_any_call("base_branch", "main")

    def test_workflow_dispatch_without_project_name_skips(
        self, mock_github_helper, workflow_dispatch_event, capsys
    ):
        """Should skip workflow_dispatch without project name"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="workflow_dispatch",
            event_json=workflow_dispatch_event,
            project_name=None,
            default_base_branch="main"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "No project_name provided for workflow_dispatch event"
        )

    def test_workflow_dispatch_respects_custom_base_branch(
        self, mock_github_helper, capsys
    ):
        """Should use custom default base branch"""
        event = json.dumps({
            "ref": "refs/heads/develop",
            "inputs": {}
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="workflow_dispatch",
            event_json=event,
            project_name="my-project",
            default_base_branch="develop"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("checkout_ref", "develop")
        mock_github_helper.write_output.assert_any_call("base_branch", "develop")

    # =============================================================================
    # Tests for push events with project detection from changed files
    # =============================================================================

    def test_push_event_with_project_name_succeeds(
        self, mock_github_helper, push_event, capsys
    ):
        """Should process push event with project name override"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json=push_event,
            project_name="pushed-project",
            default_base_branch="main"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "false")
        mock_github_helper.write_output.assert_any_call("project_name", "pushed-project")
        mock_github_helper.write_output.assert_any_call("checkout_ref", "main")
        mock_github_helper.write_output.assert_any_call("base_branch", "main")

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_push_event_detects_project_from_spec_changes(
        self, mock_detect, mock_compare, mock_github_helper, push_event, capsys
    ):
        """Should detect project from spec.md changes in push event"""
        mock_compare.return_value = ["claude-step/my-project/spec.md", "README.md"]
        mock_detect.return_value = "my-project"

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json=push_event,
            project_name=None,
            repo="owner/repo"
        )

        assert result == 0
        mock_compare.assert_called_once_with("owner/repo", "abc123", "def456")
        mock_detect.assert_called_once()
        mock_github_helper.write_output.assert_any_call("skip", "false")
        mock_github_helper.write_output.assert_any_call("project_name", "my-project")

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_push_event_without_spec_changes_skips(
        self, mock_detect, mock_compare, mock_github_helper, push_event, capsys
    ):
        """Should skip push event when no spec.md files changed"""
        mock_compare.return_value = ["src/code.py", "README.md"]
        mock_detect.return_value = None  # No spec.md found

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json=push_event,
            project_name=None,
            repo="owner/repo"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "No spec.md changes detected in push"
        )

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_push_event_multiple_projects_skips(
        self, mock_detect, mock_compare, mock_github_helper, push_event, capsys
    ):
        """Should skip when multiple projects modified in single push"""
        mock_compare.return_value = [
            "claude-step/project-a/spec.md",
            "claude-step/project-b/spec.md"
        ]
        mock_detect.side_effect = ValueError(
            "Multiple projects modified in single push: ['project-a', 'project-b']. "
            "Push changes to one project at a time."
        )

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json=push_event,
            project_name=None,
            repo="owner/repo"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        # Check that the skip reason contains information about multiple projects
        skip_reason_call = [
            call for call in mock_github_helper.write_output.call_args_list
            if call[0][0] == "skip_reason"
        ][0]
        assert "Multiple projects modified" in skip_reason_call[0][1]

    def test_push_event_without_repo_skips(
        self, mock_github_helper, push_event, capsys
    ):
        """Should skip push event when repo is not provided (can't call API)"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json=push_event,
            project_name=None,
            repo=None  # No repo provided
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "No spec.md changes detected in push"
        )

    # =============================================================================
    # Tests for error handling
    # =============================================================================

    def test_invalid_json_returns_error(
        self, mock_github_helper, capsys
    ):
        """Should handle invalid JSON gracefully"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="push",
            event_json="not valid json",
            project_name="test"
        )

        assert result == 1
        mock_github_helper.set_error.assert_called_once()
        error_msg = mock_github_helper.set_error.call_args[0][0]
        assert "Event parsing failed" in error_msg

    def test_empty_event_json_handled(
        self, mock_github_helper, capsys
    ):
        """Should handle empty event JSON by skipping (missing ref)"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="workflow_dispatch",
            event_json="",
            project_name="test-project"
        )

        # Empty JSON means no ref can be determined, so it should skip
        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
        mock_github_helper.write_output.assert_any_call(
            "skip_reason", "Could not determine checkout ref: Workflow dispatch event missing ref"
        )

    # =============================================================================
    # Tests for output consistency
    # =============================================================================

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_outputs_all_required_fields_on_success(
        self, mock_detect, mock_compare, mock_github_helper, pull_request_merged_event
    ):
        """Should output all required fields on success"""
        mock_compare.return_value = ["claude-step/my-project/spec.md"]
        mock_detect.return_value = "my-project"

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_merged_event,
            repo="owner/repo"
        )

        assert result == 0

        # Collect all output calls
        output_calls = {
            call[0][0]: call[0][1]
            for call in mock_github_helper.write_output.call_args_list
        }

        # Verify all required outputs are present
        assert "skip" in output_calls
        assert "project_name" in output_calls
        assert "checkout_ref" in output_calls
        assert "base_branch" in output_calls

    def test_outputs_all_required_fields_on_skip(
        self, mock_github_helper, pull_request_not_merged_event
    ):
        """Should output skip fields when skipping"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_not_merged_event
        )

        assert result == 0

        # Collect all output calls
        output_calls = {
            call[0][0]: call[0][1]
            for call in mock_github_helper.write_output.call_args_list
        }

        # Verify skip outputs are present
        assert output_calls.get("skip") == "true"
        assert "skip_reason" in output_calls

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_console_output_includes_context(
        self, mock_detect, mock_compare, mock_github_helper, pull_request_merged_event, capsys
    ):
        """Should include helpful context in console output"""
        mock_compare.return_value = ["claude-step/my-project/spec.md"]
        mock_detect.return_value = "my-project"

        cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=pull_request_merged_event,
            pr_label="claudestep",
            repo="owner/repo"
        )

        captured = capsys.readouterr()
        assert "ClaudeStep Event Parsing" in captured.out
        assert "Event name: pull_request" in captured.out
        assert "PR number: 42" in captured.out


class TestCmdParseEventEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def mock_github_helper(self):
        """Fixture providing mocked GitHubActionsHelper"""
        mock = Mock()
        mock.write_output = Mock()
        mock.set_error = Mock()
        return mock

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_project_name_with_multiple_hyphens(
        self, mock_detect, mock_compare, mock_github_helper
    ):
        """Should handle project names with multiple hyphens"""
        mock_compare.return_value = ["claude-step/my-very-long-project-name/spec.md"]
        mock_detect.return_value = "my-very-long-project-name"

        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 1,
                "merged": True,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-my-very-long-project-name-12345678"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            repo="owner/repo"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call(
            "project_name", "my-very-long-project-name"
        )

    @patch("claudestep.cli.commands.parse_event.compare_commits")
    @patch("claudestep.cli.commands.parse_event.detect_project_from_diff")
    def test_different_base_branches(
        self, mock_detect, mock_compare, mock_github_helper
    ):
        """Should respect different base branches from event"""
        mock_compare.return_value = ["claude-step/test/spec.md"]
        mock_detect.return_value = "test"

        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 1,
                "merged": True,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "develop"},
                "head": {"ref": "claude-step-test-abcd1234"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            repo="owner/repo"
        )

        assert result == 0
        mock_compare.assert_called_once_with("owner/repo", "develop", "claude-step-test-abcd1234")
        mock_github_helper.write_output.assert_any_call("base_branch", "develop")
        mock_github_helper.write_output.assert_any_call("checkout_ref", "develop")

    def test_project_name_override_takes_precedence(self, mock_github_helper):
        """Should use explicit project_name over diff detection"""
        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 1,
                "merged": True,
                "labels": [{"name": "claudestep"}],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-branch-project-abcd1234"}
            }
        })

        # No mocking needed - project_name override should prevent API calls
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event,
            project_name="override-project"
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("project_name", "override-project")

    def test_empty_labels_list(self, mock_github_helper):
        """Should handle PR with no labels"""
        event = json.dumps({
            "action": "closed",
            "pull_request": {
                "number": 1,
                "merged": True,
                "labels": [],
                "base": {"ref": "main"},
                "head": {"ref": "claude-step-test-abcd1234"}
            }
        })

        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="pull_request",
            event_json=event
        )

        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")

    def test_unknown_event_type_with_project(self, mock_github_helper):
        """Should handle unknown event types gracefully"""
        result = cmd_parse_event(
            gh=mock_github_helper,
            event_name="unknown_event",
            event_json="{}",
            project_name="test"
        )

        # Should skip because no checkout ref can be determined
        assert result == 0
        mock_github_helper.write_output.assert_any_call("skip", "true")
