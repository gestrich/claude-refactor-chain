"""Unit tests for hybrid metadata domain models

Tests Task, PullRequest, AIOperation, and HybridProjectMetadata models
from src/claudestep/domain/models.py
"""

import pytest
from datetime import datetime, timezone
from claudestep.domain.models import (
    Task,
    TaskStatus,
    PullRequest,
    AIOperation,
    HybridProjectMetadata,
)


class TestTask:
    """Tests for Task model"""

    def test_task_creation_with_pending_status(self):
        """Should create task with pending status"""
        # Arrange & Act
        task = Task(
            index=1,
            description="Implement authentication",
            status=TaskStatus.PENDING
        )

        # Assert
        assert task.index == 1
        assert task.description == "Implement authentication"
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict_serialization(self):
        """Should serialize task to dictionary correctly"""
        # Arrange
        task = Task(
            index=2,
            description="Add unit tests",
            status=TaskStatus.IN_PROGRESS
        )

        # Act
        result = task.to_dict()

        # Assert
        assert result == {
            "index": 2,
            "description": "Add unit tests",
            "status": "in_progress"
        }

    def test_task_from_dict_deserialization(self):
        """Should deserialize task from dictionary correctly"""
        # Arrange
        data = {
            "index": 3,
            "description": "Update documentation",
            "status": "completed"
        }

        # Act
        task = Task.from_dict(data)

        # Assert
        assert task.index == 3
        assert task.description == "Update documentation"
        assert task.status == TaskStatus.COMPLETED

    def test_task_from_dict_defaults_to_pending(self):
        """Should default to pending status when not provided"""
        # Arrange
        data = {
            "index": 1,
            "description": "New task"
        }

        # Act
        task = Task.from_dict(data)

        # Assert
        assert task.status == TaskStatus.PENDING


