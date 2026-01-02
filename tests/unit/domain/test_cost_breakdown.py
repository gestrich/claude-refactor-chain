"""Unit tests for CostBreakdown domain model"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from claudestep.domain.cost_breakdown import CostBreakdown, ExecutionUsage, ModelUsage


class TestCostBreakdownConstruction:
    """Test suite for CostBreakdown construction and basic properties"""

    def test_can_create_cost_breakdown(self):
        """Should be able to create CostBreakdown instance"""
        # Act
        breakdown = CostBreakdown(main_cost=1.5, summary_cost=0.5)

        # Assert
        assert breakdown.main_cost == 1.5
        assert breakdown.summary_cost == 0.5

    def test_total_cost_calculation(self):
        """Should calculate total cost correctly"""
        # Arrange
        breakdown = CostBreakdown(main_cost=1.234567, summary_cost=0.654321)

        # Act
        total = breakdown.total_cost

        # Assert
        assert total == pytest.approx(1.888888)

    def test_zero_costs(self):
        """Should handle zero costs"""
        # Arrange
        breakdown = CostBreakdown(main_cost=0.0, summary_cost=0.0)

        # Act
        total = breakdown.total_cost

        # Assert
        assert total == 0.0


class TestCostBreakdownFromExecutionFiles:
    """Test suite for CostBreakdown.from_execution_files() class method"""

    def test_from_execution_files_with_valid_files(self):
        """Should parse costs from valid execution files"""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "main.json"
            summary_file = Path(tmpdir) / "summary.json"

            main_file.write_text(json.dumps({"total_cost_usd": 1.5}))
            summary_file.write_text(json.dumps({"total_cost_usd": 0.5}))

            # Act
            breakdown = CostBreakdown.from_execution_files(
                str(main_file),
                str(summary_file)
            )

            # Assert
            assert breakdown.main_cost == 1.5
            assert breakdown.summary_cost == 0.5
            assert breakdown.total_cost == 2.0

    def test_from_execution_files_raises_on_missing_files(self):
        """Should raise FileNotFoundError when files don't exist"""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            CostBreakdown.from_execution_files(
                "/nonexistent/main.json",
                "/nonexistent/summary.json"
            )

    def test_from_execution_files_raises_on_empty_paths(self):
        """Should raise ValueError for empty file paths"""
        # Act & Assert
        with pytest.raises(ValueError, match="cannot be empty"):
            CostBreakdown.from_execution_files("", "")

    def test_from_execution_files_with_list_format(self):
        """Should handle execution files with list format (multiple executions)"""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "main.json"
            summary_file = Path(tmpdir) / "summary.json"

            # List with multiple entries - should use the last one with cost
            main_file.write_text(json.dumps([
                {"total_cost_usd": 0.5},
                {"total_cost_usd": 1.5},  # This should be used
            ]))
            summary_file.write_text(json.dumps([
                {"total_cost_usd": 0.3},
                {"total_cost_usd": 0.7},  # This should be used
            ]))

            # Act
            breakdown = CostBreakdown.from_execution_files(
                str(main_file),
                str(summary_file)
            )

            # Assert
            assert breakdown.main_cost == 1.5
            assert breakdown.summary_cost == 0.7


