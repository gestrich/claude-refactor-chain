"""Unit tests for Project domain model"""

import os
import pytest
from pathlib import Path

from claudestep.domain.project import Project


class TestProjectInitialization:
    """Test suite for Project initialization"""

    def test_create_project_with_default_base_path(self):
        """Should create project with default base path"""
        # Arrange & Act
        project = Project("my-project")

        # Assert
        assert project.name == "my-project"
        assert project.base_path == "claude-step/my-project"

    def test_create_project_with_custom_base_path(self):
        """Should create project with custom base path"""
        # Arrange & Act
        project = Project("my-project", base_path="custom/path/my-project")

        # Assert
        assert project.name == "my-project"
        assert project.base_path == "custom/path/my-project"


class TestProjectPathProperties:
    """Test suite for Project path properties"""

    def test_config_path_property(self):
        """Should return correct config path"""
        # Arrange
        project = Project("my-project")

        # Act
        config_path = project.config_path

        # Assert
        assert config_path == "claude-step/my-project/configuration.yml"

    def test_spec_path_property(self):
        """Should return correct spec path"""
        # Arrange
        project = Project("my-project")

        # Act
        spec_path = project.spec_path

        # Assert
        assert spec_path == "claude-step/my-project/spec.md"

    def test_pr_template_path_property(self):
        """Should return correct PR template path"""
        # Arrange
        project = Project("my-project")

        # Act
        pr_template_path = project.pr_template_path

        # Assert
        assert pr_template_path == "claude-step/my-project/pr-template.md"

    def test_metadata_file_path_property(self):
        """Should return correct metadata file path"""
        # Arrange
        project = Project("my-project")

        # Act
        metadata_path = project.metadata_file_path

        # Assert
        assert metadata_path == "my-project.json"

    def test_paths_with_custom_base_path(self):
        """Should construct correct paths with custom base path"""
        # Arrange
        project = Project("my-project", base_path="custom/path/my-project")

        # Assert
        assert project.config_path == "custom/path/my-project/configuration.yml"
        assert project.spec_path == "custom/path/my-project/spec.md"
        assert project.pr_template_path == "custom/path/my-project/pr-template.md"
        # metadata_file_path should still be just the project name
        assert project.metadata_file_path == "my-project.json"


class TestProjectBranchName:
    """Test suite for Project branch name generation"""

    def test_get_branch_name_with_single_digit_index(self):
        """Should generate correct branch name for single digit task index"""
        # Arrange
        project = Project("my-project")

        # Act
        branch_name = project.get_branch_name(1)

        # Assert
        assert branch_name == "claude-step-my-project-1"

    def test_get_branch_name_with_multi_digit_index(self):
        """Should generate correct branch name for multi-digit task index"""
        # Arrange
        project = Project("my-project")

        # Act
        branch_name = project.get_branch_name(42)

        # Assert
        assert branch_name == "claude-step-my-project-42"

    def test_get_branch_name_with_hyphenated_project_name(self):
        """Should handle project names with hyphens"""
        # Arrange
        project = Project("my-complex-project-name")

        # Act
        branch_name = project.get_branch_name(5)

        # Assert
        assert branch_name == "claude-step-my-complex-project-name-5"


class TestProjectFromConfigPath:
    """Test suite for Project.from_config_path factory method"""

    def test_from_config_path_standard_format(self):
        """Should extract project name from standard config path"""
        # Arrange
        config_path = "claude-step/my-project/configuration.yml"

        # Act
        project = Project.from_config_path(config_path)

        # Assert
        assert project.name == "my-project"
        assert project.base_path == "claude-step/my-project"

    def test_from_config_path_with_different_base_dir(self):
        """Should extract project name from config path with different base directory"""
        # Arrange
        config_path = "custom/my-project/configuration.yml"

        # Act
        project = Project.from_config_path(config_path)

        # Assert
        assert project.name == "my-project"
        # Note: from_config_path uses default base_path construction
        assert project.base_path == "claude-step/my-project"

    def test_from_config_path_with_nested_directories(self):
        """Should extract project name from deeply nested config path"""
        # Arrange
        config_path = "deeply/nested/my-project/configuration.yml"

        # Act
        project = Project.from_config_path(config_path)

        # Assert
        assert project.name == "my-project"


