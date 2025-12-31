"""Deprecated: Import from claudestep.services.core instead."""
from claudestep.services.core.pr_service import (
    PRService as PROperationsService,
    list_pull_requests,
    list_open_pull_requests,
)

__all__ = ["PROperationsService", "list_pull_requests", "list_open_pull_requests"]