class TestModelUsage:
    """Test suite for ModelUsage dataclass"""

    def test_create_model_usage(self):
        """Should be able to create ModelUsage instance"""
        # Act
        usage = ModelUsage(
            model="claude-haiku",
            cost=0.5,
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=200,
            cache_write_tokens=30,
        )

        # Assert
        assert usage.model == "claude-haiku"
        assert usage.cost == 0.5
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_tokens == 200
        assert usage.cache_write_tokens == 30

    def test_model_usage_total_tokens(self):
        """Should calculate total tokens correctly"""
        # Arrange
        usage = ModelUsage(
            model="claude-haiku",
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=200,
            cache_write_tokens=30,
        )

        # Act
        total = usage.total_tokens

        # Assert
        assert total == 380

    def test_model_usage_from_dict(self):
        """Should parse model usage from dict"""
        # Arrange
        data = {
            "inputTokens": 4271,
            "outputTokens": 389,
            "cacheReadInputTokens": 90755,
            "cacheCreationInputTokens": 12299,
            "costUSD": 0.02158975,
        }

        # Act
        usage = ModelUsage.from_dict("claude-haiku-4-5", data)

        # Assert
        assert usage.model == "claude-haiku-4-5"
        assert usage.cost == 0.02158975
        assert usage.input_tokens == 4271
        assert usage.output_tokens == 389
        assert usage.cache_read_tokens == 90755
        assert usage.cache_write_tokens == 12299

    def test_model_usage_from_dict_handles_missing_fields(self):
        """Should handle missing fields in dict"""
        # Arrange
        data = {"inputTokens": 100}

        # Act
        usage = ModelUsage.from_dict("claude-haiku", data)

        # Assert
        assert usage.input_tokens == 100
        assert usage.output_tokens == 0
        assert usage.cache_read_tokens == 0
        assert usage.cache_write_tokens == 0
        assert usage.cost == 0.0

    def test_model_usage_from_dict_handles_null_values(self):
        """Should handle null/None values in dict"""
        # Arrange
        data = {
            "inputTokens": None,
            "outputTokens": 50,
            "costUSD": None,
        }

        # Act
        usage = ModelUsage.from_dict("claude-haiku", data)

        # Assert
        assert usage.input_tokens == 0
        assert usage.output_tokens == 50
        assert usage.cost == 0.0

    def test_model_usage_from_dict_raises_on_non_dict(self):
        """Should raise TypeError for non-dict data"""
        # Act & Assert
        with pytest.raises(TypeError, match="must be a dict"):
            ModelUsage.from_dict("claude-haiku", "not a dict")


class TestExecutionUsage:
    """Test suite for ExecutionUsage dataclass"""

    def test_create_execution_usage(self):
        """Should be able to create ExecutionUsage with models"""
        # Arrange
        models = [
            ModelUsage(model="haiku", input_tokens=100, output_tokens=50),
            ModelUsage(model="sonnet", input_tokens=200, output_tokens=100),
        ]

        # Act
        usage = ExecutionUsage(models=models, total_cost_usd=1.5)

        # Assert
        assert len(usage.models) == 2
        assert usage.total_cost_usd == 1.5
        assert usage.cost == 1.5

    def test_execution_usage_default_values(self):
        """Should default to empty models and zero cost"""
        # Act
        usage = ExecutionUsage()

        # Assert
        assert usage.models == []
        assert usage.total_cost_usd == 0.0
        assert usage.cost == 0.0
        assert usage.total_tokens == 0

    def test_execution_usage_aggregates_tokens(self):
        """Should sum tokens across all models"""
        # Arrange
        models = [
            ModelUsage(
                model="haiku",
                input_tokens=100,
                output_tokens=50,
                cache_read_tokens=200,
                cache_write_tokens=30,
            ),
            ModelUsage(
                model="sonnet",
                input_tokens=150,
                output_tokens=75,
                cache_read_tokens=100,
                cache_write_tokens=20,
            ),
        ]
        usage = ExecutionUsage(models=models)

        # Assert
        assert usage.input_tokens == 250
        assert usage.output_tokens == 125
        assert usage.cache_read_tokens == 300
        assert usage.cache_write_tokens == 50
        assert usage.total_tokens == 725

    def test_add_execution_usage(self):
        """Should combine two ExecutionUsage instances"""
        # Arrange
        usage1 = ExecutionUsage(
            models=[ModelUsage(model="haiku", input_tokens=100)],
            total_cost_usd=1.0,
        )
        usage2 = ExecutionUsage(
            models=[ModelUsage(model="sonnet", input_tokens=200)],
            total_cost_usd=0.5,
        )

        # Act
        result = usage1 + usage2

        # Assert
        assert result.total_cost_usd == 1.5
        assert len(result.models) == 2
        assert result.input_tokens == 300


