"""Builder for creating test configuration data"""

from typing import Dict, Any, Optional


class ConfigBuilder:
    """Fluent interface for creating test configuration dictionaries

    Provides a clean, readable way to create configuration data for tests
    with sensible defaults.

    Example:
        config = ConfigBuilder()
            .with_assignee("alice")
            .with_project("my-project")
            .build()
    """

    def __init__(self):
        """Initialize builder with default values"""
        self._assignee: Optional[str] = None
        self._project: str = "sample-project"
        self._custom_fields: Dict[str, Any] = {}

    def with_assignee(self, username: str) -> "ConfigBuilder":
        """Set the assignee for the configuration

        Args:
            username: GitHub username of the assignee

        Returns:
            Self for method chaining
        """
        self._assignee = username
        return self

    def with_no_assignee(self) -> "ConfigBuilder":
        """Clear the assignee (for testing no assignee)

        Returns:
            Self for method chaining
        """
        self._assignee = None
        return self

    def with_project(self, project_name: str) -> "ConfigBuilder":
        """Set the project name

        Args:
            project_name: Name of the project

        Returns:
            Self for method chaining
        """
        self._project = project_name
        return self

    def with_field(self, key: str, value: Any) -> "ConfigBuilder":
        """Add a custom field to the configuration

        Useful for testing edge cases or new configuration options.

        Args:
            key: Field name
            value: Field value

        Returns:
            Self for method chaining
        """
        self._custom_fields[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build and return the configuration dictionary

        Returns:
            Complete configuration dictionary ready for use in tests
        """
        config = {
            "project": self._project
        }

        if self._assignee:
            config["assignee"] = self._assignee

        # Merge any custom fields
        config.update(self._custom_fields)

        return config

    @staticmethod
    def with_default_assignee(username: str = "alice") -> Dict[str, Any]:
        """Quick helper for creating a config with an assignee

        Args:
            username: GitHub username (default: "alice")

        Returns:
            Configuration dictionary with assignee
        """
        return ConfigBuilder().with_assignee(username).build()

    @staticmethod
    def default() -> Dict[str, Any]:
        """Quick helper for creating a default configuration

        Creates a configuration with assignee alice.

        Returns:
            Default configuration dictionary
        """
        return ConfigBuilder().with_assignee("alice").build()

    @staticmethod
    def empty() -> Dict[str, Any]:
        """Quick helper for creating a configuration with no assignee

        Returns:
            Configuration dictionary without assignee
        """
        return ConfigBuilder().with_no_assignee().build()
