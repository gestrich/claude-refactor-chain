"""
Utility functions for extracting cost information from Claude Code execution files.

This module provides helper functions used by other commands (e.g., prepare_summary)
to extract cost data from Claude Code execution output files.
"""

from typing import Optional


def extract_cost_from_execution(data: dict) -> Optional[float]:
    """
    Extract total_cost_usd from Claude Code execution data.

    Args:
        data: Parsed JSON data from the execution file

    Returns:
        Cost in USD as float, or None if not found
    """
    # Try to get total_cost_usd from the top level
    if 'total_cost_usd' in data:
        try:
            return float(data['total_cost_usd'])
        except (ValueError, TypeError):
            pass

    # Try to get it from a nested structure if needed
    if 'usage' in data and 'total_cost_usd' in data['usage']:
        try:
            return float(data['usage']['total_cost_usd'])
        except (ValueError, TypeError):
            pass

    return None