class TestExecutionUsageFromFile:
    """Test suite for ExecutionUsage.from_execution_file() class method"""

    def test_from_valid_json(self):
        """Should extract usage from valid JSON file"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"total_cost_usd": 2.345678}, f)
            filepath = f.name

        try:
            # Act
            usage = ExecutionUsage.from_execution_file(filepath)

            # Assert
            assert usage.cost == 2.345678
            assert usage.models == []
        finally:
            os.unlink(filepath)

    def test_from_nested_usage_field(self):
        """Should extract cost from nested usage.total_cost_usd field"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"usage": {"total_cost_usd": 3.456789}}, f)
            filepath = f.name

        try:
            # Act
            usage = ExecutionUsage.from_execution_file(filepath)

            # Assert
            assert usage.cost == 3.456789
        finally:
            os.unlink(filepath)

    def test_from_empty_file_raises(self):
        """Should raise JSONDecodeError for empty file"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            # Act & Assert
            with pytest.raises(json.JSONDecodeError):
                ExecutionUsage.from_execution_file(filepath)
        finally:
            os.unlink(filepath)

    def test_from_invalid_json_raises(self):
        """Should raise JSONDecodeError for invalid JSON"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {]}")
            filepath = f.name

        try:
            # Act & Assert
            with pytest.raises(json.JSONDecodeError):
                ExecutionUsage.from_execution_file(filepath)
        finally:
            os.unlink(filepath)

    def test_from_nonexistent_file_raises(self):
        """Should raise FileNotFoundError for nonexistent file"""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ExecutionUsage.from_execution_file("/nonexistent/file.json")

    def test_from_whitespace_path_raises(self):
        """Should raise ValueError for whitespace-only path"""
        # Act & Assert
        with pytest.raises(ValueError, match="cannot be empty"):
            ExecutionUsage.from_execution_file("   ")

    def test_from_list_with_items_with_cost(self):
        """Should use last item with cost from list format"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"other_field": "value"},
                {"total_cost_usd": 1.0},
                {"other_field": "another"},
                {"total_cost_usd": 2.5},  # Last item with cost
            ], f)
            filepath = f.name

        try:
            # Act
            usage = ExecutionUsage.from_execution_file(filepath)

            # Assert
            assert usage.cost == 2.5
        finally:
            os.unlink(filepath)

    def test_from_list_without_cost_fields(self):
        """Should use last item when no items have total_cost_usd"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"other_field": "value1"},
                {"other_field": "value2"},
            ], f)
            filepath = f.name

        try:
            # Act
            usage = ExecutionUsage.from_execution_file(filepath)

            # Assert
            assert usage.cost == 0.0  # No cost field found
        finally:
            os.unlink(filepath)

    def test_from_empty_list_raises(self):
        """Should raise ValueError for empty list"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            filepath = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="empty list"):
                ExecutionUsage.from_execution_file(filepath)
        finally:
            os.unlink(filepath)

    def test_from_file_with_model_usage(self):
        """Should extract both cost and per-model usage from file"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "total_cost_usd": 1.5,
                "modelUsage": {
                    "claude-haiku": {
                        "inputTokens": 1000,
                        "outputTokens": 500,
                        "cacheReadInputTokens": 2000,
                        "cacheCreationInputTokens": 300,
                        "costUSD": 0.5,
                    },
                    "claude-sonnet": {
                        "inputTokens": 200,
                        "outputTokens": 100,
                        "costUSD": 1.0,
                    },
                },
            }, f)
            filepath = f.name

        try:
            # Act
            usage = ExecutionUsage.from_execution_file(filepath)

            # Assert
            assert usage.cost == 1.5
            assert len(usage.models) == 2
            assert usage.input_tokens == 1200
            assert usage.output_tokens == 600
            assert usage.cache_read_tokens == 2000
            assert usage.cache_write_tokens == 300
        finally:
            os.unlink(filepath)


