"""Tests for Slack Block Kit formatter"""

from datetime import datetime, timezone

import pytest

from claudechain.domain.formatters.slack_block_kit_formatter import (
    SlackBlockKitFormatter,
    header_block,
    context_block,
    section_block,
    section_fields_block,
    divider_block,
    _generate_progress_bar,
)


class TestBlockBuilderFunctions:
    """Tests for module-level block builder functions"""

    def test_header_block_structure(self):
        """Header block uses plain_text type as required by Slack"""
        result = header_block("Test Title")

        assert result["type"] == "header"
        assert result["text"]["type"] == "plain_text"
        assert result["text"]["text"] == "Test Title"
        assert result["text"]["emoji"] is True

    def test_header_block_truncates_long_text(self):
        """Header text is truncated to 150 characters"""
        long_text = "x" * 200
        result = header_block(long_text)

        assert len(result["text"]["text"]) == 150

    def test_context_block_structure(self):
        """Context block uses mrkdwn type"""
        result = context_block("Test context")

        assert result["type"] == "context"
        assert len(result["elements"]) == 1
        assert result["elements"][0]["type"] == "mrkdwn"
        assert result["elements"][0]["text"] == "Test context"

    def test_section_block_with_text_only(self):
        """Section block with just text"""
        result = section_block("*Bold text*")

        assert result["type"] == "section"
        assert result["text"]["type"] == "mrkdwn"
        assert result["text"]["text"] == "*Bold text*"
        assert "fields" not in result

    def test_section_block_with_fields(self):
        """Section block with text and fields"""
        result = section_block("Main text", fields=["Field 1", "Field 2"])

        assert result["type"] == "section"
        assert result["text"]["text"] == "Main text"
        assert len(result["fields"]) == 2
        assert result["fields"][0]["type"] == "mrkdwn"
        assert result["fields"][0]["text"] == "Field 1"

    def test_section_block_limits_fields_to_10(self):
        """Section fields are limited to 10 per Slack API requirements"""
        fields = [f"Field {i}" for i in range(15)]
        result = section_block("Text", fields=fields)

        assert len(result["fields"]) == 10

    def test_section_fields_block_structure(self):
        """Section fields block has no main text"""
        result = section_fields_block(["Field 1", "Field 2"])

        assert result["type"] == "section"
        assert "text" not in result
        assert len(result["fields"]) == 2

    def test_section_fields_block_limits_to_10(self):
        """Section fields block limited to 10 fields"""
        fields = [f"Field {i}" for i in range(15)]
        result = section_fields_block(fields)

        assert len(result["fields"]) == 10

    def test_divider_block_structure(self):
        """Divider block has correct type"""
        result = divider_block()

        assert result == {"type": "divider"}


class TestProgressBar:
    """Tests for progress bar generation"""

    def test_progress_bar_0_percent(self):
        """0% shows all empty blocks"""
        result = _generate_progress_bar(0)
        assert result == "░░░░░░░░░░ 0%"

    def test_progress_bar_50_percent(self):
        """50% shows half filled"""
        result = _generate_progress_bar(50)
        assert result == "█████░░░░░ 50%"

    def test_progress_bar_100_percent(self):
        """100% shows all filled"""
        result = _generate_progress_bar(100)
        assert result == "██████████ 100%"

    def test_progress_bar_small_percentage_shows_at_least_one(self):
        """Small non-zero percentages show at least one filled block"""
        result = _generate_progress_bar(5)
        assert result.startswith("█")
        assert "5%" in result

    def test_progress_bar_custom_width(self):
        """Custom width parameter works"""
        result = _generate_progress_bar(50, width=20)
        assert "██████████░░░░░░░░░░" in result


class TestSlackBlockKitFormatter:
    """Tests for SlackBlockKitFormatter class"""

    @pytest.fixture
    def formatter(self):
        """Fixture providing formatter instance"""
        return SlackBlockKitFormatter(repo="owner/repo")

    def test_build_message_structure(self, formatter):
        """Build message includes text and blocks"""
        blocks = [{"type": "divider"}]
        result = formatter.build_message(blocks, fallback_text="Test")

        assert result["text"] == "Test"
        assert result["blocks"] == blocks

    def test_format_header_blocks_includes_required_elements(self, formatter):
        """Header blocks include title, context, and divider"""
        test_date = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = formatter.format_header_blocks(
            title="Test Report",
            generated_at=test_date,
            branch="main"
        )

        assert len(result) == 3
        assert result[0]["type"] == "header"
        assert result[0]["text"]["text"] == "Test Report"
        assert result[1]["type"] == "context"
        assert "2024-01-15" in result[1]["elements"][0]["text"]
        assert "main" in result[1]["elements"][0]["text"]
        assert result[2]["type"] == "divider"

    def test_format_header_blocks_defaults_to_now(self, formatter):
        """Header uses current time when generated_at not provided"""
        result = formatter.format_header_blocks(title="Test")

        assert len(result) == 3
        assert result[1]["type"] == "context"