class TestProjectFromBranchName:
    """Test suite for Project.from_branch_name factory method"""

    def test_from_branch_name_valid_branch(self):
        """Should extract project from valid branch name"""
        # Arrange
        branch_name = "claude-step-my-project-5"

        # Act
        project = Project.from_branch_name(branch_name)

        # Assert
        assert project is not None
        assert project.name == "my-project"
        assert project.base_path == "claude-step/my-project"

    def test_from_branch_name_with_hyphenated_project_name(self):
        """Should extract project with hyphens from branch name"""
        # Arrange
        branch_name = "claude-step-my-complex-project-name-10"

        # Act
        project = Project.from_branch_name(branch_name)

        # Assert
        assert project is not None
        assert project.name == "my-complex-project-name"

    def test_from_branch_name_invalid_format_returns_none(self):
        """Should return None for invalid branch name format"""
        # Arrange
        invalid_branches = [
            "invalid-branch-name",
            "claude-step-project",  # Missing index
            "claude-step-5",  # Missing project name
            "main",
            "feature/something",
            "claude-step-project-abc",  # Non-numeric index
        ]

        # Act & Assert
        for branch_name in invalid_branches:
            project = Project.from_branch_name(branch_name)
            assert project is None, f"Should return None for: {branch_name}"

    def test_from_branch_name_multi_digit_index(self):
        """Should extract project from branch with multi-digit task index"""
        # Arrange
        branch_name = "claude-step-my-project-123"

        # Act
        project = Project.from_branch_name(branch_name)

        # Assert
        assert project is not None
        assert project.name == "my-project"


class TestProjectFindAll:
    """Test suite for Project.find_all factory method"""

    def test_find_all_discovers_multiple_projects(self, tmp_path):
        """Should discover all valid projects in directory"""
        # Arrange
        base_dir = tmp_path / "claude-step"
        base_dir.mkdir()

        # Create valid projects
        for project_name in ["project-a", "project-b", "project-c"]:
            project_dir = base_dir / project_name
            project_dir.mkdir()
            (project_dir / "configuration.yml").write_text("reviewers: []")

        # Act
        projects = Project.find_all(str(base_dir))

        # Assert
        assert len(projects) == 3
        project_names = [p.name for p in projects]
        assert "project-a" in project_names
        assert "project-b" in project_names
        assert "project-c" in project_names

    def test_find_all_returns_sorted_projects(self, tmp_path):
        """Should return projects sorted by name"""
        # Arrange
        base_dir = tmp_path / "claude-step"
        base_dir.mkdir()

        # Create projects in non-alphabetical order
        for project_name in ["zebra", "alpha", "middle"]:
            project_dir = base_dir / project_name
            project_dir.mkdir()
            (project_dir / "configuration.yml").write_text("reviewers: []")

        # Act
        projects = Project.find_all(str(base_dir))

        # Assert
        assert len(projects) == 3
        assert [p.name for p in projects] == ["alpha", "middle", "zebra"]

    def test_find_all_ignores_directories_without_config(self, tmp_path):
        """Should ignore directories without configuration.yml"""
        # Arrange
        base_dir = tmp_path / "claude-step"
        base_dir.mkdir()

        # Valid project
        valid_project = base_dir / "valid-project"
        valid_project.mkdir()
        (valid_project / "configuration.yml").write_text("reviewers: []")

        # Invalid projects (no config file)
        (base_dir / "invalid-project-1").mkdir()
        (base_dir / "invalid-project-2").mkdir()

        # Act
        projects = Project.find_all(str(base_dir))

        # Assert
        assert len(projects) == 1
        assert projects[0].name == "valid-project"

    def test_find_all_ignores_files_in_base_dir(self, tmp_path):
        """Should ignore files (not directories) in base directory"""
        # Arrange
        base_dir = tmp_path / "claude-step"
        base_dir.mkdir()

        # Create a valid project
        project_dir = base_dir / "my-project"
        project_dir.mkdir()
        (project_dir / "configuration.yml").write_text("reviewers: []")

        # Create some files that should be ignored
        (base_dir / "README.md").write_text("# Readme")
        (base_dir / "some-file.txt").write_text("content")

        # Act
        projects = Project.find_all(str(base_dir))

        # Assert
        assert len(projects) == 1
        assert projects[0].name == "my-project"

    def test_find_all_returns_empty_list_when_directory_not_exists(self, tmp_path):
        """Should return empty list when base directory doesn't exist"""
        # Arrange
        non_existent_dir = tmp_path / "non-existent"

        # Act
        projects = Project.find_all(str(non_existent_dir))

        # Assert
        assert projects == []

    def test_find_all_with_custom_base_dir(self, tmp_path):
        """Should discover projects in custom base directory"""
        # Arrange
        custom_dir = tmp_path / "custom-projects"
        custom_dir.mkdir()

        project_dir = custom_dir / "my-project"
        project_dir.mkdir()
        (project_dir / "configuration.yml").write_text("reviewers: []")

        # Act
        projects = Project.find_all(str(custom_dir))

        # Assert
        assert len(projects) == 1
        assert projects[0].name == "my-project"