class TestAIOperation:
    """Tests for AIOperation model"""

    def test_ai_operation_creation(self):
        """Should create AI operation with all fields"""
        # Arrange & Act
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        operation = AIOperation(
            type="PRCreation",
            model="claude-sonnet-4",
            cost_usd=0.15,
            created_at=created_at,
            workflow_run_id=123456,
            tokens_input=5000,
            tokens_output=2000,
            duration_seconds=45.5
        )

        # Assert
        assert operation.type == "PRCreation"
        assert operation.model == "claude-sonnet-4"
        assert operation.cost_usd == 0.15
        assert operation.created_at == created_at
        assert operation.workflow_run_id == 123456
        assert operation.tokens_input == 5000
        assert operation.tokens_output == 2000
        assert operation.duration_seconds == 45.5

    def test_ai_operation_to_dict_serialization(self):
        """Should serialize AI operation to dictionary correctly"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        operation = AIOperation(
            type="PRCreation",
            model="claude-sonnet-4",
            cost_usd=0.15,
            created_at=created_at,
            workflow_run_id=123456,
            tokens_input=5000,
            tokens_output=2000,
            duration_seconds=45.5
        )

        # Act
        result = operation.to_dict()

        # Assert
        assert result["type"] == "PRCreation"
        assert result["model"] == "claude-sonnet-4"
        assert result["cost_usd"] == 0.15
        assert result["created_at"] == created_at.isoformat()
        assert result["workflow_run_id"] == 123456
        assert result["tokens_input"] == 5000
        assert result["tokens_output"] == 2000
        assert result["duration_seconds"] == 45.5

    def test_ai_operation_from_dict_deserialization(self):
        """Should deserialize AI operation from dictionary correctly"""
        # Arrange
        data = {
            "type": "PRRefinement",
            "model": "claude-opus-4",
            "cost_usd": 0.25,
            "created_at": "2025-12-29T14:30:00+00:00",
            "workflow_run_id": 789012,
            "tokens_input": 8000,
            "tokens_output": 3000,
            "duration_seconds": 60.2
        }

        # Act
        operation = AIOperation.from_dict(data)

        # Assert
        assert operation.type == "PRRefinement"
        assert operation.model == "claude-opus-4"
        assert operation.cost_usd == 0.25
        assert operation.workflow_run_id == 789012
        assert operation.tokens_input == 8000
        assert operation.tokens_output == 3000
        assert operation.duration_seconds == 60.2

    def test_ai_operation_from_dict_with_z_timestamp(self):
        """Should handle timestamp ending with Z instead of +00:00"""
        # Arrange
        data = {
            "type": "PRCreation",
            "model": "claude-sonnet-4",
            "cost_usd": 0.10,
            "created_at": "2025-12-29T10:00:00Z",
            "workflow_run_id": 123456
        }

        # Act
        operation = AIOperation.from_dict(data)

        # Assert
        assert operation.created_at.tzinfo is not None

    def test_ai_operation_from_dict_defaults_optional_fields(self):
        """Should use default values for optional fields"""
        # Arrange
        data = {
            "type": "PRCreation",
            "model": "claude-sonnet-4",
            "cost_usd": 0.10,
            "created_at": "2025-12-29T10:00:00Z",
            "workflow_run_id": 123456
        }

        # Act
        operation = AIOperation.from_dict(data)

        # Assert
        assert operation.tokens_input == 0
        assert operation.tokens_output == 0
        assert operation.duration_seconds == 0.0


class TestPullRequest:
    """Tests for PullRequest model"""

    def test_pull_request_creation(self):
        """Should create pull request with all fields"""
        # Arrange & Act
        created_at = datetime(2025, 12, 29, 9, 0, 0, tzinfo=timezone.utc)
        ai_op = AIOperation(
            type="PRCreation",
            model="claude-sonnet-4",
            cost_usd=0.12,
            created_at=created_at,
            workflow_run_id=111222
        )
        pr = PullRequest(
            task_index=1,
            pr_number=42,
            branch_name="claudestep/project/step-1",
            reviewer="alice",
            pr_state="open",
            created_at=created_at,
            ai_operations=[ai_op]
        )

        # Assert
        assert pr.task_index == 1
        assert pr.pr_number == 42
        assert pr.branch_name == "claudestep/project/step-1"
        assert pr.reviewer == "alice"
        assert pr.pr_state == "open"
        assert pr.created_at == created_at
        assert len(pr.ai_operations) == 1

    def test_pull_request_to_dict_serialization(self):
        """Should serialize pull request to dictionary correctly"""
        # Arrange
        created_at = datetime(2025, 12, 29, 9, 0, 0, tzinfo=timezone.utc)
        ai_op = AIOperation(
            type="PRCreation",
            model="claude-sonnet-4",
            cost_usd=0.12,
            created_at=created_at,
            workflow_run_id=111222
        )
        pr = PullRequest(
            task_index=1,
            pr_number=42,
            branch_name="claudestep/project/step-1",
            reviewer="alice",
            pr_state="merged",
            created_at=created_at,
            ai_operations=[ai_op]
        )

        # Act
        result = pr.to_dict()

        # Assert
        assert result["task_index"] == 1
        assert result["pr_number"] == 42
        assert result["branch_name"] == "claudestep/project/step-1"
        assert result["reviewer"] == "alice"
        assert result["pr_state"] == "merged"
        assert result["created_at"] == created_at.isoformat()
        assert len(result["ai_operations"]) == 1

    def test_pull_request_from_dict_deserialization(self):
        """Should deserialize pull request from dictionary correctly"""
        # Arrange
        data = {
            "task_index": 2,
            "pr_number": 43,
            "branch_name": "claudestep/project/step-2",
            "reviewer": "bob",
            "pr_state": "open",
            "created_at": "2025-12-29T10:00:00Z",
            "ai_operations": [
                {
                    "type": "PRCreation",
                    "model": "claude-sonnet-4",
                    "cost_usd": 0.15,
                    "created_at": "2025-12-29T10:00:00Z",
                    "workflow_run_id": 333444
                }
            ]
        }

        # Act
        pr = PullRequest.from_dict(data)

        # Assert
        assert pr.task_index == 2
        assert pr.pr_number == 43
        assert pr.reviewer == "bob"
        assert pr.pr_state == "open"
        assert len(pr.ai_operations) == 1

    def test_pull_request_get_total_cost(self):
        """Should calculate total cost from all AI operations"""
        # Arrange
        created_at = datetime(2025, 12, 29, 9, 0, 0, tzinfo=timezone.utc)
        ai_ops = [
            AIOperation(
                type="PRCreation",
                model="claude-sonnet-4",
                cost_usd=0.12,
                created_at=created_at,
                workflow_run_id=111
            ),
            AIOperation(
                type="PRRefinement",
                model="claude-sonnet-4",
                cost_usd=0.08,
                created_at=created_at,
                workflow_run_id=222
            ),
            AIOperation(
                type="PRSummary",
                model="claude-haiku-4",
                cost_usd=0.02,
                created_at=created_at,
                workflow_run_id=333
            )
        ]
        pr = PullRequest(
            task_index=1,
            pr_number=42,
            branch_name="claudestep/project/step-1",
            reviewer="alice",
            pr_state="merged",
            created_at=created_at,
            ai_operations=ai_ops
        )

        # Act
        total_cost = pr.get_total_cost()

        # Assert
        assert total_cost == 0.22  # 0.12 + 0.08 + 0.02

    def test_pull_request_get_total_tokens(self):
        """Should calculate total input and output tokens"""
        # Arrange
        created_at = datetime(2025, 12, 29, 9, 0, 0, tzinfo=timezone.utc)
        ai_ops = [
            AIOperation(
                type="PRCreation",
                model="claude-sonnet-4",
                cost_usd=0.12,
                created_at=created_at,
                workflow_run_id=111,
                tokens_input=5000,
                tokens_output=2000
            ),
            AIOperation(
                type="PRRefinement",
                model="claude-sonnet-4",
                cost_usd=0.08,
                created_at=created_at,
                workflow_run_id=222,
                tokens_input=3000,
                tokens_output=1500
            )
        ]
        pr = PullRequest(
            task_index=1,
            pr_number=42,
            branch_name="claudestep/project/step-1",
            reviewer="alice",
            pr_state="merged",
            created_at=created_at,
            ai_operations=ai_ops
        )

        # Act
        total_input, total_output = pr.get_total_tokens()

        # Assert
        assert total_input == 8000  # 5000 + 3000
        assert total_output == 3500  # 2000 + 1500

    def test_pull_request_get_total_duration(self):
        """Should calculate total duration in seconds"""
        # Arrange
        created_at = datetime(2025, 12, 29, 9, 0, 0, tzinfo=timezone.utc)
        ai_ops = [
            AIOperation(
                type="PRCreation",
                model="claude-sonnet-4",
                cost_usd=0.12,
                created_at=created_at,
                workflow_run_id=111,
                duration_seconds=45.5
            ),
            AIOperation(
                type="PRRefinement",
                model="claude-sonnet-4",
                cost_usd=0.08,
                created_at=created_at,
                workflow_run_id=222,
                duration_seconds=30.2
            )
        ]
        pr = PullRequest(
            task_index=1,
            pr_number=42,
            branch_name="claudestep/project/step-1",
            reviewer="alice",
            pr_state="merged",
            created_at=created_at,
            ai_operations=ai_ops
        )

        # Act
        total_duration = pr.get_total_duration()

        # Assert
        assert total_duration == 75.7  # 45.5 + 30.2


class TestHybridProjectMetadata:
    """Tests for HybridProjectMetadata model"""

    def test_create_empty_project(self):
        """Should create empty project with default values"""
        # Act
        project = HybridProjectMetadata.create_empty("auth-refactor")

        # Assert
        assert project.project == "auth-refactor"
        assert project.schema_version == "2.0"
        assert len(project.tasks) == 0
        assert len(project.pull_requests) == 0
        assert project.last_updated is not None

    def test_project_to_dict_serialization(self):
        """Should serialize project to dictionary correctly"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED),
                Task(index=2, description="Task 2", status=TaskStatus.PENDING)
            ],
            pull_requests=[]
        )

        # Act
        result = project.to_dict()

        # Assert
        assert result["schema_version"] == "2.0"
        assert result["project"] == "test-project"
        assert result["last_updated"] == created_at.isoformat()
        assert len(result["tasks"]) == 2
        assert len(result["pull_requests"]) == 0

    def test_project_from_dict_deserialization(self):
        """Should deserialize project from dictionary correctly"""
        # Arrange
        data = {
            "schema_version": "2.0",
            "project": "my-project",
            "last_updated": "2025-12-29T10:00:00Z",
            "tasks": [
                {"index": 1, "description": "Task 1", "status": "pending"}
            ],
            "pull_requests": []
        }

        # Act
        project = HybridProjectMetadata.from_dict(data)

        # Assert
        assert project.project == "my-project"
        assert project.schema_version == "2.0"
        assert len(project.tasks) == 1
        assert len(project.pull_requests) == 0

    def test_sync_task_statuses_with_no_prs(self):
        """Should set all tasks to pending when no PRs exist"""
        # Arrange
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=datetime.now(timezone.utc),
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.IN_PROGRESS),
                Task(index=2, description="Task 2", status=TaskStatus.COMPLETED)
            ],
            pull_requests=[]
        )

        # Act
        project.sync_task_statuses()

        # Assert
        assert project.tasks[0].status == TaskStatus.PENDING
        assert project.tasks[1].status == TaskStatus.PENDING

    def test_sync_task_statuses_with_open_pr(self):
        """Should set task to in_progress when PR is open"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.PENDING)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="open",
                    created_at=created_at,
                    ai_operations=[]
                )
            ]
        )

        # Act
        project.sync_task_statuses()

        # Assert
        assert project.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_sync_task_statuses_with_merged_pr(self):
        """Should set task to completed when PR is merged"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.IN_PROGRESS)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="merged",
                    created_at=created_at,
                    ai_operations=[]
                )
            ]
        )

        # Act
        project.sync_task_statuses()

        # Assert
        assert project.tasks[0].status == TaskStatus.COMPLETED

    def test_sync_task_statuses_with_closed_pr(self):
        """Should set task to in_progress when PR is closed (not merged)"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.PENDING)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="closed",
                    created_at=created_at,
                    ai_operations=[]
                )
            ]
        )

        # Act
        project.sync_task_statuses()

        # Assert
        assert project.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_sync_task_statuses_uses_latest_pr_for_retries(self):
        """Should use latest PR when multiple PRs exist for same task"""
        # Arrange
        older_time = datetime(2025, 12, 28, 10, 0, 0, tzinfo=timezone.utc)
        newer_time = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=newer_time,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.PENDING)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="closed",
                    created_at=older_time,
                    ai_operations=[]
                ),
                PullRequest(
                    task_index=1,
                    pr_number=45,
                    branch_name="claudestep/project/step-1-retry",
                    reviewer="bob",
                    pr_state="merged",
                    created_at=newer_time,
                    ai_operations=[]
                )
            ]
        )

        # Act
        project.sync_task_statuses()

        # Assert
        # Should use newer PR (merged) instead of older PR (closed)
        assert project.tasks[0].status == TaskStatus.COMPLETED

    def test_get_task_by_index_found(self):
        """Should return task when found by index"""
        # Arrange
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=datetime.now(timezone.utc),
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.PENDING),
                Task(index=2, description="Task 2", status=TaskStatus.PENDING)
            ],
            pull_requests=[]
        )

        # Act
        task = project.get_task_by_index(2)

        # Assert
        assert task is not None
        assert task.index == 2
        assert task.description == "Task 2"

    def test_get_task_by_index_not_found(self):
        """Should return None when task not found"""
        # Arrange
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=datetime.now(timezone.utc),
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.PENDING)
            ],
            pull_requests=[]
        )

        # Act
        task = project.get_task_by_index(99)

        # Assert
        assert task is None

    def test_get_prs_for_task(self):
        """Should return all PRs for a given task index"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="closed",
                    created_at=created_at,
                    ai_operations=[]
                ),
                PullRequest(
                    task_index=1,
                    pr_number=45,
                    branch_name="claudestep/project/step-1-retry",
                    reviewer="bob",
                    pr_state="merged",
                    created_at=created_at,
                    ai_operations=[]
                ),
                PullRequest(
                    task_index=2,
                    pr_number=46,
                    branch_name="claudestep/project/step-2",
                    reviewer="alice",
                    pr_state="open",
                    created_at=created_at,
                    ai_operations=[]
                )
            ]
        )

        # Act
        prs = project.get_prs_for_task(1)

        # Assert
        assert len(prs) == 2
        assert prs[0].pr_number == 42
        assert prs[1].pr_number == 45

    def test_get_total_cost(self):
        """Should calculate total cost across all PRs"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="merged",
                    created_at=created_at,
                    ai_operations=[
                        AIOperation(
                            type="PRCreation",
                            model="claude-sonnet-4",
                            cost_usd=0.12,
                            created_at=created_at,
                            workflow_run_id=111
                        )
                    ]
                ),
                PullRequest(
                    task_index=2,
                    pr_number=43,
                    branch_name="claudestep/project/step-2",
                    reviewer="bob",
                    pr_state="open",
                    created_at=created_at,
                    ai_operations=[
                        AIOperation(
                            type="PRCreation",
                            model="claude-sonnet-4",
                            cost_usd=0.15,
                            created_at=created_at,
                            workflow_run_id=222
                        ),
                        AIOperation(
                            type="PRRefinement",
                            model="claude-sonnet-4",
                            cost_usd=0.08,
                            created_at=created_at,
                            workflow_run_id=333
                        )
                    ]
                )
            ]
        )

        # Act
        total_cost = project.get_total_cost()

        # Assert
        assert total_cost == 0.35  # 0.12 + 0.15 + 0.08

    def test_get_cost_by_model(self):
        """Should return cost breakdown by model"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/project/step-1",
                    reviewer="alice",
                    pr_state="merged",
                    created_at=created_at,
                    ai_operations=[
                        AIOperation(
                            type="PRCreation",
                            model="claude-sonnet-4",
                            cost_usd=0.12,
                            created_at=created_at,
                            workflow_run_id=111
                        ),
                        AIOperation(
                            type="PRRefinement",
                            model="claude-sonnet-4",
                            cost_usd=0.08,
                            created_at=created_at,
                            workflow_run_id=222
                        ),
                        AIOperation(
                            type="PRSummary",
                            model="claude-haiku-4",
                            cost_usd=0.02,
                            created_at=created_at,
                            workflow_run_id=333
                        )
                    ]
                )
            ]
        )

        # Act
        cost_by_model = project.get_cost_by_model()

        # Assert
        assert cost_by_model["claude-sonnet-4"] == 0.20  # 0.12 + 0.08
        assert cost_by_model["claude-haiku-4"] == 0.02

    def test_get_progress_stats(self):
        """Should return task counts by status"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED),
                Task(index=2, description="Task 2", status=TaskStatus.COMPLETED),
                Task(index=3, description="Task 3", status=TaskStatus.IN_PROGRESS),
                Task(index=4, description="Task 4", status=TaskStatus.PENDING),
                Task(index=5, description="Task 5", status=TaskStatus.PENDING),
                Task(index=6, description="Task 6", status=TaskStatus.PENDING),
            ],
            pull_requests=[]
        )

        # Act
        stats = project.get_progress_stats()

        # Assert
        assert stats["total"] == 6
        assert stats["completed"] == 2
        assert stats["in_progress"] == 1
        assert stats["pending"] == 3

    def test_get_completion_percentage(self):
        """Should calculate completion percentage correctly"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED),
                Task(index=2, description="Task 2", status=TaskStatus.COMPLETED),
                Task(index=3, description="Task 3", status=TaskStatus.IN_PROGRESS),
                Task(index=4, description="Task 4", status=TaskStatus.PENDING),
            ],
            pull_requests=[]
        )

        # Act
        percentage = project.get_completion_percentage()

        # Assert
        assert percentage == 50.0  # 2 out of 4 tasks completed

    def test_get_completion_percentage_empty_project(self):
        """Should return 0% for project with no tasks"""
        # Arrange
        project = HybridProjectMetadata.create_empty("test-project")

        # Act
        percentage = project.get_completion_percentage()

        # Assert
        assert percentage == 0.0

    def test_get_completion_percentage_all_complete(self):
        """Should return 100% when all tasks completed"""
        # Arrange
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        project = HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED),
                Task(index=2, description="Task 2", status=TaskStatus.COMPLETED),
            ],
            pull_requests=[]
        )

        # Act
        percentage = project.get_completion_percentage()

        # Assert
        assert percentage == 100.0
