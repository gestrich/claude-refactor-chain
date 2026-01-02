"""Domain model for Claude Code execution cost breakdown."""

import json
import os
from dataclasses import dataclass, field
from typing import Self


@dataclass
class ModelUsage:
    """Usage data for a single model within a Claude Code execution."""

    model: str
    cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens for this model."""
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )

    @classmethod
    def from_dict(cls, model: str, data: dict) -> Self:
        """Parse model usage from execution file modelUsage entry.

        Args:
            model: Model name/identifier
            data: Dict with inputTokens, outputTokens, etc.

        Returns:
            ModelUsage instance

        Raises:
            TypeError: If data is not a dict
        """
        if not isinstance(data, dict):
            raise TypeError(f"Model usage data must be a dict, got {type(data).__name__}")

        return cls(
            model=model,
            cost=float(data.get('costUSD', 0) or 0),
            input_tokens=int(data.get('inputTokens', 0) or 0),
            output_tokens=int(data.get('outputTokens', 0) or 0),
            cache_read_tokens=int(data.get('cacheReadInputTokens', 0) or 0),
            cache_write_tokens=int(data.get('cacheCreationInputTokens', 0) or 0),
        )


@dataclass
class ExecutionUsage:
    """Usage data from a single Claude Code execution."""

    models: list[ModelUsage] = field(default_factory=list)
    # Top-level cost from execution file (may differ from sum of model costs)
    total_cost_usd: float = 0.0

    @property
    def cost(self) -> float:
        """Total cost (uses top-level total_cost_usd from file)."""
        return self.total_cost_usd

    @property
    def input_tokens(self) -> int:
        """Sum of input tokens across all models."""
        return sum(m.input_tokens for m in self.models)

    @property
    def output_tokens(self) -> int:
        """Sum of output tokens across all models."""
        return sum(m.output_tokens for m in self.models)

    @property
    def cache_read_tokens(self) -> int:
        """Sum of cache read tokens across all models."""
        return sum(m.cache_read_tokens for m in self.models)

    @property
    def cache_write_tokens(self) -> int:
        """Sum of cache write tokens across all models."""
        return sum(m.cache_write_tokens for m in self.models)

    @property
    def total_tokens(self) -> int:
        """Sum of all tokens across all models."""
        return sum(m.total_tokens for m in self.models)

    def __add__(self, other: Self) -> Self:
        """Combine two ExecutionUsage instances."""
        return ExecutionUsage(
            models=self.models + other.models,
            total_cost_usd=self.total_cost_usd + other.total_cost_usd,
        )

    @classmethod
    def from_execution_file(cls, execution_file: str) -> Self:
        """Extract usage data from a Claude Code execution file.

        Args:
            execution_file: Path to execution file

        Returns:
            ExecutionUsage with cost and per-model usage

        Raises:
            ValueError: If execution_file is empty/whitespace
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not execution_file or not execution_file.strip():
            raise ValueError("execution_file cannot be empty")

        if not os.path.exists(execution_file):
            raise FileNotFoundError(f"Execution file not found: {execution_file}")

        with open(execution_file, 'r') as f:
            data = json.load(f)

        # Handle list format (may have multiple executions)
        if isinstance(data, list):
            # Filter to only items that have cost information
            items_with_cost = [
                item for item in data
                if isinstance(item, dict) and 'total_cost_usd' in item
            ]

            if items_with_cost:
                data = items_with_cost[-1]
            elif data:
                data = data[-1]
            else:
                raise ValueError(f"Execution file contains empty list: {execution_file}")

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> Self:
        """Extract usage data from parsed JSON dict.

        Args:
            data: Parsed JSON data from the execution file

        Returns:
            ExecutionUsage with cost and per-model usage

        Raises:
            TypeError: If data is not a dict or modelUsage is not a dict
            ValueError: If total_cost_usd cannot be parsed as float
        """
        if not isinstance(data, dict):
            raise TypeError(f"Execution data must be a dict, got {type(data).__name__}")

        # Extract top-level cost
        total_cost = 0.0
        if 'total_cost_usd' in data:
            try:
                total_cost = float(data['total_cost_usd'])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid total_cost_usd value: {data['total_cost_usd']}") from e
        elif 'usage' in data and isinstance(data['usage'], dict) and 'total_cost_usd' in data['usage']:
            try:
                total_cost = float(data['usage']['total_cost_usd'])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid usage.total_cost_usd value: {data['usage']['total_cost_usd']}") from e

        # Extract per-model usage
        models = []
        model_usage = data.get('modelUsage', {})
        if model_usage:
            if not isinstance(model_usage, dict):
                raise TypeError(f"modelUsage must be a dict, got {type(model_usage).__name__}")
            for model_name, model_data in model_usage.items():
                models.append(ModelUsage.from_dict(model_name, model_data))

        return cls(models=models, total_cost_usd=total_cost)


@dataclass
class CostBreakdown:
    """Domain model for Claude Code execution cost breakdown."""

    main_cost: float
    summary_cost: float
    # Token counts (summed across all models in modelUsage)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_cost(self) -> float:
        """Calculate total cost."""
        return self.main_cost + self.summary_cost

    @classmethod
    def from_execution_files(
        cls,
        main_execution_file: str,
        summary_execution_file: str
    ) -> 'CostBreakdown':
        """Parse cost and token information from execution files.

        Args:
            main_execution_file: Path to main execution file
            summary_execution_file: Path to summary execution file

        Returns:
            CostBreakdown with costs and tokens extracted from files
        """
        main_usage = ExecutionUsage.from_execution_file(main_execution_file)
        summary_usage = ExecutionUsage.from_execution_file(summary_execution_file)
        total_usage = main_usage + summary_usage

        return cls(
            main_cost=main_usage.cost,
            summary_cost=summary_usage.cost,
            input_tokens=total_usage.input_tokens,
            output_tokens=total_usage.output_tokens,
            cache_read_tokens=total_usage.cache_read_tokens,
            cache_write_tokens=total_usage.cache_write_tokens,
        )

    @property
    def total_tokens(self) -> int:
        """Calculate total token count (all token types)."""
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )

    @staticmethod
    def _format_token_count(count: int) -> str:
        """Format token count with thousands separator."""
        return f"{count:,}"

    def format_for_github(self, repo: str, run_id: str) -> str:
        """Format cost breakdown as markdown table for GitHub PR comment.

        Args:
            repo: Repository name (owner/repo)
            run_id: Workflow run ID

        Returns:
            Formatted markdown string
        """
        workflow_url = f"https://github.com/{repo}/actions/runs/{run_id}"

        # Build token section only if we have token data
        token_section = ""
        if self.total_tokens > 0:
            token_section = f"""
### Token Usage

| Token Type | Count |
|------------|-------|
| Input | {self._format_token_count(self.input_tokens)} |
| Output | {self._format_token_count(self.output_tokens)} |
| Cache Read | {self._format_token_count(self.cache_read_tokens)} |
| Cache Write | {self._format_token_count(self.cache_write_tokens)} |
| **Total** | **{self._format_token_count(self.total_tokens)}** |
"""

        cost_section = f"""## 💰 Cost Breakdown

This PR was generated using Claude Code with the following costs:

| Component | Cost (USD) |
|-----------|------------|
| Main refactoring task | ${self.main_cost:.6f} |
| PR summary generation | ${self.summary_cost:.6f} |
| **Total** | **${self.total_cost:.6f}** |
{token_section}
---
*Cost tracking by ClaudeStep • [View workflow run]({workflow_url})*
"""
        return cost_section
