"""Tests for GitHub CLI operations"""

import json
import subprocess
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, call, mock_open, patch

import pytest

from claudestep.domain.exceptions import GitHubAPIError
from claudestep.infrastructure.github.operations import (
    download_artifact_json,
    ensure_label_exists,
    file_exists_in_branch,
    get_file_from_branch,
    gh_api_call,
    list_merged_pull_requests,
    list_open_pull_requests,
    list_pull_requests,
    run_gh_command,
)


class TestRunGhCommand:
    """Test suite for run_gh_command function"""

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_success(self, mock_run):
        """Should execute gh command and return stdout"""
        # Arrange
        mock_run.return_value = Mock(stdout="  command output  \n", stderr="")
        args = ["pr", "list"]

        # Act
        result = run_gh_command(args)

        # Assert
        assert result == "command output"
        mock_run.assert_called_once_with(["gh", "pr", "list"])

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_strips_whitespace(self, mock_run):
        """Should strip leading and trailing whitespace from output"""
        # Arrange
        mock_run.return_value = Mock(stdout="\n\n  PR #123  \n\n", stderr="")
        args = ["pr", "view", "123"]

        # Act
        result = run_gh_command(args)

        # Assert
        assert result == "PR #123"

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_handles_empty_output(self, mock_run):
        """Should handle empty output correctly"""
        # Arrange
        mock_run.return_value = Mock(stdout="", stderr="")
        args = ["pr", "list"]

        # Act
        result = run_gh_command(args)

        # Assert
        assert result == ""

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_raises_github_error_on_failure(self, mock_run):
        """Should raise GitHubAPIError when gh command fails"""
        # Arrange
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "pr", "view", "999"],
            stderr="could not resolve to a PullRequest"
        )
        mock_run.side_effect = error
        args = ["pr", "view", "999"]

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="GitHub CLI command failed"):
            run_gh_command(args)

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_includes_stderr_in_error(self, mock_run):
        """Should include stderr output in GitHubAPIError message"""
        # Arrange
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "api"],
            stderr="HTTP 404: Not Found"
        )
        mock_run.side_effect = error
        args = ["api", "/invalid/endpoint"]

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="HTTP 404"):
            run_gh_command(args)

    @patch('claudestep.infrastructure.github.operations.run_command')
    def test_run_gh_command_includes_command_in_error(self, mock_run):
        """Should include command arguments in error message"""
        # Arrange
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "pr", "create"],
            stderr="title is required"
        )
        mock_run.side_effect = error
        args = ["pr", "create", "--body", "test"]

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="pr create --body test"):
            run_gh_command(args)


class TestGhApiCall:
    """Test suite for gh_api_call function"""

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_success(self, mock_run_gh):
        """Should execute API call and return parsed JSON"""
        # Arrange
        mock_run_gh.return_value = '{"key": "value", "number": 123}'
        endpoint = "/repos/owner/repo/pulls/1"

        # Act
        result = gh_api_call(endpoint)

        # Assert
        assert result == {"key": "value", "number": 123}
        mock_run_gh.assert_called_once_with(["api", endpoint, "--method", "GET"])

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_with_post_method(self, mock_run_gh):
        """Should execute POST request with correct method"""
        # Arrange
        mock_run_gh.return_value = '{"created": true}'
        endpoint = "/repos/owner/repo/issues"

        # Act
        result = gh_api_call(endpoint, method="POST")

        # Assert
        assert result == {"created": True}
        mock_run_gh.assert_called_once_with(["api", endpoint, "--method", "POST"])

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_handles_empty_response(self, mock_run_gh):
        """Should return empty dict when response is empty"""
        # Arrange
        mock_run_gh.return_value = ""
        endpoint = "/repos/owner/repo/actions/runs"

        # Act
        result = gh_api_call(endpoint)

        # Assert
        assert result == {}

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_raises_error_on_invalid_json(self, mock_run_gh):
        """Should raise GitHubAPIError when response is invalid JSON"""
        # Arrange
        mock_run_gh.return_value = "not valid json {{"
        endpoint = "/repos/owner/repo/pulls"

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="Invalid JSON from API"):
            gh_api_call(endpoint)

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_handles_nested_json(self, mock_run_gh):
        """Should correctly parse nested JSON structures"""
        # Arrange
        mock_run_gh.return_value = '{"data": {"nested": {"value": 42}}}'
        endpoint = "/repos/owner/repo/contents"

        # Act
        result = gh_api_call(endpoint)

        # Assert
        assert result == {"data": {"nested": {"value": 42}}}

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_gh_api_call_propagates_gh_errors(self, mock_run_gh):
        """Should propagate GitHubAPIError from run_gh_command"""
        # Arrange
        mock_run_gh.side_effect = GitHubAPIError("API rate limit exceeded")
        endpoint = "/repos/owner/repo/pulls"

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="API rate limit exceeded"):
            gh_api_call(endpoint)


