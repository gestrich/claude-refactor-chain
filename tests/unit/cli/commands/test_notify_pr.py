"""
Tests for notify_pr.py - PR notification command
"""

import os
from unittest.mock import Mock, patch

import pytest

from claudestep.cli.commands.notify_pr import cmd_notify_pr, format_pr_notification


class TestFormatPrNotification:
    """Test suite for PR notification formatting functionality"""

    def test_format_pr_notification_creates_slack_message(self):
        """Should format notification as Slack mrkdwn with proper structure"""
        # Arrange
        pr_number = "42"
        pr_url = "https://github.com/owner/repo/pull/42"
        project_name = "my-project"
        task = "Refactor authentication system"
        main_cost = 0.123456
        summary_cost = 0.045678
        total_cost = 0.169134
        repo = "owner/repo"

        # Act
        result = format_pr_notification(
            pr_number=pr_number,
            pr_url=pr_url,
            project_name=project_name,
            task=task,
            main_cost=main_cost,
            summary_cost=summary_cost,
            total_cost=total_cost,
            repo=repo
        )

        # Assert
        assert "🎉 *New PR Created*" in result
        assert f"*PR:* <{pr_url}|#{pr_number}>" in result
        assert f"*Project:* `{project_name}`" in result
        assert f"*Task:* {task}" in result

    def test_format_pr_notification_includes_cost_breakdown(self):
        """Should include detailed cost breakdown in code block"""
        # Arrange
        main_cost = 0.123456
        summary_cost = 0.045678
        total_cost = 0.169134

        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test task",
            main_cost=main_cost,
            summary_cost=summary_cost,
            total_cost=total_cost,
            repo="owner/repo"
        )

        # Assert
        assert "*💰 Cost Breakdown:*" in result
        assert "```" in result
        assert "Main task:      $0.123456" in result
        assert "PR summary:     $0.045678" in result
        assert "Total:          $0.169134" in result

    def test_format_pr_notification_uses_six_decimal_places(self):
        """Should display costs with 6 decimal places precision"""
        # Arrange
        main_cost = 0.000001
        summary_cost = 0.000002
        total_cost = 0.000003

        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test",
            main_cost=main_cost,
            summary_cost=summary_cost,
            total_cost=total_cost,
            repo="owner/repo"
        )

        # Assert
        assert "$0.000001" in result
        assert "$0.000002" in result
        assert "$0.000003" in result

    def test_format_pr_notification_handles_zero_costs(self):
        """Should format zero costs correctly"""
        # Arrange
        main_cost = 0.0
        summary_cost = 0.0
        total_cost = 0.0

        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test",
            main_cost=main_cost,
            summary_cost=summary_cost,
            total_cost=total_cost,
            repo="owner/repo"
        )

        # Assert
        assert "$0.000000" in result
        assert "Main task:      $0.000000" in result
        assert "PR summary:     $0.000000" in result
        assert "Total:          $0.000000" in result

    def test_format_pr_notification_handles_large_costs(self):
        """Should format large cost values correctly"""
        # Arrange
        main_cost = 123.456789
        summary_cost = 45.678901
        total_cost = 169.135690

        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test",
            main_cost=main_cost,
            summary_cost=summary_cost,
            total_cost=total_cost,
            repo="owner/repo"
        )

        # Assert
        assert "$123.456789" in result
        assert "$45.678901" in result
        assert "$169.135690" in result

    def test_format_pr_notification_formats_pr_link_as_slack_mrkdwn(self):
        """Should format PR link using Slack mrkdwn syntax"""
        # Arrange
        pr_number = "99"
        pr_url = "https://github.com/owner/repo/pull/99"

        # Act
        result = format_pr_notification(
            pr_number=pr_number,
            pr_url=pr_url,
            project_name="test",
            task="test",
            main_cost=0.0,
            summary_cost=0.0,
            total_cost=0.0,
            repo="owner/repo"
        )

        # Assert
        # Slack mrkdwn link format: <URL|Text>
        assert f"<{pr_url}|#{pr_number}>" in result

    def test_format_pr_notification_includes_separator_line(self):
        """Should include visual separator in cost breakdown"""
        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test",
            main_cost=1.0,
            summary_cost=2.0,
            total_cost=3.0,
            repo="owner/repo"
        )

        # Assert
        assert "─────────────────────────────" in result


