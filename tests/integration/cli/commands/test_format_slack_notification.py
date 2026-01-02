"""
Tests for format_slack_notification.py - Slack notification formatting command
"""

from unittest.mock import Mock, patch

import pytest

from claudestep.cli.commands.format_slack_notification import cmd_format_slack_notification, format_pr_notification


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
            model_breakdown=[],
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
            model_breakdown=[],
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
            model_breakdown=[],
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
            model_breakdown=[],
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
            model_breakdown=[],
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
            model_breakdown=[],
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
            model_breakdown=[],
            repo="owner/repo"
        )

        # Assert
        assert "─────────────────────────────" in result

    def test_format_pr_notification_includes_model_breakdown(self):
        """Should include per-model breakdown when provided"""
        # Arrange
        model_breakdown = [
            {
                "model": "claude-3-haiku-20240307",
                "input_tokens": 1000,
                "output_tokens": 500,
                "cost": 0.01,
            }
        ]

        # Act
        result = format_pr_notification(
            pr_number="1",
            pr_url="https://example.com",
            project_name="test",
            task="test",
            main_cost=0.01,
            summary_cost=0.0,
            total_cost=0.01,
            model_breakdown=model_breakdown,
            repo="owner/repo"
        )

        # Assert
        assert "*📊 Per-Model Usage:*" in result
        assert "claude-3-haiku-20240307" in result
        assert "1,000" in result
        assert "500" in result