class TestDownloadArtifactJson:
    """Test suite for download_artifact_json function"""

    @patch('claudestep.infrastructure.github.operations.subprocess.run')
    @patch('claudestep.infrastructure.github.operations.zipfile.ZipFile')
    @patch('claudestep.infrastructure.github.operations.os.path.exists')
    @patch('claudestep.infrastructure.github.operations.os.remove')
    def test_download_artifact_json_success(self, mock_remove, mock_exists, mock_zipfile, mock_subprocess):
        """Should download, extract, and parse artifact JSON"""
        # Arrange
        repo = "owner/repo"
        artifact_id = 12345
        expected_data = {"cost": 1.23, "task": "test"}

        mock_subprocess.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        mock_zip = Mock()
        mock_zip.namelist.return_value = ["metadata.json", "other.txt"]
        mock_zip.open.return_value.__enter__ = Mock(return_value=Mock(
            read=Mock(return_value=json.dumps(expected_data).encode())
        ))
        mock_zip.open.return_value.__exit__ = Mock(return_value=False)
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zipfile.return_value.__exit__ = Mock(return_value=False)

        # Act
        result = download_artifact_json(repo, artifact_id)

        # Assert
        assert result == expected_data
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert args[0] == "gh"
        assert args[1] == "api"
        assert f"/repos/{repo}/actions/artifacts/{artifact_id}/zip" in args

    @patch('claudestep.infrastructure.github.operations.subprocess.run')
    @patch('claudestep.infrastructure.github.operations.zipfile.ZipFile')
    @patch('claudestep.infrastructure.github.operations.os.path.exists')
    @patch('claudestep.infrastructure.github.operations.os.remove')
    def test_download_artifact_json_cleans_up_temp_file(self, mock_remove, mock_exists, mock_zipfile, mock_subprocess):
        """Should clean up temporary zip file after processing"""
        # Arrange
        repo = "owner/repo"
        artifact_id = 12345

        mock_subprocess.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        mock_zip = Mock()
        mock_zip.namelist.return_value = ["data.json"]
        mock_zip.open.return_value.__enter__ = Mock(return_value=Mock(
            read=Mock(return_value=b'{"key": "value"}')
        ))
        mock_zip.open.return_value.__exit__ = Mock(return_value=False)
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zipfile.return_value.__exit__ = Mock(return_value=False)

        # Act
        download_artifact_json(repo, artifact_id)

        # Assert
        mock_remove.assert_called_once()

    @patch('claudestep.infrastructure.github.operations.subprocess.run')
    @patch('claudestep.infrastructure.github.operations.zipfile.ZipFile')
    @patch('claudestep.infrastructure.github.operations.os.path.exists')
    @patch('claudestep.infrastructure.github.operations.os.remove')
    def test_download_artifact_json_returns_none_when_no_json_in_zip(self, mock_remove, mock_exists, mock_zipfile, mock_subprocess, capsys):
        """Should return None when no JSON file found in artifact"""
        # Arrange
        repo = "owner/repo"
        artifact_id = 12345

        mock_subprocess.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        mock_zip = Mock()
        mock_zip.namelist.return_value = ["readme.txt", "data.csv"]  # No JSON files
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zipfile.return_value.__exit__ = Mock(return_value=False)

        # Act
        result = download_artifact_json(repo, artifact_id)

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No JSON file found" in captured.out

    @patch('claudestep.infrastructure.github.operations.subprocess.run')
    def test_download_artifact_json_returns_none_on_download_failure(self, mock_subprocess, capsys):
        """Should return None and print warning when download fails"""
        # Arrange
        repo = "owner/repo"
        artifact_id = 12345
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, ["gh"], stderr="Not found")

        # Act
        result = download_artifact_json(repo, artifact_id)

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "Failed to download/parse artifact" in captured.out

    @patch('claudestep.infrastructure.github.operations.subprocess.run')
    @patch('claudestep.infrastructure.github.operations.zipfile.ZipFile')
    @patch('claudestep.infrastructure.github.operations.os.path.exists')
    @patch('claudestep.infrastructure.github.operations.os.remove')
    def test_download_artifact_json_returns_none_on_parse_error(self, mock_remove, mock_exists, mock_zipfile, mock_subprocess, capsys):
        """Should return None when JSON parsing fails"""
        # Arrange
        repo = "owner/repo"
        artifact_id = 12345

        mock_subprocess.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        mock_zip = Mock()
        mock_zip.namelist.return_value = ["data.json"]
        mock_zip.open.return_value.__enter__ = Mock(return_value=Mock(
            read=Mock(return_value=b'invalid json {{')
        ))
        mock_zip.open.return_value.__exit__ = Mock(return_value=False)
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zipfile.return_value.__exit__ = Mock(return_value=False)

        # Act
        result = download_artifact_json(repo, artifact_id)

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "Failed to download/parse artifact" in captured.out