class TestProjectEquality:
    """Test suite for Project equality and hashing"""

    def test_equality_same_name_and_base_path(self):
        """Should be equal when name and base_path match"""
        # Arrange
        project1 = Project("my-project")
        project2 = Project("my-project")

        # Act & Assert
        assert project1 == project2

    def test_equality_different_names(self):
        """Should not be equal when names differ"""
        # Arrange
        project1 = Project("project-a")
        project2 = Project("project-b")

        # Act & Assert
        assert project1 != project2

    def test_equality_different_base_paths(self):
        """Should not be equal when base paths differ"""
        # Arrange
        project1 = Project("my-project", base_path="claude-step/my-project")
        project2 = Project("my-project", base_path="custom/my-project")

        # Act & Assert
        assert project1 != project2

    def test_equality_with_non_project_object(self):
        """Should not be equal to non-Project objects"""
        # Arrange
        project = Project("my-project")

        # Act & Assert
        assert project != "my-project"
        assert project != 123
        assert project != None
        assert project != {"name": "my-project"}

    def test_hash_same_for_equal_projects(self):
        """Should have same hash for equal projects"""
        # Arrange
        project1 = Project("my-project")
        project2 = Project("my-project")

        # Act & Assert
        assert hash(project1) == hash(project2)

    def test_hash_different_for_different_projects(self):
        """Should have different hash for different projects"""
        # Arrange
        project1 = Project("project-a")
        project2 = Project("project-b")

        # Act & Assert
        assert hash(project1) != hash(project2)

    def test_can_use_in_set(self):
        """Should be usable in sets"""
        # Arrange
        project1 = Project("project-a")
        project2 = Project("project-b")
        project3 = Project("project-a")  # Duplicate of project1

        # Act
        project_set = {project1, project2, project3}

        # Assert
        assert len(project_set) == 2  # Only unique projects
        assert project1 in project_set
        assert project2 in project_set

    def test_can_use_as_dict_key(self):
        """Should be usable as dictionary keys"""
        # Arrange
        project1 = Project("project-a")
        project2 = Project("project-b")

        # Act
        project_dict = {
            project1: "data-a",
            project2: "data-b"
        }

        # Assert
        assert project_dict[project1] == "data-a"
        assert project_dict[project2] == "data-b"


class TestProjectRepr:
    """Test suite for Project string representation"""

    def test_repr_contains_name_and_base_path(self):
        """Should have readable string representation"""
        # Arrange
        project = Project("my-project")

        # Act
        repr_str = repr(project)

        # Assert
        assert "Project" in repr_str
        assert "my-project" in repr_str
        assert "claude-step/my-project" in repr_str

    def test_repr_with_custom_base_path(self):
        """Should include custom base path in representation"""
        # Arrange
        project = Project("my-project", base_path="custom/path")

        # Act
        repr_str = repr(project)

        # Assert
        assert "my-project" in repr_str
        assert "custom/path" in repr_str