class TestExecutionUsageFromDict:
    """Test suite for ExecutionUsage._from_dict() class method"""

    def test_from_dict_with_model_usage(self):
        """Should extract per-model usage from modelUsage section"""
        # Arrange
        data = {
            "total_cost_usd": 0.5,
            "modelUsage": {
                "claude-haiku-4-5-20251001": {
                    "inputTokens": 4271,
                    "outputTokens": 389,
                    "cacheReadInputTokens": 0,
                    "cacheCreationInputTokens": 12299,
                    "costUSD": 0.02,
                },
                "claude-3-haiku-20240307": {
                    "inputTokens": 15,
                    "outputTokens": 426,
                    "cacheReadInputTokens": 90755,
                    "cacheCreationInputTokens": 30605,
                    "costUSD": 0.15,
                },
            },
        }

        # Act
        usage = ExecutionUsage._from_dict(data)

        # Assert
        assert usage.cost == 0.5
        assert len(usage.models) == 2
        assert usage.input_tokens == 4271 + 15
        assert usage.output_tokens == 389 + 426
        assert usage.cache_read_tokens == 0 + 90755
        assert usage.cache_write_tokens == 12299 + 30605

    def test_from_dict_without_model_usage(self):
        """Should return empty models when modelUsage is missing"""
        # Arrange
        data = {"total_cost_usd": 0.5}

        # Act
        usage = ExecutionUsage._from_dict(data)

        # Assert
        assert usage.cost == 0.5
        assert usage.models == []
        assert usage.total_tokens == 0

    def test_from_dict_with_empty_model_usage(self):
        """Should return empty models when modelUsage is empty"""
        # Arrange
        data = {"total_cost_usd": 0.5, "modelUsage": {}}

        # Act
        usage = ExecutionUsage._from_dict(data)

        # Assert
        assert usage.cost == 0.5
        assert usage.models == []

    def test_from_dict_raises_on_invalid_model_usage_type(self):
        """Should raise TypeError when modelUsage is not a dict"""
        # Arrange
        data = {"total_cost_usd": 1.0, "modelUsage": "not a dict"}

        # Act & Assert
        with pytest.raises(TypeError, match="modelUsage must be a dict"):
            ExecutionUsage._from_dict(data)

    def test_from_dict_with_nested_usage_cost(self):
        """Should extract cost from nested usage.total_cost_usd"""
        # Arrange
        data = {"usage": {"total_cost_usd": 2.5}}

        # Act
        usage = ExecutionUsage._from_dict(data)

        # Assert
        assert usage.cost == 2.5

    def test_from_dict_prefers_top_level_cost(self):
        """Should prefer top-level total_cost_usd over nested"""
        # Arrange
        data = {
            "total_cost_usd": 3.0,
            "usage": {"total_cost_usd": 1.0}
        }

        # Act
        usage = ExecutionUsage._from_dict(data)

        # Assert
        assert usage.cost == 3.0

    def test_from_dict_raises_on_invalid_cost_value(self):
        """Should raise ValueError for non-numeric cost values"""
        # Arrange
        data = {"total_cost_usd": "not a number"}

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid total_cost_usd"):
            ExecutionUsage._from_dict(data)

    def test_from_dict_raises_on_none_cost_value(self):
        """Should raise ValueError when cost value is None"""
        # Arrange
        data = {"total_cost_usd": None}

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid total_cost_usd"):
            ExecutionUsage._from_dict(data)