class TestEnsureLabelExists:
    """Test suite for ensure_label_exists function"""

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_ensure_label_creates_new_label(self, mock_run_gh, mock_github_actions_helper):
        """Should create label when it doesn't exist"""
        # Arrange
        mock_run_gh.return_value = "Label created"
        label = "claude-step"
        gh = mock_github_actions_helper

        # Act
        ensure_label_exists(label, gh)

        # Assert
        mock_run_gh.assert_called_once()
        args = mock_run_gh.call_args[0][0]
        assert "label" in args
        assert "create" in args
        assert label in args
        assert "--color" in args
        gh.write_step_summary.assert_called_once_with(f"- Label '{label}': ✅ Created")
        gh.set_notice.assert_called_once_with(f"Created label '{label}'")

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_ensure_label_handles_existing_label(self, mock_run_gh, mock_github_actions_helper):
        """Should handle label that already exists gracefully"""
        # Arrange
        mock_run_gh.side_effect = GitHubAPIError("label already exists on repository")
        label = "claude-step"
        gh = mock_github_actions_helper

        # Act
        ensure_label_exists(label, gh)

        # Assert
        gh.write_step_summary.assert_called_once_with(f"- Label '{label}': ✅ Already exists")

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_ensure_label_reraises_other_errors(self, mock_run_gh, mock_github_actions_helper):
        """Should re-raise GitHubAPIError if not about existing label"""
        # Arrange
        mock_run_gh.side_effect = GitHubAPIError("API rate limit exceeded")
        label = "claude-step"
        gh = mock_github_actions_helper

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="API rate limit exceeded"):
            ensure_label_exists(label, gh)

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_ensure_label_uses_correct_color_and_description(self, mock_run_gh, mock_github_actions_helper):
        """Should create label with correct color and description"""
        # Arrange
        mock_run_gh.return_value = "success"
        label = "test-label"
        gh = mock_github_actions_helper

        # Act
        ensure_label_exists(label, gh)

        # Assert
        args = mock_run_gh.call_args[0][0]
        assert "--description" in args
        desc_idx = args.index("--description")
        assert "ClaudeStep automated refactoring" == args[desc_idx + 1]
        assert "--color" in args
        color_idx = args.index("--color")
        assert "0E8A16" == args[color_idx + 1]


