"""Deprecated: Import from claudestep.services.core instead."""
from claudestep.services.core.project_service import ProjectService as ProjectDetectionService
# Re-export infrastructure functions for backward compatibility with tests
from claudestep.infrastructure.github.operations import run_gh_command

__all__ = ["ProjectDetectionService", "run_gh_command"]
