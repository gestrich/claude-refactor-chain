"""Unit tests for domain models"""

import pytest
from datetime import datetime

from claudestep.domain.models import (
    MarkdownFormatter,
    ReviewerCapacityResult,
    TeamMemberStats,
    ProjectStats,
    StatisticsReport,
)


class TestMarkdownFormatter:
    """Test suite for MarkdownFormatter functionality"""

    def test_bold_formatting_for_github(self):
        """Should format text as bold using GitHub markdown syntax"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.bold("important")

        # Assert
        assert result == "**important**"

    def test_bold_formatting_for_slack(self):
        """Should format text as bold using Slack mrkdwn syntax"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=True)

        # Act
        result = formatter.bold("important")

        # Assert
        assert result == "*important*"

    def test_italic_formatting(self):
        """Should format text as italic (same for both platforms)"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.italic("emphasis")

        # Assert
        assert result == "_emphasis_"

    def test_header_formatting_for_github(self):
        """Should format headers with hash marks for GitHub"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        h1 = formatter.header("Title", level=1)
        h2 = formatter.header("Subtitle", level=2)
        h3 = formatter.header("Section", level=3)

        # Assert
        assert h1 == "# Title"
        assert h2 == "## Subtitle"
        assert h3 == "### Section"

    def test_header_formatting_for_slack(self):
        """Should format headers as bold for Slack (no heading levels)"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=True)

        # Act
        h1 = formatter.header("Title", level=1)
        h2 = formatter.header("Subtitle", level=2)

        # Assert
        assert h1 == "*Title*"
        assert h2 == "*Subtitle*"

    def test_code_formatting(self):
        """Should format inline code with backticks"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.code("function_name")

        # Assert
        assert result == "`function_name`"

    def test_code_block_formatting_for_github(self):
        """Should format code blocks with language for GitHub"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.code_block("print('hello')", language="python")

        # Assert
        assert result == "```python\nprint('hello')\n```"

    def test_code_block_formatting_for_slack(self):
        """Should format code blocks without language for Slack"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=True)

        # Act
        result = formatter.code_block("print('hello')", language="python")

        # Assert
        assert result == "```print('hello')```"

    def test_link_formatting_for_github(self):
        """Should format links using GitHub markdown syntax"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.link("Click here", "https://example.com")

        # Assert
        assert result == "[Click here](https://example.com)"

    def test_link_formatting_for_slack(self):
        """Should format links using Slack mrkdwn syntax"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=True)

        # Act
        result = formatter.link("Click here", "https://example.com")

        # Assert
        assert result == "<https://example.com|Click here>"

    def test_list_item_formatting(self):
        """Should format list items with bullet"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.list_item("First item")

        # Assert
        assert result == "- First item"

    def test_list_item_with_custom_bullet(self):
        """Should support custom bullet characters"""
        # Arrange
        formatter = MarkdownFormatter(for_slack=False)

        # Act
        result = formatter.list_item("Numbered", bullet="1.")

        # Assert
        assert result == "1. Numbered"


class TestReviewerCapacityResult:
    """Test suite for ReviewerCapacityResult model"""

    def test_initialization(self):
        """Should initialize with empty state"""
        # Act
        result = ReviewerCapacityResult()

        # Assert
        assert result.reviewers_status == []
        assert result.selected_reviewer is None
        assert result.all_at_capacity is False

    def test_add_reviewer_with_capacity(self):
        """Should add reviewer status information"""
        # Arrange
        result = ReviewerCapacityResult()
        open_prs = [{"pr_number": 123, "task_index": 1, "task_description": "Task 1"}]

        # Act
        result.add_reviewer("alice", max_prs=2, open_prs=open_prs, has_capacity=True)

        # Assert
        assert len(result.reviewers_status) == 1
        assert result.reviewers_status[0]["username"] == "alice"
        assert result.reviewers_status[0]["max_prs"] == 2
        assert result.reviewers_status[0]["open_count"] == 1
        assert result.reviewers_status[0]["has_capacity"] is True

    def test_format_summary_with_available_reviewer(self):
        """Should format summary showing reviewer with capacity"""
        # Arrange
        result = ReviewerCapacityResult()
        result.add_reviewer("alice", max_prs=2, open_prs=[], has_capacity=True)
        result.selected_reviewer = "alice"

        # Act
        summary = result.format_summary()

        # Assert
        assert "## Reviewer Capacity Check" in summary
        assert "alice" in summary
        assert "✅" in summary
        assert "Available" in summary
        assert "Selected **alice**" in summary

    def test_format_summary_with_reviewer_at_capacity(self):
        """Should format summary showing reviewer at capacity"""
        # Arrange
        result = ReviewerCapacityResult()
        open_prs = [
            {"pr_number": 123, "task_index": 1, "task_description": "Task 1"},
            {"pr_number": 124, "task_index": 2, "task_description": "Task 2"},
        ]
        result.add_reviewer("bob", max_prs=2, open_prs=open_prs, has_capacity=False)
        result.all_at_capacity = True

        # Act
        summary = result.format_summary()

        # Assert
        assert "bob" in summary
        assert "❌" in summary
        assert "At capacity" in summary
        assert "PR #123" in summary
        assert "PR #124" in summary
        assert "All reviewers at capacity" in summary


class TestTeamMemberStats:
    """Test suite for TeamMemberStats model"""

    def test_initialization(self):
        """Should initialize with username and empty PR lists"""
        # Act
        stats = TeamMemberStats("alice")

        # Assert
        assert stats.username == "alice"
        assert stats.merged_prs == []
        assert stats.open_prs == []

    def test_merged_count_property(self):
        """Should count merged PRs correctly"""
        # Arrange
        stats = TeamMemberStats("alice")
        stats.merged_prs = [
            {"pr_number": 1, "title": "PR 1"},
            {"pr_number": 2, "title": "PR 2"},
        ]

        # Act
        count = stats.merged_count

        # Assert
        assert count == 2

    def test_open_count_property(self):
        """Should count open PRs correctly"""
        # Arrange
        stats = TeamMemberStats("alice")
        stats.open_prs = [{"pr_number": 3, "title": "PR 3"}]

        # Act
        count = stats.open_count

        # Assert
        assert count == 1

    def test_format_summary_with_activity(self):
        """Should format summary for active member"""
        # Arrange
        stats = TeamMemberStats("alice")
        stats.merged_prs = [{"pr_number": 1}]
        stats.open_prs = [{"pr_number": 2}]

        # Act
        summary = stats.format_summary(for_slack=False)

        # Assert
        assert "alice" in summary
        assert "✅" in summary
        assert "Merged: 1" in summary
        assert "Open: 1" in summary

    def test_format_summary_without_activity(self):
        """Should show inactive status for member with no PRs"""
        # Arrange
        stats = TeamMemberStats("bob")

        # Act
        summary = stats.format_summary(for_slack=False)

        # Assert
        assert "bob" in summary
        assert "💤" in summary
        assert "Merged: 0" in summary
        assert "Open: 0" in summary

    def test_format_table_row_with_rank(self):
        """Should format table row with medal for top 3"""
        # Arrange
        stats = TeamMemberStats("alice")
        stats.merged_prs = [{"pr_number": i} for i in range(5)]
        stats.open_prs = [{"pr_number": 10}]

        # Act
        row = stats.format_table_row(rank=1)

        # Assert
        assert "🥇" in row
        assert "alice" in row
        assert "5" in row  # merged count
        assert "1" in row  # open count

    def test_format_table_row_truncates_long_username(self):
        """Should truncate usernames longer than 15 characters"""
        # Arrange
        stats = TeamMemberStats("very-long-username-here")
        stats.merged_prs = []
        stats.open_prs = []

        # Act
        row = stats.format_table_row(rank=0)

        # Assert
        assert "very-long-usern" in row
        assert len("very-long-username-here"[:15]) == 15


class TestProjectStats:
    """Test suite for ProjectStats model"""

    def test_initialization(self):
        """Should initialize with project name and zero counts"""
        # Act
        stats = ProjectStats("my-project", "/path/to/spec.md")

        # Assert
        assert stats.project_name == "my-project"
        assert stats.spec_path == "/path/to/spec.md"
        assert stats.total_tasks == 0
        assert stats.completed_tasks == 0
        assert stats.in_progress_tasks == 0
        assert stats.pending_tasks == 0
        assert stats.total_cost_usd == 0.0

    def test_completion_percentage_with_tasks(self):
        """Should calculate completion percentage correctly"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 7

        # Act
        percentage = stats.completion_percentage

        # Assert
        assert percentage == 70.0

    def test_completion_percentage_with_no_tasks(self):
        """Should return 0% when there are no tasks"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 0
        stats.completed_tasks = 0

        # Act
        percentage = stats.completion_percentage

        # Assert
        assert percentage == 0.0

    def test_format_progress_bar_partial_completion(self):
        """Should format progress bar with partial completion"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 5

        # Act
        bar = stats.format_progress_bar(width=10)

        # Assert
        assert "█" in bar
        assert "░" in bar
        assert "50%" in bar

    def test_format_progress_bar_full_completion(self):
        """Should format progress bar with 100% completion"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 10

        # Act
        bar = stats.format_progress_bar(width=10)

        # Assert
        assert bar.count("█") == 10
        assert "100%" in bar

    def test_format_progress_bar_empty(self):
        """Should format progress bar with no tasks"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 0

        # Act
        bar = stats.format_progress_bar(width=10)

        # Assert
        assert bar.count("░") == 10
        assert "0%" in bar

    def test_format_summary_includes_progress_bar(self):
        """Should include progress bar in summary"""
        # Arrange
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 7
        stats.in_progress_tasks = 2
        stats.pending_tasks = 1

        # Act
        summary = stats.format_summary(for_slack=False)

        # Assert
        assert "my-project" in summary
        assert "█" in summary
        assert "7/10 complete" in summary
        assert "✅7" in summary
        assert "🔄2" in summary
        assert "⏸️1" in summary


