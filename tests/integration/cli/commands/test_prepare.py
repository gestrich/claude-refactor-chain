"""Tests for prepare command - setup before Claude Code execution"""

import argparse
import json
import pytest
from unittest.mock import Mock, patch, mock_open

from claudestep.cli.commands.prepare import cmd_prepare
from claudestep.domain.exceptions import ConfigurationError, FileNotFoundError, GitError, GitHubAPIError

from tests.builders import ConfigBuilder, SpecFileBuilder


class TestCmdPrepare:
    """Test suite for cmd_prepare functionality"""

    @pytest.fixture
    def args(self):
        """Fixture providing command-line arguments"""
        args = argparse.Namespace()
        return args

    @pytest.fixture
    def mock_gh(self):
        """Fixture providing mocked GitHubActionsHelper"""
        return Mock()

    @pytest.fixture
    def mock_env(self):
        """Fixture providing standard environment variables"""
        return {
            "PROJECT_NAME": "my-project",
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_LABEL": "claudestep",
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"
        }

    @pytest.fixture
    def sample_config(self):
        """Fixture providing sample configuration using ConfigBuilder"""
        return (ConfigBuilder()
                .with_reviewer("alice", 2)
                .with_reviewer("bob", 2)
                .build())

    @pytest.fixture
    def sample_spec_content(self):
        """Fixture providing sample spec.md content using SpecFileBuilder"""
        return (SpecFileBuilder()
                .with_title("Project Spec")
                .add_section("## Tasks")
                .add_completed_task("Task 1")
                .add_tasks("Task 2", "Task 3")
                .build())

    def test_successful_preparation_workflow(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should complete full preparation workflow successfully"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True) as mock_exists:
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string") as mock_validate:
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists") as mock_label:
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command") as mock_git:
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content  # Returns content for both config and spec
                                                    MockProjectService.detect_project_paths.return_value = (
                                                        "claude-step/my-project/config.yml",
                                                        "claude-step/my-project/spec.md",
                                                        "claude-step/my-project/pr_template.md",
                                                        "claude-step/my-project"
                                                    )
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    mock_git.assert_called_once_with(["checkout", "-b", "claude-step-my-project-2"])
                                                    mock_gh.write_output.assert_any_call("has_capacity", "true")
                                                    mock_gh.write_output.assert_any_call("has_task", "true")
                                                    mock_gh.write_output.assert_any_call("reviewer", "alice")
                                                    mock_gh.write_output.assert_any_call("task_index", "2")
                                                    mock_gh.write_output.assert_any_call("branch_name", "claude-step-my-project-2")

    def test_preparation_with_merged_pr_number(
        self, args, mock_gh, sample_config, sample_spec_content
    ):
        """Should detect project from merged PR when MERGED_PR_NUMBER is provided"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "123",
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_LABEL": "claudestep"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                            with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                                with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                    with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                        with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                                with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                    with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                        # Setup mocks
                                                        mock_get_file.return_value = sample_spec_content
                                                        mock_project_service = MockProjectService.return_value
                                                        mock_project_service.detect_project_from_pr.return_value = "detected-project"
                                                        MockProjectService.detect_project_paths.return_value = (
                                                            "config.yml", "spec.md", "template.md", "path"
                                                        )
                                                        mock_load.return_value = sample_config
                                                        mock_reviewer_service = MockReviewerService.return_value
                                                        mock_reviewer_service.find_available_reviewer.return_value = (
                                                            "alice",
                                                            Mock(format_summary=Mock(return_value="Summary"))
                                                        )
                                                        mock_indices.return_value = set()
                                                        mock_task.return_value = (1, "Task 1")

                                                        # Act
                                                        result = cmd_prepare(args, mock_gh)

                                                        # Assert
                                                        assert result == 0
                                                        mock_project_service.detect_project_from_pr.assert_called_once_with("123")
                                                        mock_gh.write_output.assert_any_call("project_name", "detected-project")

    def test_preparation_fails_when_no_project_from_pr(self, args, mock_gh):
        """Should return error when merged PR has no matching project label"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "123",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                    # Setup mocks
                    mock_service = MockProjectService.return_value
                    mock_service.detect_project_from_pr.return_value = None

                    # Act
                    result = cmd_prepare(args, mock_gh)

                    # Assert
                    assert result == 1
                    mock_gh.set_error.assert_called_once()
                    assert "No refactor project found" in mock_gh.set_error.call_args[0][0]

    def test_preparation_fails_when_no_project_name(self, args, mock_gh):
        """Should return error when neither PROJECT_NAME nor MERGED_PR_NUMBER provided"""
        # Arrange
        with patch.dict("os.environ", {}, clear=True):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                # Act
                result = cmd_prepare(args, mock_gh)

                # Assert
                assert result == 1
                mock_gh.set_error.assert_called_once()
                assert "project_name must be provided" in mock_gh.set_error.call_args[0][0]

    def test_preparation_fails_when_no_reviewers(
        self, args, mock_gh, mock_env
    ):
        """Should return error when configuration has no reviewers"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            # Setup mocks
                            mock_get_file.return_value = "config content"
                            MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                            mock_load.return_value = {}  # No reviewers

                            # Act
                            result = cmd_prepare(args, mock_gh)

                            # Assert
                            assert result == 1
                            mock_gh.set_error.assert_called_once()
                            assert "Missing required field: reviewers" in mock_gh.set_error.call_args[0][0]

    def test_preparation_when_no_reviewer_capacity(
        self, args, mock_gh, mock_env, sample_config
    ):
        """Should exit gracefully when all reviewers at capacity"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        # Setup mocks
                                        mock_get_file.return_value = "config content"
                                        MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                        mock_load.return_value = sample_config
                                        mock_service = MockReviewerService.return_value
                                        mock_service.find_available_reviewer.return_value = (
                                            None,
                                            Mock(format_summary=Mock(return_value="All at capacity"))
                                        )

                                        # Act
                                        result = cmd_prepare(args, mock_gh)

                                        # Assert
                                        assert result == 0  # Not an error
                                        mock_gh.write_output.assert_any_call("has_capacity", "false")
                                        mock_gh.write_output.assert_any_call("reviewer", "")
                                        mock_gh.set_notice.assert_called_once()
                                        assert "All reviewers at capacity" in mock_gh.set_notice.call_args[0][0]

    def test_preparation_when_no_tasks_available(
        self, args, mock_gh, mock_env, sample_config
    ):
        """Should exit gracefully when no tasks available"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                # Setup mocks
                                                mock_get_file.return_value = "config content"
                                                MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                mock_load.return_value = sample_config
                                                mock_service = MockReviewerService.return_value
                                                mock_service.find_available_reviewer.return_value = (
                                                    "alice",
                                                    Mock(format_summary=Mock(return_value="Summary"))
                                                )
                                                mock_indices.return_value = set()
                                                mock_task.return_value = None  # No tasks

                                                # Act
                                                result = cmd_prepare(args, mock_gh)

                                                # Assert
                                                assert result == 0  # Not an error
                                                mock_gh.write_output.assert_any_call("has_task", "false")
                                                mock_gh.write_output.assert_any_call("all_tasks_done", "true")
                                                mock_gh.set_notice.assert_called_once()
                                                assert "No available tasks" in mock_gh.set_notice.call_args[0][0]

    def test_preparation_skips_in_progress_tasks(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should skip tasks that are already in progress"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = {2, 3}  # Tasks 2 and 3 in progress
                                                    mock_task.return_value = (4, "Task 4")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    # Verify in_progress_indices passed to find_next_available_task
                                                    mock_task.assert_called_once()
                                                    call_args = mock_task.call_args[0]
                                                    assert call_args[1] == {2, 3}

    def test_preparation_creates_branch_with_correct_format(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should create branch with format claude-step-{project}-{index}"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command") as mock_git:
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (5, "Task 5")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    mock_git.assert_called_once_with(["checkout", "-b", "claude-step-my-project-5"])

    def test_preparation_fails_when_branch_creation_fails(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should return error when git branch creation fails"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command") as mock_git:
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")
                                                    mock_git.side_effect = GitError("Branch already exists")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 1
                                                    mock_gh.set_error.assert_called_once()
                                                    assert "Failed to create branch" in mock_gh.set_error.call_args[0][0]

    def test_preparation_generates_claude_prompt(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should generate Claude prompt with task and spec content"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    # Find the claude_prompt output call
                                                    prompt_call = None
                                                    for call in mock_gh.write_output.call_args_list:
                                                        if call[0][0] == "claude_prompt":
                                                            prompt_call = call[0][1]
                                                            break

                                                    assert prompt_call is not None
                                                    assert "Task: Task 2" in prompt_call
                                                    assert "--- BEGIN spec.md ---" in prompt_call
                                                    assert sample_spec_content in prompt_call
                                                    assert "--- END spec.md ---" in prompt_call

    def test_preparation_writes_all_outputs(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should write all required output variables"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = (
                                                        "claude-step/my-project/config.yml",
                                                        "claude-step/my-project/spec.md",
                                                        "claude-step/my-project/pr_template.md",
                                                        "claude-step/my-project"
                                                    )
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (3, "Task 3")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0

                                                    # Verify all outputs were written
                                                    output_calls = {call[0][0]: call[0][1] for call in mock_gh.write_output.call_args_list}

                                                    assert output_calls["project_name"] == "my-project"
                                                    assert output_calls["project_path"] == "claude-step/my-project"
                                                    assert output_calls["config_path"] == "claude-step/my-project/config.yml"
                                                    assert output_calls["spec_path"] == "claude-step/my-project/spec.md"
                                                    assert output_calls["pr_template_path"] == "claude-step/my-project/pr_template.md"
                                                    assert output_calls["label"] == "claudestep"
                                                    assert output_calls["reviewers_json"] == json.dumps(sample_config["reviewers"])
                                                    assert output_calls["slack_webhook_url"] == "https://hooks.slack.com/test"
                                                    assert output_calls["task"] == "Task 3"
                                                    assert output_calls["task_index"] == "3"
                                                    assert output_calls["has_task"] == "true"
                                                    assert output_calls["all_tasks_done"] == "false"
                                                    assert output_calls["branch_name"] == "claude-step-my-project-3"
                                                    assert output_calls["has_capacity"] == "true"
                                                    assert output_calls["reviewer"] == "alice"

    def test_preparation_handles_file_not_found_error(
        self, args, mock_gh, mock_env
    ):
        """Should handle FileNotFoundError gracefully"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            # Setup mocks
                            mock_get_file.return_value = "config content"
                            MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                            mock_load.side_effect = FileNotFoundError("Config file not found")

                            # Act
                            result = cmd_prepare(args, mock_gh)

                            # Assert
                            assert result == 1
                            mock_gh.set_error.assert_called_once()
                            assert "Preparation failed" in mock_gh.set_error.call_args[0][0]

    def test_preparation_handles_configuration_error(
        self, args, mock_gh, mock_env
    ):
        """Should handle ConfigurationError gracefully"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            # Setup mocks
                            mock_get_file.return_value = "config content"
                            MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                            mock_load.side_effect = ConfigurationError("Invalid configuration")

                            # Act
                            result = cmd_prepare(args, mock_gh)

                            # Assert
                            assert result == 1
                            mock_gh.set_error.assert_called_once()
                            assert "Preparation failed" in mock_gh.set_error.call_args[0][0]

    def test_preparation_handles_github_api_error(
        self, args, mock_gh, mock_env, sample_config
    ):
        """Should handle GitHubAPIError gracefully"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists") as mock_label:
                                    # Setup mocks
                                    mock_get_file.return_value = "config content"
                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                    mock_load.return_value = sample_config
                                    mock_label.side_effect = GitHubAPIError("API rate limit exceeded")

                                    # Act
                                    result = cmd_prepare(args, mock_gh)

                                    # Assert
                                    assert result == 1
                                    mock_gh.set_error.assert_called_once()
                                    assert "Preparation failed" in mock_gh.set_error.call_args[0][0]

    def test_preparation_handles_unexpected_error(
        self, args, mock_gh, mock_env
    ):
        """Should handle unexpected errors gracefully"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                    # Setup mocks
                    MockProjectService.detect_project_paths.side_effect = RuntimeError("Unexpected error")

                    # Act
                    result = cmd_prepare(args, mock_gh)

                    # Assert
                    assert result == 1
                    mock_gh.set_error.assert_called_once()
                    assert "Unexpected error" in mock_gh.set_error.call_args[0][0]

    def test_preparation_ensures_label_exists(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should ensure GitHub label exists during preparation"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists") as mock_label:
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    mock_label.assert_called_once_with("claudestep", mock_gh)

    def test_preparation_validates_spec_format(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should validate spec.md format during preparation"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string") as mock_validate:
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = (
                                                        "claude-step/my-project/config.yml",
                                                        "claude-step/my-project/spec.md",
                                                        "claude-step/my-project/pr_template.md",
                                                        "claude-step/my-project"
                                                    )
                                                    mock_load.return_value = sample_config
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = (
                                                        "alice",
                                                        Mock(format_summary=Mock(return_value="Summary"))
                                                    )
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    mock_validate.assert_called_once_with(sample_spec_content, "claude-step/my-project/spec.md")

    def test_preparation_writes_step_summary(
        self, args, mock_gh, mock_env, sample_config, sample_spec_content
    ):
        """Should write step summary with reviewer capacity information"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                        with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                            with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                    with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                        with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                    # Setup mocks
                                                    mock_get_file.return_value = sample_spec_content
                                                    MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                    mock_load.return_value = sample_config
                                                    capacity_result = Mock()
                                                    capacity_result.format_summary.return_value = "Capacity Summary"
                                                    mock_service = MockReviewerService.return_value
                                                    mock_service.find_available_reviewer.return_value = ("alice", capacity_result)
                                                    mock_indices.return_value = set()
                                                    mock_task.return_value = (2, "Task 2")

                                                    # Act
                                                    result = cmd_prepare(args, mock_gh)

                                                    # Assert
                                                    assert result == 0
                                                    mock_gh.write_step_summary.assert_called_once_with("Capacity Summary")

    def test_preparation_fails_when_spec_files_missing_in_base_branch(
        self, args, mock_gh, mock_env
    ):
        """Should return error when spec files don't exist in base branch"""
        # Arrange
        with patch.dict("os.environ", mock_env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=False):
                with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                    # Setup mocks
                    MockProjectService.detect_project_paths.return_value = (
                        "claude-step/my-project/config.yml",
                        "claude-step/my-project/spec.md",
                        "claude-step/my-project/pr_template.md",
                        "claude-step/my-project"
                    )

                    # Act
                    result = cmd_prepare(args, mock_gh)

                    # Assert
                    assert result == 1
                    mock_gh.set_error.assert_called_once()
                    error_msg = mock_gh.set_error.call_args[0][0]
                    assert "Spec files not found in branch 'main'" in error_msg
                    assert "claude-step/my-project/spec.md" in error_msg
                    assert "claude-step/my-project/configuration.yml" in error_msg
                    assert "Please merge your spec files" in error_msg

    def test_preparation_updates_metadata_when_merged_pr_provided(
        self, args, mock_gh, sample_config, sample_spec_content
    ):
        """Should update metadata to mark PR as merged and task as completed"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "123",
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_LABEL": "claudestep"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                            with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                                with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                    with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                        with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                                with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                    with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                        with patch("claudestep.cli.commands.prepare.GitHubMetadataStore") as mock_store_class:
                                                            with patch("claudestep.cli.commands.prepare.MetadataService") as mock_service_class:
                                                                # Setup mocks
                                                                mock_get_file.return_value = sample_spec_content
                                                                mock_project_service = MockProjectService.return_value
                                                                mock_project_service.detect_project_from_pr.return_value = "test-project"
                                                                MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                                mock_load.return_value = sample_config
                                                                mock_service = MockReviewerService.return_value
                                                                mock_service.find_available_reviewer.return_value = (
                                                                    "alice",
                                                                    Mock(format_summary=Mock(return_value="Summary"))
                                                                )
                                                                mock_indices.return_value = set()
                                                                mock_task.return_value = (2, "Task 2")

                                                                # Mock metadata service
                                                                mock_metadata_service = Mock()
                                                                mock_service_class.return_value = mock_metadata_service

                                                                # Act
                                                                result = cmd_prepare(args, mock_gh)

                                                                # Assert
                                                                assert result == 0
                                                                mock_store_class.assert_called_once_with("owner/repo")
                                                                mock_service_class.assert_called_once()
                                                                mock_metadata_service.update_pr_state.assert_called_once_with(
                                                                    "test-project", 123, "merged"
                                                                )

    def test_preparation_continues_when_metadata_update_fails(
        self, args, mock_gh, sample_config, sample_spec_content
    ):
        """Should continue to prepare next task even if metadata update fails"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "123",
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_LABEL": "claudestep"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                            with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                                with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                    with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                        with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                                with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                    with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                        with patch("claudestep.cli.commands.prepare.GitHubMetadataStore") as mock_store_class:
                                                            with patch("claudestep.cli.commands.prepare.MetadataService") as mock_service_class:
                                                                # Setup mocks
                                                                mock_get_file.return_value = sample_spec_content
                                                                mock_project_service = MockProjectService.return_value
                                                                mock_project_service.detect_project_from_pr.return_value = "test-project"
                                                                MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                                mock_load.return_value = sample_config
                                                                mock_service = MockReviewerService.return_value
                                                                mock_service.find_available_reviewer.return_value = (
                                                                    "alice",
                                                                    Mock(format_summary=Mock(return_value="Summary"))
                                                                )
                                                                mock_indices.return_value = set()
                                                                mock_task.return_value = (2, "Task 2")

                                                                # Mock metadata service to raise exception
                                                                mock_metadata_service = Mock()
                                                                mock_metadata_service.update_pr_state.side_effect = Exception("Metadata update failed")
                                                                mock_service_class.return_value = mock_metadata_service

                                                                # Act
                                                                result = cmd_prepare(args, mock_gh)

                                                                # Assert - should still succeed
                                                                assert result == 0
                                                                mock_gh.write_output.assert_any_call("has_task", "true")
                                                                mock_gh.write_output.assert_any_call("task_index", "2")

    def test_preparation_calls_update_pr_state_with_correct_parameters(
        self, args, mock_gh, sample_config, sample_spec_content
    ):
        """Should call update_pr_state with project name, PR number, and 'merged' state"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "456",
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_LABEL": "claudestep"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                            with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                                with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                    with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                        with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                                with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                    with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                        with patch("claudestep.cli.commands.prepare.GitHubMetadataStore") as mock_store_class:
                                                            with patch("claudestep.cli.commands.prepare.MetadataService") as mock_service_class:
                                                                # Setup mocks
                                                                mock_get_file.return_value = sample_spec_content
                                                                mock_project_service = MockProjectService.return_value
                                                                mock_project_service.detect_project_from_pr.return_value = "my-special-project"
                                                                MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                                mock_load.return_value = sample_config
                                                                mock_service = MockReviewerService.return_value
                                                                mock_service.find_available_reviewer.return_value = (
                                                                    "bob",
                                                                    Mock(format_summary=Mock(return_value="Summary"))
                                                                )
                                                                mock_indices.return_value = set()
                                                                mock_task.return_value = (1, "Task 1")

                                                                # Mock metadata service
                                                                mock_metadata_service = Mock()
                                                                mock_service_class.return_value = mock_metadata_service

                                                                # Act
                                                                result = cmd_prepare(args, mock_gh)

                                                                # Assert
                                                                assert result == 0
                                                                mock_metadata_service.update_pr_state.assert_called_once_with(
                                                                    "my-special-project",
                                                                    456,
                                                                    "merged"
                                                                )

    def test_preparation_instantiates_metadata_store_with_repository(
        self, args, mock_gh, sample_config, sample_spec_content
    ):
        """Should instantiate GitHubMetadataStore with correct repository name"""
        # Arrange
        env = {
            "MERGED_PR_NUMBER": "789",
            "GITHUB_REPOSITORY": "myorg/myrepo",
            "PR_LABEL": "claudestep"
        }

        with patch.dict("os.environ", env):
            with patch("claudestep.cli.commands.prepare.file_exists_in_branch", return_value=True):
                with patch("claudestep.cli.commands.prepare.get_file_from_branch") as mock_get_file:
                    with patch("claudestep.cli.commands.prepare.ProjectDetectionService") as MockProjectService:
                            with patch("claudestep.cli.commands.prepare.load_config_from_string") as mock_load:
                                with patch("claudestep.cli.commands.prepare.validate_spec_format_from_string"):
                                    with patch("claudestep.cli.commands.prepare.ensure_label_exists"):
                                        with patch("claudestep.cli.commands.prepare.ReviewerManagementService") as MockReviewerService:
                                            with patch("claudestep.cli.commands.prepare.TaskManagementService.get_in_progress_task_indices") as mock_indices:
                                                with patch("claudestep.cli.commands.prepare.TaskManagementService.find_next_available_task") as mock_task:
                                                    with patch("claudestep.cli.commands.prepare.run_git_command"):
                                                        with patch("claudestep.cli.commands.prepare.GitHubMetadataStore") as mock_store_class:
                                                            with patch("claudestep.cli.commands.prepare.MetadataService") as mock_service_class:
                                                                # Setup mocks
                                                                mock_get_file.return_value = sample_spec_content
                                                                mock_project_service = MockProjectService.return_value
                                                                mock_project_service.detect_project_from_pr.return_value = "test-project"
                                                                MockProjectService.detect_project_paths.return_value = ("config.yml", "spec.md", "template.md", "path")
                                                                mock_load.return_value = sample_config
                                                                mock_service = MockReviewerService.return_value
                                                                mock_service.find_available_reviewer.return_value = (
                                                                    "alice",
                                                                    Mock(format_summary=Mock(return_value="Summary"))
                                                                )
                                                                mock_indices.return_value = set()
                                                                mock_task.return_value = (1, "Task 1")

                                                                # Mock metadata service
                                                                mock_metadata_service = Mock()
                                                                mock_service_class.return_value = mock_metadata_service

                                                                # Act
                                                                result = cmd_prepare(args, mock_gh)

                                                                # Assert
                                                                assert result == 0
                                                                mock_store_class.assert_called_once_with("myorg/myrepo")