class TestProjectBlocks:
    """Tests for project formatting"""

    @pytest.fixture
    def formatter(self):
        return SlackBlockKitFormatter(repo="owner/repo")

    def test_project_shows_checkmark_when_complete(self, formatter):
        """100% complete projects show ✅"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=10,
            total=10,
            cost_usd=5.00
        )

        section_text = result[0]["text"]["text"]
        assert "✅" in section_text
        assert "*test-project*" in section_text

    def test_project_no_checkmark_when_incomplete(self, formatter):
        """Incomplete projects don't show ✅"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00
        )

        section_text = result[0]["text"]["text"]
        assert "✅" not in section_text

    def test_project_shows_progress_bar(self, formatter):
        """Project blocks include progress bar"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00
        )

        section_text = result[0]["text"]["text"]
        assert "█" in section_text
        assert "50%" in section_text

    def test_project_shows_stats_context(self, formatter):
        """Project blocks include merged count and cost"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=15.50
        )

        context_text = result[1]["elements"][0]["text"]
        assert "5/10 merged" in context_text
        assert "$15.50" in context_text

    def test_project_shows_open_prs_with_links(self, formatter):
        """Open PRs are shown as clickable links"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00,
            open_prs=[
                {"number": 42, "title": "Fix bug", "url": "https://github.com/owner/repo/pull/42", "age_days": 3}
            ]
        )

        # Should have section, context, PR section, divider
        assert len(result) == 4
        pr_section_text = result[2]["text"]["text"]
        assert "<https://github.com/owner/repo/pull/42|#42 Fix bug>" in pr_section_text
        assert "(3d)" in pr_section_text

    def test_project_shows_warning_for_stale_prs(self, formatter):
        """PRs older than 5 days show ⚠️"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00,
            open_prs=[
                {"number": 42, "title": "Old PR", "age_days": 7}
            ]
        )

        pr_section_text = result[2]["text"]["text"]
        assert "⚠️" in pr_section_text

    def test_project_no_warning_for_fresh_prs(self, formatter):
        """PRs under 5 days don't show ⚠️"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00,
            open_prs=[
                {"number": 42, "title": "Fresh PR", "age_days": 2}
            ]
        )

        pr_section_text = result[2]["text"]["text"]
        assert "⚠️" not in pr_section_text

    def test_project_builds_pr_url_from_repo(self, formatter):
        """PR URLs are built from repo when not provided"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00,
            open_prs=[
                {"number": 42, "title": "Test PR", "age_days": 1}
            ]
        )

        pr_section_text = result[2]["text"]["text"]
        assert "https://github.com/owner/repo/pull/42" in pr_section_text

    def test_project_ends_with_divider(self, formatter):
        """Each project block ends with a divider"""
        result = formatter.format_project_blocks(
            project_name="test-project",
            merged=5,
            total=10,
            cost_usd=5.00
        )

        assert result[-1]["type"] == "divider"


class TestLeaderboardBlocks:
    """Tests for leaderboard formatting"""

    @pytest.fixture
    def formatter(self):
        return SlackBlockKitFormatter(repo="owner/repo")

    def test_leaderboard_returns_empty_for_no_entries(self, formatter):
        """Empty entries returns empty list"""
        result = formatter.format_leaderboard_blocks([])
        assert result == []

    def test_leaderboard_shows_medals_for_top_3(self, formatter):
        """Top 3 entries get medal emojis"""
        entries = [
            {"username": "alice", "merged": 10},
            {"username": "bob", "merged": 8},
            {"username": "charlie", "merged": 6},
            {"username": "dave", "merged": 4},
        ]
        result = formatter.format_leaderboard_blocks(entries)

        # Find the fields section
        fields_block = result[1]
        fields_text = " ".join(f["text"] for f in fields_block["fields"])

        assert "🥇" in fields_text
        assert "🥈" in fields_text
        assert "🥉" in fields_text
        assert "4." in fields_text  # 4th place gets number

    def test_leaderboard_uses_section_fields(self, formatter):
        """Leaderboard uses 2-column section fields layout"""
        entries = [
            {"username": "alice", "merged": 10},
            {"username": "bob", "merged": 8},
        ]
        result = formatter.format_leaderboard_blocks(entries)

        assert len(result) == 2
        assert result[0]["type"] == "section"  # Header
        assert result[1]["type"] == "section"  # Fields
        assert "fields" in result[1]

    def test_leaderboard_limits_to_6_entries(self, formatter):
        """Leaderboard limited to 6 entries to stay under 10 fields"""
        entries = [{"username": f"user{i}", "merged": 10-i} for i in range(10)]
        result = formatter.format_leaderboard_blocks(entries)

        fields_block = result[1]
        assert len(fields_block["fields"]) == 6


class TestWarningsBlocks:
    """Tests for warnings/attention formatting"""

    @pytest.fixture
    def formatter(self):
        return SlackBlockKitFormatter(repo="owner/repo")

    def test_warnings_returns_empty_for_no_warnings(self, formatter):
        """Empty warnings returns empty list"""
        result = formatter.format_warnings_blocks([])
        assert result == []

    def test_warnings_shows_header_and_items(self, formatter):
        """Warnings include header and item list"""
        warnings = [
            {
                "project_name": "test-project",
                "items": ["#42 (7d, stale)", "#43 (orphaned)"]
            }
        ]
        result = formatter.format_warnings_blocks(warnings)

        assert len(result) == 2
        assert "⚠️ Needs Attention" in result[0]["text"]["text"]
        assert "test-project" in result[1]["text"]["text"]
        assert "#42" in result[1]["text"]["text"]