class TestGetFileFromBranch:
    """Test suite for get_file_from_branch function"""

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_success(self, mock_gh_api):
        """Should fetch and decode file content from branch"""
        # Arrange
        import base64
        file_content = "# Sample Spec File\n\nTask 1: Do something"
        encoded = base64.b64encode(file_content.encode()).decode()
        mock_gh_api.return_value = {"content": encoded, "encoding": "base64"}

        repo = "owner/repo"
        branch = "main"
        file_path = "claude-step/project/spec.md"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result == file_content
        mock_gh_api.assert_called_once_with(
            f"/repos/{repo}/contents/{file_path}?ref={branch}",
            method="GET"
        )

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_handles_newlines_in_base64(self, mock_gh_api):
        """Should handle base64 content with newlines (GitHub adds them)"""
        # Arrange
        import base64
        file_content = "Line 1\nLine 2\nLine 3"
        encoded = base64.b64encode(file_content.encode()).decode()
        # Simulate GitHub adding newlines every 60 chars
        encoded_with_newlines = encoded[:20] + "\n" + encoded[20:40] + "\n" + encoded[40:]
        mock_gh_api.return_value = {"content": encoded_with_newlines, "encoding": "base64"}

        repo = "owner/repo"
        branch = "main"
        file_path = "test.txt"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result == file_content

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_returns_none_on_404(self, mock_gh_api):
        """Should return None when file not found (404 error)"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("404 Not Found")
        repo = "owner/repo"
        branch = "main"
        file_path = "missing/file.md"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result is None

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_returns_none_when_not_found_in_message(self, mock_gh_api):
        """Should return None when 'Not Found' in error message"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("HTTP 404: Not Found (cached)")
        repo = "owner/repo"
        branch = "develop"
        file_path = "nonexistent.yml"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result is None

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_reraises_other_errors(self, mock_gh_api):
        """Should re-raise GitHubAPIError for non-404 errors"""
        # Arrange
        mock_gh_api.side_effect = GitHubAPIError("API rate limit exceeded")
        repo = "owner/repo"
        branch = "main"
        file_path = "some/file.md"

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="API rate limit exceeded"):
            get_file_from_branch(repo, branch, file_path)

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_returns_none_when_no_content_field(self, mock_gh_api):
        """Should return None when API response lacks content field"""
        # Arrange
        mock_gh_api.return_value = {"type": "dir", "name": "folder"}
        repo = "owner/repo"
        branch = "main"
        file_path = "directory"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result is None

    @patch('claudestep.infrastructure.github.operations.gh_api_call')
    def test_get_file_from_branch_handles_unicode_content(self, mock_gh_api):
        """Should correctly decode unicode characters"""
        # Arrange
        import base64
        file_content = "Unicode test: 你好世界 🎉 café"
        encoded = base64.b64encode(file_content.encode('utf-8')).decode()
        mock_gh_api.return_value = {"content": encoded}

        repo = "owner/repo"
        branch = "main"
        file_path = "unicode.txt"

        # Act
        result = get_file_from_branch(repo, branch, file_path)

        # Assert
        assert result == file_content


class TestFileExistsInBranch:
    """Test suite for file_exists_in_branch function"""

    @patch('claudestep.infrastructure.github.operations.get_file_from_branch')
    def test_file_exists_returns_true_when_file_found(self, mock_get_file):
        """Should return True when file content is returned"""
        # Arrange
        mock_get_file.return_value = "file content here"
        repo = "owner/repo"
        branch = "main"
        file_path = "existing/file.md"

        # Act
        result = file_exists_in_branch(repo, branch, file_path)

        # Assert
        assert result is True
        mock_get_file.assert_called_once_with(repo, branch, file_path)

    @patch('claudestep.infrastructure.github.operations.get_file_from_branch')
    def test_file_exists_returns_false_when_file_not_found(self, mock_get_file):
        """Should return False when get_file_from_branch returns None"""
        # Arrange
        mock_get_file.return_value = None
        repo = "owner/repo"
        branch = "main"
        file_path = "missing/file.md"

        # Act
        result = file_exists_in_branch(repo, branch, file_path)

        # Assert
        assert result is False

    @patch('claudestep.infrastructure.github.operations.get_file_from_branch')
    def test_file_exists_returns_true_for_empty_file(self, mock_get_file):
        """Should return True even for empty file content"""
        # Arrange
        mock_get_file.return_value = ""
        repo = "owner/repo"
        branch = "develop"
        file_path = "empty.txt"

        # Act
        result = file_exists_in_branch(repo, branch, file_path)

        # Assert
        assert result is True

    @patch('claudestep.infrastructure.github.operations.get_file_from_branch')
    def test_file_exists_propagates_errors(self, mock_get_file):
        """Should propagate GitHubAPIError from get_file_from_branch"""
        # Arrange
        mock_get_file.side_effect = GitHubAPIError("API error")
        repo = "owner/repo"
        branch = "main"
        file_path = "file.md"

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="API error"):
            file_exists_in_branch(repo, branch, file_path)