class TestCmdFormatSlackNotification:
    """Test suite for format_slack_notification command functionality"""

    @pytest.fixture
    def mock_gh_actions(self):
        """Fixture providing mocked GitHub Actions helper"""
        mock = Mock()
        mock.write_output = Mock()
        mock.set_error = Mock()
        return mock

    @pytest.fixture
    def default_params(self):
        """Fixture providing standard notification parameters"""
        return {
            "pr_number": "42",
            "pr_url": "https://github.com/owner/repo/pull/42",
            "project_name": "my-project",
            "task": "Refactor authentication system",
            "main_cost": "0.123456",
            "summary_cost": "0.045678",
            "model_breakdown_json": "",
            "repo": "owner/repo"
        }

    def test_cmd_format_slack_notification_generates_notification_successfully(self, mock_gh_actions, default_params):
        """Should generate Slack notification when all inputs are valid"""
        # Act
        result = cmd_format_slack_notification(gh=mock_gh_actions, **default_params)

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

    def test_cmd_format_slack_notification_includes_all_required_fields_in_message(self, mock_gh_actions, default_params):
        """Should include PR number, URL, project, task, and costs in message"""
        # Act
        cmd_format_slack_notification(gh=mock_gh_actions, **default_params)

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

    def test_cmd_format_slack_notification_calculates_total_cost_correctly(self, mock_gh_actions):
        """Should calculate total cost as sum of main and summary costs"""
        # Act
        cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="test",
            main_cost="0.123",
            summary_cost="0.456",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        assert "$0.123000" in message  # Main cost
        assert "$0.456000" in message  # Summary cost
        assert "$0.579000" in message  # Total (0.123 + 0.456)

    def test_cmd_format_slack_notification_skips_when_no_pr_number(self, mock_gh_actions):
        """Should skip notification and return success when pr_number is empty"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="test",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")
        mock_gh_actions.set_error.assert_not_called()

    def test_cmd_format_slack_notification_skips_when_no_pr_url(self, mock_gh_actions):
        """Should skip notification when pr_url is empty"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="",
            project_name="test",
            task="test",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_format_slack_notification_skips_when_pr_number_is_whitespace(self, mock_gh_actions):
        """Should skip notification when pr_number is whitespace only"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="   ",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="test",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_format_slack_notification_skips_when_pr_url_is_whitespace(self, mock_gh_actions):
        """Should skip notification when pr_url is whitespace only"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="   ",
            project_name="test",
            task="test",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_format_slack_notification_handles_invalid_cost_values(self, mock_gh_actions):
        """Should treat invalid cost values as zero and continue"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="test",
            main_cost="invalid",
            summary_cost="not-a-number",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "$0.000000" in message  # Should use 0.0 for invalid values

    def test_cmd_format_slack_notification_uses_default_zero_costs(self, mock_gh_actions):
        """Should use 0 for costs when cost strings are '0'"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="test",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "$0.000000" in message

    def test_cmd_format_slack_notification_strips_whitespace_from_inputs(self, mock_gh_actions):
        """Should strip whitespace from parameter values"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="  42  ",
            pr_url="  https://github.com/owner/repo/pull/42  ",
            project_name="  my-project  ",
            task="  test task  ",
            main_cost="  0.123  ",
            summary_cost="  0.456  ",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        # Verify trimmed values are used
        assert "#42>" in message  # PR number without spaces
        assert "$0.123000" in message
        assert "$0.456000" in message

    def test_cmd_format_slack_notification_handles_empty_optional_fields(self, mock_gh_actions):
        """Should handle empty optional fields gracefully"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="",
            task="",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo=""
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]

        # Should still contain basic structure
        assert "🎉 *New PR Created*" in message
        assert "#42" in message

    def test_cmd_format_slack_notification_handles_unexpected_exception(self, mock_gh_actions, default_params):
        """Should catch and report unexpected exceptions"""
        # Arrange
        with patch('claudestep.cli.commands.format_slack_notification.format_pr_notification') as mock_format:
            # Simulate unexpected error during formatting
            mock_format.side_effect = RuntimeError("Unexpected error")

            # Act
            result = cmd_format_slack_notification(gh=mock_gh_actions, **default_params)

        # Assert
        assert result == 1
        mock_gh_actions.set_error.assert_called_once()
        error_message = mock_gh_actions.set_error.call_args[0][0]
        assert "Error generating PR notification" in error_message
        assert "Unexpected error" in error_message
        mock_gh_actions.write_output.assert_called_once_with("has_pr", "false")

    def test_cmd_format_slack_notification_writes_has_pr_false_on_exception(self, mock_gh_actions, default_params):
        """Should write has_pr=false when exception occurs"""
        # Arrange
        with patch('claudestep.cli.commands.format_slack_notification.format_pr_notification') as mock_format:
            mock_format.side_effect = Exception("Test error")

            # Act
            result = cmd_format_slack_notification(gh=mock_gh_actions, **default_params)

        # Assert
        assert result == 1
        mock_gh_actions.write_output.assert_called_with("has_pr", "false")

    def test_cmd_format_slack_notification_handles_empty_task_description(self, mock_gh_actions):
        """Should handle empty task description gracefully"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="test",
            task="",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "*Task:*" in message  # Task field should still be present

    def test_cmd_format_slack_notification_handles_empty_project_name(self, mock_gh_actions):
        """Should handle empty project name gracefully"""
        # Act
        result = cmd_format_slack_notification(
            gh=mock_gh_actions,
            pr_number="42",
            pr_url="https://github.com/owner/repo/pull/42",
            project_name="",
            task="test task",
            main_cost="0",
            summary_cost="0",
            model_breakdown_json="",
            repo="owner/repo"
        )

        # Assert
        assert result == 0
        calls = mock_gh_actions.write_output.call_args_list
        slack_message_call = [c for c in calls if c[0][0] == "slack_message"]
        message = slack_message_call[0][0][1]
        assert "*Project:*" in message  # Project field should still be present

    def test_cmd_format_slack_notification_outputs_message_to_console(self, mock_gh_actions, default_params, capsys):
        """Should print notification message to console for debugging"""
        # Act
        cmd_format_slack_notification(gh=mock_gh_actions, **default_params)

        # Assert
        captured = capsys.readouterr()
        assert "=== Slack Notification Message ===" in captured.out
        assert "🎉 *New PR Created*" in captured.out