class TestStatisticsReport:
    """Test suite for StatisticsReport aggregation"""

    def test_initialization(self):
        """Should initialize with empty statistics"""
        # Act
        report = StatisticsReport()

        # Assert
        assert report.team_stats == {}
        assert report.project_stats == {}
        assert report.generated_at is None

    def test_add_team_member(self):
        """Should add team member statistics"""
        # Arrange
        report = StatisticsReport()
        stats = TeamMemberStats("alice")

        # Act
        report.add_team_member(stats)

        # Assert
        assert "alice" in report.team_stats
        assert report.team_stats["alice"] == stats

    def test_add_project(self):
        """Should add project statistics"""
        # Arrange
        report = StatisticsReport()
        stats = ProjectStats("my-project", "/path/to/spec.md")

        # Act
        report.add_project(stats)

        # Assert
        assert "my-project" in report.project_stats
        assert report.project_stats["my-project"] == stats

    def test_format_leaderboard_with_activity(self):
        """Should format leaderboard with rankings"""
        # Arrange
        report = StatisticsReport()

        alice = TeamMemberStats("alice")
        alice.merged_prs = [{"pr_number": i} for i in range(5)]

        bob = TeamMemberStats("bob")
        bob.merged_prs = [{"pr_number": i} for i in range(3)]

        report.add_team_member(alice)
        report.add_team_member(bob)

        # Act
        leaderboard = report.format_leaderboard(for_slack=False)

        # Assert
        assert "🏆 Leaderboard" in leaderboard
        assert "🥇" in leaderboard  # First place
        assert "🥈" in leaderboard  # Second place
        assert "alice" in leaderboard
        assert "bob" in leaderboard

    def test_format_leaderboard_empty_with_no_activity(self):
        """Should return empty string when no members have activity"""
        # Arrange
        report = StatisticsReport()
        stats = TeamMemberStats("alice")  # No PRs
        report.add_team_member(stats)

        # Act
        leaderboard = report.format_leaderboard(for_slack=False)

        # Assert
        assert leaderboard == ""

    def test_to_json_exports_correctly(self):
        """Should export statistics as JSON"""
        # Arrange
        import json
        report = StatisticsReport()
        report.generated_at = datetime(2025, 1, 1, 12, 0, 0)

        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 7
        report.add_project(stats)

        alice = TeamMemberStats("alice")
        alice.merged_prs = [{"pr_number": 1}]
        report.add_team_member(alice)

        # Act
        json_output = report.to_json()
        data = json.loads(json_output)

        # Assert
        assert data["generated_at"] == "2025-01-01T12:00:00"
        assert "my-project" in data["projects"]
        assert data["projects"]["my-project"]["total_tasks"] == 10
        assert data["projects"]["my-project"]["completed_tasks"] == 7
        assert "alice" in data["team_members"]
        assert data["team_members"]["alice"]["merged_count"] == 1

    def test_format_for_pr_comment_single_project(self):
        """Should format brief summary for single project"""
        # Arrange
        report = StatisticsReport()
        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 5
        report.add_project(stats)

        # Act
        comment = report.format_for_pr_comment()

        # Assert
        assert "my-project" in comment
        assert "5/10" in comment

    def test_format_for_slack_includes_tables(self):
        """Should format complete report with tables for Slack"""
        # Arrange
        report = StatisticsReport()

        alice = TeamMemberStats("alice")
        alice.merged_prs = [{"pr_number": 1}]
        report.add_team_member(alice)

        stats = ProjectStats("my-project", "/path/to/spec.md")
        stats.total_tasks = 10
        stats.completed_tasks = 5
        report.add_project(stats)

        # Act
        slack_output = report.format_for_slack()

        # Assert
        assert "ClaudeStep Statistics Report" in slack_output
        assert "Leaderboard" in slack_output
        assert "Project Progress" in slack_output
        assert "```" in slack_output  # Code blocks for tables