class TestListPullRequests:
    """Test suite for list_pull_requests function"""

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_success(self, mock_run_gh):
        """Should fetch PRs and return domain models"""
        # Arrange
        pr_data = [
            {
                "number": 123,
                "title": "Add feature",
                "state": "OPEN",
                "createdAt": "2024-01-01T12:00:00Z",
                "mergedAt": None,
                "assignees": [{"login": "alice", "name": "Alice"}],
                "labels": [{"name": "claudestep"}]
            },
            {
                "number": 124,
                "title": "Fix bug",
                "state": "MERGED",
                "createdAt": "2024-01-02T12:00:00Z",
                "mergedAt": "2024-01-03T12:00:00Z",
                "assignees": [{"login": "bob"}],
                "labels": [{"name": "claudestep"}, {"name": "bug"}]
            }
        ]
        mock_run_gh.return_value = json.dumps(pr_data)
        repo = "owner/repo"

        # Act
        result = list_pull_requests(repo)

        # Assert
        assert len(result) == 2
        assert result[0].number == 123
        assert result[0].title == "Add feature"
        assert result[0].state == "open"
        assert result[1].number == 124
        assert result[1].is_merged()

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_with_filters(self, mock_run_gh):
        """Should build command with correct filters"""
        # Arrange
        mock_run_gh.return_value = "[]"
        repo = "owner/repo"

        # Act
        list_pull_requests(repo, state="merged", label="claudestep", limit=50)

        # Assert
        args = mock_run_gh.call_args[0][0]
        assert "pr" in args
        assert "list" in args
        assert "--repo" in args
        assert "owner/repo" in args
        assert "--state" in args
        assert "merged" in args
        assert "--label" in args
        assert "claudestep" in args
        assert "--limit" in args
        assert "50" in args

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_with_assignee_filter(self, mock_run_gh):
        """Should build command with assignee filter"""
        # Arrange
        mock_run_gh.return_value = "[]"
        repo = "owner/repo"

        # Act
        list_pull_requests(repo, state="open", assignee="reviewer1")

        # Assert
        args = mock_run_gh.call_args[0][0]
        assert "pr" in args
        assert "list" in args
        assert "--assignee" in args
        assert "reviewer1" in args
        assert "--state" in args
        assert "open" in args

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_filters_by_date(self, mock_run_gh):
        """Should filter PRs by date when since parameter provided"""
        # Arrange
        cutoff = datetime(2024, 1, 2, tzinfo=timezone.utc)
        pr_data = [
            {
                "number": 123,
                "title": "Old PR",
                "state": "MERGED",
                "createdAt": "2024-01-01T12:00:00Z",
                "mergedAt": None,
                "assignees": [],
                "labels": []
            },
            {
                "number": 124,
                "title": "New PR",
                "state": "MERGED",
                "createdAt": "2024-01-03T12:00:00Z",
                "mergedAt": None,
                "assignees": [],
                "labels": []
            }
        ]
        mock_run_gh.return_value = json.dumps(pr_data)

        # Act
        result = list_pull_requests("owner/repo", since=cutoff)

        # Assert
        assert len(result) == 1
        assert result[0].number == 124

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_handles_empty_response(self, mock_run_gh):
        """Should handle empty PR list"""
        # Arrange
        mock_run_gh.return_value = "[]"

        # Act
        result = list_pull_requests("owner/repo")

        # Assert
        assert result == []

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_raises_on_invalid_json(self, mock_run_gh):
        """Should raise GitHubAPIError on invalid JSON"""
        # Arrange
        mock_run_gh.return_value = "invalid json {{"

        # Act & Assert
        with pytest.raises(GitHubAPIError, match="Invalid JSON"):
            list_pull_requests("owner/repo")

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_pull_requests_handles_empty_output(self, mock_run_gh):
        """Should handle empty string output"""
        # Arrange
        mock_run_gh.return_value = ""

        # Act
        result = list_pull_requests("owner/repo")

        # Assert
        assert result == []