class TestFormatForGitHub:
    """Test suite for CostBreakdown.format_for_github() method"""

    def test_format_creates_markdown_table(self):
        """Should create properly formatted markdown table"""
        # Arrange
        breakdown = CostBreakdown(main_cost=1.234567, summary_cost=0.543210)

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "## 💰 Cost Breakdown" in result
        assert "| Component | Cost (USD) |" in result
        assert "| Main refactoring task | $1.234567 |" in result
        assert "| PR summary generation | $0.543210 |" in result
        assert "| **Total** | **$1.777777** |" in result

    def test_format_includes_workflow_url(self):
        """Should include link to workflow run"""
        # Arrange
        breakdown = CostBreakdown(main_cost=1.0, summary_cost=0.5)

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "https://github.com/owner/repo/actions/runs/12345" in result
        assert "[View workflow run]" in result

    def test_format_with_zero_costs(self):
        """Should format zero costs correctly"""
        # Arrange
        breakdown = CostBreakdown(main_cost=0.0, summary_cost=0.0)

        # Act
        result = breakdown.format_for_github("owner/repo", "99999")

        # Assert
        assert "$0.000000" in result
        assert "**$0.000000**" in result  # Total

    def test_format_preserves_six_decimal_places(self):
        """Should format costs with 6 decimal places"""
        # Arrange
        breakdown = CostBreakdown(main_cost=1.23, summary_cost=0.45)

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "$1.230000" in result
        assert "$0.450000" in result
        assert "**$1.680000**" in result

    def test_format_includes_token_section_when_tokens_present(self):
        """Should include token usage section when tokens are available"""
        # Arrange
        breakdown = CostBreakdown(
            main_cost=1.0,
            summary_cost=0.5,
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=2000,
            cache_write_tokens=300,
        )

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "### Token Usage" in result
        assert "| Token Type | Count |" in result
        assert "| Input | 1,000 |" in result
        assert "| Output | 500 |" in result
        assert "| Cache Read | 2,000 |" in result
        assert "| Cache Write | 300 |" in result
        assert "| **Total** | **3,800** |" in result

    def test_format_excludes_token_section_when_no_tokens(self):
        """Should not include token usage section when all tokens are zero"""
        # Arrange
        breakdown = CostBreakdown(main_cost=1.0, summary_cost=0.5)

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "### Token Usage" not in result
        assert "| Token Type | Count |" not in result

    def test_format_with_large_token_counts(self):
        """Should format large token counts with thousands separators"""
        # Arrange
        breakdown = CostBreakdown(
            main_cost=1.0,
            summary_cost=0.5,
            input_tokens=1234567,
            output_tokens=987654,
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

        # Act
        result = breakdown.format_for_github("owner/repo", "12345")

        # Assert
        assert "| Input | 1,234,567 |" in result
        assert "| Output | 987,654 |" in result


class TestCostBreakdownWithTokens:
    """Test suite for CostBreakdown with token data from execution files"""

    def test_from_execution_files_extracts_tokens(self):
        """Should extract token data from execution files with modelUsage"""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "main.json"
            summary_file = Path(tmpdir) / "summary.json"

            main_file.write_text(json.dumps({
                "total_cost_usd": 1.5,
                "modelUsage": {
                    "claude-haiku": {
                        "inputTokens": 1000,
                        "outputTokens": 500,
                        "cacheReadInputTokens": 2000,
                        "cacheCreationInputTokens": 300,
                    },
                },
            }))
            summary_file.write_text(json.dumps({
                "total_cost_usd": 0.5,
                "modelUsage": {
                    "claude-haiku": {
                        "inputTokens": 200,
                        "outputTokens": 100,
                        "cacheReadInputTokens": 400,
                        "cacheCreationInputTokens": 50,
                    },
                },
            }))

            # Act
            breakdown = CostBreakdown.from_execution_files(
                str(main_file),
                str(summary_file)
            )

            # Assert
            assert breakdown.main_cost == 1.5
            assert breakdown.summary_cost == 0.5
            # Tokens should be summed from both files
            assert breakdown.input_tokens == 1000 + 200
            assert breakdown.output_tokens == 500 + 100
            assert breakdown.cache_read_tokens == 2000 + 400
            assert breakdown.cache_write_tokens == 300 + 50

    def test_from_execution_files_backward_compatible_without_model_usage(self):
        """Should work with execution files that don't have modelUsage (backward compat)"""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "main.json"
            summary_file = Path(tmpdir) / "summary.json"

            # Files without modelUsage (old format)
            main_file.write_text(json.dumps({"total_cost_usd": 1.5}))
            summary_file.write_text(json.dumps({"total_cost_usd": 0.5}))

            # Act
            breakdown = CostBreakdown.from_execution_files(
                str(main_file),
                str(summary_file)
            )

            # Assert
            assert breakdown.main_cost == 1.5
            assert breakdown.summary_cost == 0.5
            # Tokens should be zero
            assert breakdown.input_tokens == 0
            assert breakdown.output_tokens == 0
            assert breakdown.cache_read_tokens == 0
            assert breakdown.cache_write_tokens == 0

    def test_total_tokens_property(self):
        """Should calculate total tokens correctly"""
        # Arrange
        breakdown = CostBreakdown(
            main_cost=1.0,
            summary_cost=0.5,
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=200,
            cache_write_tokens=30,
        )

        # Act
        total = breakdown.total_tokens

        # Assert
        assert total == 100 + 50 + 200 + 30