class TestCmdNotifyPr:
    """Test suite for notify_pr command functionality"""

    @pytest.fixture
    def mock_gh_actions(self):
        """Fixture providing mocked GitHub Actions helper"""
        mock = Mock()
        mock.write_output = Mock()
        mock.set_error = Mock()
        return mock

    @pytest.fixture
    def notification_env_vars(self):
        """Fixture providing standard notification environment variables"""
        return {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "my-project",
            "TASK": "Refactor authentication system",
            "MAIN_COST": "0.123456",
            "SUMMARY_COST": "0.045678",
            "GITHUB_REPOSITORY": "owner/repo"
        }

    def test_cmd_notify_pr_generates_notification_successfully(self, mock_gh_actions, notification_env_vars):
        """Should generate Slack notification when all inputs are valid"""
        # Arrange
        with patch.dict(os.environ, notification_env_vars, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        assert mock_gh_actions.write_output.call_count == 2
        mock_gh_actions.write_output.assert_any_call("has_pr", "true")

        # Verify slack_message was written
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        assert len(slack_message_call) == 1
        message = slack_message_call[0][0][1]
        assert "🎉 *New PR Created*" in message
        assert "my-project" in message

    def test_cmd_notify_pr_includes_all_required_fields_in_message(self, mock_gh_actions, notification_env_vars):
        """Should include PR number, URL, project, task, and costs in message"""
        # Arrange
        with patch.dict(os.environ, notification_env_vars, clear=True):
            # Act
            cmd_notify_pr(None, mock_gh_actions)

        # Assert
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        assert "#42" in message
        assert "https://github.com/owner/repo/pull/42" in message
        assert "my-project" in message
        assert "Refactor authentication system" in message
        assert "$0.123456" in message
        assert "$0.045678" in message

    def test_cmd_notify_pr_calculates_total_cost_correctly(self, mock_gh_actions):
        """Should calculate total cost as sum of main and summary costs"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "MAIN_COST": "0.123",
            "SUMMARY_COST": "0.456",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            cmd_notify_pr(None, mock_gh_actions)

        # Assert
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        assert "$0.123000" in message  # Main cost
        assert "$0.456000" in message  # Summary cost
        assert "$0.579000" in message  # Total (0.123 + 0.456)

    def test_cmd_notify_pr_skips_when_no_pr_number(self, mock_gh_actions):
        """Should skip notification and return success when PR_NUMBER is not set"""
        # Arrange
        env = {
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")
        mock_gh_actions.set_error.assert_not_called()

    def test_cmd_notify_pr_skips_when_no_pr_url(self, mock_gh_actions):
        """Should skip notification when PR_URL is not set"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_notify_pr_skips_when_pr_number_is_whitespace(self, mock_gh_actions):
        """Should skip notification when PR_NUMBER is whitespace only"""
        # Arrange
        env = {
            "PR_NUMBER": "   ",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_notify_pr_skips_when_pr_url_is_whitespace(self, mock_gh_actions):
        """Should skip notification when PR_URL is whitespace only"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "   ",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_notify_pr_handles_invalid_cost_values(self, mock_gh_actions):
        """Should treat invalid cost values as zero and continue"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "MAIN_COST": "invalid",
            "SUMMARY_COST": "not-a-number",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "$0.000000" in message  # Should use 0.0 for invalid values

    def test_cmd_notify_pr_uses_default_zero_costs_when_missing(self, mock_gh_actions):
        """Should use 0 for costs when environment variables are not set"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "test",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "$0.000000" in message

    def test_cmd_notify_pr_strips_whitespace_from_inputs(self, mock_gh_actions):
        """Should strip whitespace from environment variable values"""
        # Arrange
        env = {
            "PR_NUMBER": "  42  ",
            "PR_URL": "  https://github.com/owner/repo/pull/42  ",
            "PROJECT_NAME": "  my-project  ",
            "TASK": "  test task  ",
            "MAIN_COST": "  0.123  ",
            "SUMMARY_COST": "  0.456  ",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        # Verify trimmed values are used
        assert "#42>" in message  # PR number without spaces
        assert "$0.123000" in message
        assert "$0.456000" in message

    def test_cmd_notify_pr_handles_missing_optional_fields(self, mock_gh_actions):
        """Should handle missing optional fields gracefully"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            # PROJECT_NAME, TASK, MAIN_COST, SUMMARY_COST, GITHUB_REPOSITORY all missing
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        # Should still contain basic structure
        assert "🎉 *New PR Created*" in message
        assert "#42" in message

    def test_cmd_notify_pr_handles_unexpected_exception(self, mock_gh_actions, notification_env_vars):
        """Should catch and report unexpected exceptions"""
        # Arrange
        with patch.dict(os.environ, notification_env_vars, clear=True):
            with patch('claudestep.cli.commands.notify_pr.format_pr_notification') as mock_format:
                # Simulate unexpected error during formatting
                mock_format.side_effect = RuntimeError("Unexpected error")

                # Act
                result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 1
        mock_gh_actions.set_error.assert_called_once()
        error_message = mock_gh_actions.set_error.call_args[0][0]
        assert "Error generating PR notification" in error_message
        assert "Unexpected error" in error_message
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_notify_pr_writes_has_pr_false_on_exception(self, mock_gh_actions, notification_env_vars):
        """Should write has_pr=false when exception occurs"""
        # Arrange
        with patch.dict(os.environ, notification_env_vars, clear=True):
            with patch('claudestep.cli.commands.notify_pr.format_pr_notification') as mock_format:
                mock_format.side_effect = Exception("Test error")

                # Act
                result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 1
        mock_gh_actions.write_output.assert_called_with("has_pr", "false")

    def test_cmd_notify_pr_handles_empty_task_description(self, mock_gh_actions):
        """Should handle empty task description gracefully"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "test",
            "TASK": "",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "*Task:*" in message  # Task field should still be present

    def test_cmd_notify_pr_handles_empty_project_name(self, mock_gh_actions):
        """Should handle empty project name gracefully"""
        # Arrange
        env = {
            "PR_NUMBER": "42",
            "PR_URL": "https://github.com/owner/repo/pull/42",
            "PROJECT_NAME": "",
            "TASK": "test task",
            "GITHUB_REPOSITORY": "owner/repo"
        }

        with patch.dict(os.environ, env, clear=True):
            # Act
            result = cmd_notify_pr(None, mock_gh_actions)

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "*Project:*" in message  # Project field should still be present

    def test_cmd_notify_pr_outputs_message_to_console(self, mock_gh_actions, notification_env_vars, capsys):
        """Should print notification message to console for debugging"""
        # Arrange
        with patch.dict(os.environ, notification_env_vars, clear=True):
            # Act
            cmd_notify_pr(None, mock_gh_actions)

        # Assert
        captured = capsys.readouterr()
        assert "=== Slack Notification Message ===" in captured.out
        assert "🎉 *New PR Created*" in captured.out