class TestListMergedPullRequests:
    """Test suite for list_merged_pull_requests convenience function"""

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_merged_pull_requests_filters_by_merged_at(self, mock_run_gh):
        """Should filter merged PRs by merged_at date"""
        # Arrange
        cutoff = datetime(2024, 1, 2, tzinfo=timezone.utc)
        pr_data = [
            {
                "number": 123,
                "title": "Old merged PR",
                "state": "MERGED",
                "createdAt": "2024-01-01T12:00:00Z",
                "mergedAt": "2024-01-01T13:00:00Z",
                "assignees": [],
                "labels": []
            },
            {
                "number": 124,
                "title": "New merged PR",
                "state": "MERGED",
                "createdAt": "2024-01-01T12:00:00Z",
                "mergedAt": "2024-01-03T12:00:00Z",
                "assignees": [],
                "labels": []
            }
        ]
        mock_run_gh.return_value = json.dumps(pr_data)

        # Act
        result = list_merged_pull_requests("owner/repo", since=cutoff)

        # Assert
        assert len(result) == 1
        assert result[0].number == 124

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_merged_pull_requests_with_label(self, mock_run_gh):
        """Should pass label filter to list_pull_requests"""
        # Arrange
        mock_run_gh.return_value = "[]"
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        # Act
        list_merged_pull_requests("owner/repo", since=cutoff, label="claudestep")

        # Assert
        args = mock_run_gh.call_args[0][0]
        assert "--label" in args
        assert "claudestep" in args
        assert "--state" in args
        assert "merged" in args

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_merged_pull_requests_excludes_prs_without_merged_at(self, mock_run_gh):
        """Should exclude PRs that don't have merged_at timestamp"""
        # Arrange
        cutoff = datetime(2024, 1, 1, tzinfo=timezone.utc)
        pr_data = [
            {
                "number": 123,
                "title": "Merged PR",
                "state": "MERGED",
                "createdAt": "2024-01-02T12:00:00Z",
                "mergedAt": "2024-01-03T12:00:00Z",
                "assignees": [],
                "labels": []
            },
            {
                "number": 124,
                "title": "No merge timestamp",
                "state": "MERGED",
                "createdAt": "2024-01-02T12:00:00Z",
                "mergedAt": None,
                "assignees": [],
                "labels": []
            }
        ]
        mock_run_gh.return_value = json.dumps(pr_data)

        # Act
        result = list_merged_pull_requests("owner/repo", since=cutoff)

        # Assert
        assert len(result) == 1
        assert result[0].number == 123


class TestListOpenPullRequests:
    """Test suite for list_open_pull_requests convenience function"""

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_open_pull_requests_success(self, mock_run_gh):
        """Should fetch open PRs"""
        # Arrange
        pr_data = [
            {
                "number": 123,
                "title": "Open PR",
                "state": "OPEN",
                "createdAt": "2024-01-01T12:00:00Z",
                "mergedAt": None,
                "assignees": [],
                "labels": []
            }
        ]
        mock_run_gh.return_value = json.dumps(pr_data)

        # Act
        result = list_open_pull_requests("owner/repo")

        # Assert
        assert len(result) == 1
        assert result[0].is_open()

    @patch('claudestep.infrastructure.github.operations.run_gh_command')
    def test_list_open_pull_requests_with_label(self, mock_run_gh):
        """Should filter by label"""
        # Arrange
        mock_run_gh.return_value = "[]"

        # Act
        list_open_pull_requests("owner/repo", label="claudestep", limit=25)

        # Assert
        args = mock_run_gh.call_args[0][0]
        assert "--state" in args
        assert "open" in args
        assert "--label" in args
        assert "claudestep" in args
        assert "--limit" in args
        assert "25" in args
