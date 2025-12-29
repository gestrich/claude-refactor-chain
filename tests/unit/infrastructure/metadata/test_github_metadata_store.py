"""Unit tests for GitHubMetadataStore

Tests the GitHub branch-based metadata storage implementation
from src/claudestep/infrastructure/metadata/github_metadata_store.py
"""

import base64
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, call

from claudestep.domain.exceptions import GitHubAPIError
from claudestep.domain.models import (
    Task,
    TaskStatus,
    PullRequest,
    AIOperation,
    HybridProjectMetadata,
)
from claudestep.infrastructure.metadata.github_metadata_store import GitHubMetadataStore


class TestGitHubMetadataStore:
    """Tests for GitHubMetadataStore class"""

    @pytest.fixture
    def store(self):
        """Create a GitHubMetadataStore instance for testing"""
        return GitHubMetadataStore(repo="owner/repo", branch="claudestep-metadata")

    @pytest.fixture
    def sample_project(self):
        """Create a sample project metadata for testing"""
        created_at = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        return HybridProjectMetadata(
            schema_version="2.0",
            project="test-project",
            last_updated=created_at,
            tasks=[
                Task(index=1, description="Task 1", status=TaskStatus.COMPLETED),
                Task(index=2, description="Task 2", status=TaskStatus.PENDING)
            ],
            pull_requests=[
                PullRequest(
                    task_index=1,
                    pr_number=42,
                    branch_name="claudestep/test-project/step-1",
                    reviewer="alice",
                    pr_state="merged",
                    created_at=created_at,
                    ai_operations=[
                        AIOperation(
                            type="PRCreation",
                            model="claude-sonnet-4",
                            cost_usd=0.12,
                            created_at=created_at,
                            workflow_run_id=111222
                        )
                    ]
                )
            ]
        )

    def test_get_file_path(self, store):
        """Should construct correct file path for project"""
        # Act
        path = store._get_file_path("my-project")

        # Assert
        assert path == "projects/my-project.json"

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_ensure_branch_exists_when_branch_exists(self, mock_gh_api, store):
        """Should not create branch when it already exists"""
        # Arrange
        mock_gh_api.return_value = {"ref": "refs/heads/claudestep-metadata"}

        # Act
        store._ensure_branch_exists()

        # Assert
        # Should only check for branch existence
        mock_gh_api.assert_called_once_with(
            "/repos/owner/repo/git/ref/heads/claudestep-metadata",
            method="GET"
        )

    @patch('claudestep.infrastructure.metadata.github_metadata_store.run_gh_command')
    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_ensure_branch_exists_creates_branch_when_missing(self, mock_gh_api, mock_run_gh, store):
        """Should create branch when it doesn't exist"""
        # Arrange
        # First call (check branch): 404 error
        # Second call (get repo info): return default branch
        # Third call (create ref): success
        mock_gh_api.side_effect = [
            GitHubAPIError("404 Not Found"),  # Branch doesn't exist
            {"default_branch": "main"},  # Repo info
            {"ref": "refs/heads/claudestep-metadata"}  # Created ref
        ]
        mock_run_gh.return_value = "abc123def456"  # Default branch SHA

        # Act
        store._ensure_branch_exists()

        # Assert
        # Should check branch, get repo info, get default branch SHA, create branch, and write README
        assert mock_gh_api.call_count >= 3
        assert mock_run_gh.call_count >= 1

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_read_file_success(self, mock_gh_api, store, sample_project):
        """Should read and decode file from GitHub API"""
        # Arrange
        content_dict = sample_project.to_dict()
        content_json = json.dumps(content_dict, indent=2)
        content_base64 = base64.b64encode(content_json.encode()).decode()

        mock_gh_api.return_value = {
            "content": content_base64,
            "sha": "file-sha-123",
            "encoding": "base64"
        }

        # Act
        result = store._read_file("test-project")

        # Assert
        assert result["content"] == content_dict
        assert result["sha"] == "file-sha-123"
        mock_gh_api.assert_called_once()

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_read_file_not_found(self, mock_gh_api, store):
        """Should return None when file doesn't exist"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")

        # Act
        result = store._read_file("nonexistent-project")

        # Assert
        assert result is None

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_write_file_create_new(self, mock_gh_api, store, sample_project):
        """Should create new file when it doesn't exist"""
        # Arrange
        content_dict = sample_project.to_dict()

        # Mock: branch exists
        mock_gh_api.return_value = {"sha": "new-file-sha"}

        # Act
        store._write_file("test-project", content_dict)

        # Assert
        # Should call API to create file
        call_args = mock_gh_api.call_args
        assert call_args[0][0] == "/repos/owner/repo/contents/projects/test-project.json"
        assert call_args[1]["method"] == "PUT"

        # Verify content is base64 encoded
        data = call_args[1]["data"]
        assert "content" in data
        assert "message" in data
        assert "branch" in data

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_write_file_update_existing(self, mock_gh_api, store, sample_project):
        """Should update existing file with SHA"""
        # Arrange
        content_dict = sample_project.to_dict()

        # Mock: file exists with SHA, then update succeeds
        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata"},  # Branch exists
            {  # File exists
                "content": base64.b64encode(b"old content").decode(),
                "sha": "old-sha-123",
                "encoding": "base64"
            },
            {"sha": "new-sha-456"}  # Update success
        ]

        # Act
        store._write_file("test-project", content_dict, sha="old-sha-123")

        # Assert
        # Last call should include SHA for update
        call_args = mock_gh_api.call_args
        data = call_args[1]["data"]
        assert data["sha"] == "old-sha-123"

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_write_file_retries_on_conflict(self, mock_gh_api, store, sample_project):
        """Should retry when SHA conflict occurs"""
        # Arrange
        content_dict = sample_project.to_dict()

        # Mock: branch exists, then conflict, then success on retry
        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata"},  # Branch exists
            GitHubAPIError("409 Conflict"),  # First write fails
            {  # Read file for fresh SHA
                "content": base64.b64encode(b"current content").decode(),
                "sha": "fresh-sha-789",
                "encoding": "base64"
            },
            {"sha": "new-sha-456"}  # Second write succeeds
        ]

        # Act
        store._write_file("test-project", content_dict)

        # Assert
        # Should have retried
        assert mock_gh_api.call_count == 4

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_list_project_files_success(self, mock_gh_api, store):
        """Should list all project JSON files from Git Tree API"""
        # Arrange
        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata", "object": {"sha": "branch-sha"}},  # Get branch
            {  # Get tree
                "tree": [
                    {"path": "projects/project1.json", "type": "blob"},
                    {"path": "projects/project2.json", "type": "blob"},
                    {"path": "projects/project3.json", "type": "blob"},
                    {"path": "README.md", "type": "blob"},
                    {"path": "projects", "type": "tree"}
                ]
            }
        ]

        # Act
        result = store._list_project_files()

        # Assert
        assert len(result) == 3
        assert "project1" in result
        assert "project2" in result
        assert "project3" in result

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_list_project_files_empty_branch(self, mock_gh_api, store):
        """Should return empty list when branch doesn't exist"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")

        # Act
        result = store._list_project_files()

        # Assert
        assert result == []

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_save_project_success(self, mock_gh_api, store, sample_project):
        """Should save project metadata to GitHub"""
        # Arrange
        content_json = json.dumps(sample_project.to_dict(), indent=2)
        content_base64 = base64.b64encode(content_json.encode()).decode()

        # Mock: branch exists, file doesn't exist, write succeeds
        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata"},  # Branch exists
            GitHubAPIError("404 Not Found"),  # File doesn't exist
            {"sha": "new-sha"}  # Write succeeds
        ]

        # Act
        store.save_project(sample_project)

        # Assert
        # Should have called API to write file
        assert mock_gh_api.call_count == 3

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_get_project_success(self, mock_gh_api, store, sample_project):
        """Should retrieve project metadata from GitHub"""
        # Arrange
        content_dict = sample_project.to_dict()
        content_json = json.dumps(content_dict, indent=2)
        content_base64 = base64.b64encode(content_json.encode()).decode()

        mock_gh_api.return_value = {
            "content": content_base64,
            "sha": "file-sha-123",
            "encoding": "base64"
        }

        # Act
        result = store.get_project("test-project")

        # Assert
        assert result is not None
        assert result.project == "test-project"
        assert len(result.tasks) == 2
        assert len(result.pull_requests) == 1

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_get_project_not_found(self, mock_gh_api, store):
        """Should return None when project doesn't exist"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")

        # Act
        result = store.get_project("nonexistent-project")

        # Assert
        assert result is None

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_project_exists_true(self, mock_gh_api, store):
        """Should return True when project file exists"""
        # Arrange
        mock_gh_api.return_value = {
            "content": base64.b64encode(b"{}").decode(),
            "sha": "file-sha"
        }

        # Act
        result = store.project_exists("test-project")

        # Assert
        assert result is True

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_project_exists_false(self, mock_gh_api, store):
        """Should return False when project file doesn't exist"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")

        # Act
        result = store.project_exists("nonexistent-project")

        # Assert
        assert result is False

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_list_project_names(self, mock_gh_api, store):
        """Should return list of all project names"""
        # Arrange
        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata", "object": {"sha": "branch-sha"}},
            {
                "tree": [
                    {"path": "projects/auth-refactor.json", "type": "blob"},
                    {"path": "projects/api-migration.json", "type": "blob"},
                    {"path": "README.md", "type": "blob"}
                ]
            }
        ]

        # Act
        result = store.list_project_names()

        # Assert
        assert len(result) == 2
        assert "auth-refactor" in result
        assert "api-migration" in result

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_get_all_projects(self, mock_gh_api, store, sample_project):
        """Should return all project metadata objects"""
        # Arrange
        content_dict = sample_project.to_dict()
        content_json = json.dumps(content_dict, indent=2)
        content_base64 = base64.b64encode(content_json.encode()).decode()

        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata", "object": {"sha": "branch-sha"}},
            {
                "tree": [
                    {"path": "projects/project1.json", "type": "blob"},
                    {"path": "projects/project2.json", "type": "blob"}
                ]
            },
            {"content": content_base64, "sha": "sha1", "encoding": "base64"},
            {"content": content_base64, "sha": "sha2", "encoding": "base64"}
        ]

        # Act
        result = store.get_all_projects()

        # Assert
        assert len(result) == 2
        assert all(isinstance(p, HybridProjectMetadata) for p in result)

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_get_projects_modified_since(self, mock_gh_api, store):
        """Should filter projects by last_updated timestamp"""
        # Arrange
        old_time = datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc)
        cutoff_time = datetime(2025, 12, 25, 0, 0, 0, tzinfo=timezone.utc)

        old_project = HybridProjectMetadata(
            schema_version="2.0",
            project="old-project",
            last_updated=old_time,
            tasks=[],
            pull_requests=[]
        )
        new_project = HybridProjectMetadata(
            schema_version="2.0",
            project="new-project",
            last_updated=new_time,
            tasks=[],
            pull_requests=[]
        )

        old_content = base64.b64encode(json.dumps(old_project.to_dict()).encode()).decode()
        new_content = base64.b64encode(json.dumps(new_project.to_dict()).encode()).decode()

        mock_gh_api.side_effect = [
            {"ref": "refs/heads/claudestep-metadata", "object": {"sha": "branch-sha"}},
            {
                "tree": [
                    {"path": "projects/old-project.json", "type": "blob"},
                    {"path": "projects/new-project.json", "type": "blob"}
                ]
            },
            {"content": old_content, "sha": "sha1", "encoding": "base64"},
            {"content": new_content, "sha": "sha2", "encoding": "base64"}
        ]

        # Act
        result = store.get_projects_modified_since(cutoff_time)

        # Assert
        # Should only return new-project (modified after cutoff)
        assert len(result) == 1
        assert result[0].project == "new-project"

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_delete_project_success(self, mock_gh_api, store):
        """Should delete project file from GitHub"""
        # Arrange
        mock_gh_api.side_effect = [
            {  # Get file to retrieve SHA
                "content": base64.b64encode(b"{}").decode(),
                "sha": "file-sha-123",
                "encoding": "base64"
            },
            {"commit": {"sha": "commit-sha"}}  # Delete success
        ]

        # Act
        store.delete_project("test-project")

        # Assert
        # Should have called API to delete file
        assert mock_gh_api.call_count == 2
        delete_call = mock_gh_api.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"
        assert delete_call[1]["data"]["sha"] == "file-sha-123"

    @patch('claudestep.infrastructure.metadata.github_metadata_store.gh_api_call')
    def test_delete_project_not_found(self, mock_gh_api, store):
        """Should not raise error when deleting non-existent project"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")

        # Act & Assert
        # Should not raise exception
        store.delete_project("nonexistent-project")

    def test_initialization_with_custom_parameters(self):
        """Should initialize with custom repository, branch, and retries"""
        # Act
        store = GitHubMetadataStore(
            repo="custom/repo",
            branch="custom-branch",
            max_retries=5
        )

        # Assert
        assert store.repo == "custom/repo"
        assert store.branch == "custom-branch"
        assert store.max_retries == 5
        assert store.base_path == "projects"
