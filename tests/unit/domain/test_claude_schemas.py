"""Tests for Claude Code JSON schema definitions"""

import json

import pytest

from claudechain.domain.claude_schemas import (
    MAIN_TASK_SCHEMA,
    SUMMARY_TASK_SCHEMA,
    get_main_task_schema_json,
    get_summary_task_schema_json,
)


class TestMainTaskSchema:
    """Tests for the main task JSON schema"""

    def test_schema_is_valid_json_schema(self):
        """Main task schema has valid JSON Schema structure"""
        assert MAIN_TASK_SCHEMA["type"] == "object"
        assert "properties" in MAIN_TASK_SCHEMA
        assert "required" in MAIN_TASK_SCHEMA

    def test_schema_has_required_properties(self):
        """Main task schema has success and summary as required"""
        assert "success" in MAIN_TASK_SCHEMA["required"]
        assert "summary" in MAIN_TASK_SCHEMA["required"]

    def test_schema_has_success_property(self):
        """Main task schema has success as boolean"""
        success_prop = MAIN_TASK_SCHEMA["properties"]["success"]
        assert success_prop["type"] == "boolean"
        assert "description" in success_prop

    def test_schema_has_error_message_property(self):
        """Main task schema has error_message as optional string"""
        error_prop = MAIN_TASK_SCHEMA["properties"]["error_message"]
        assert error_prop["type"] == "string"
        assert "error_message" not in MAIN_TASK_SCHEMA["required"]

    def test_schema_has_summary_property(self):
        """Main task schema has summary as required string"""
        summary_prop = MAIN_TASK_SCHEMA["properties"]["summary"]
        assert summary_prop["type"] == "string"
        assert "summary" in MAIN_TASK_SCHEMA["required"]

    def test_schema_disallows_additional_properties(self):
        """Main task schema prevents extra properties"""
        assert MAIN_TASK_SCHEMA.get("additionalProperties") is False


class TestSummaryTaskSchema:
    """Tests for the summary task JSON schema"""

    def test_schema_is_valid_json_schema(self):
        """Summary task schema has valid JSON Schema structure"""
        assert SUMMARY_TASK_SCHEMA["type"] == "object"
        assert "properties" in SUMMARY_TASK_SCHEMA
        assert "required" in SUMMARY_TASK_SCHEMA

    def test_schema_has_required_properties(self):
        """Summary task schema has success and summary_content as required"""
        assert "success" in SUMMARY_TASK_SCHEMA["required"]
        assert "summary_content" in SUMMARY_TASK_SCHEMA["required"]

    def test_schema_has_success_property(self):
        """Summary task schema has success as boolean"""
        success_prop = SUMMARY_TASK_SCHEMA["properties"]["success"]
        assert success_prop["type"] == "boolean"

    def test_schema_has_error_message_property(self):
        """Summary task schema has error_message as optional string"""
        error_prop = SUMMARY_TASK_SCHEMA["properties"]["error_message"]
        assert error_prop["type"] == "string"
        assert "error_message" not in SUMMARY_TASK_SCHEMA["required"]

    def test_schema_has_summary_content_property(self):
        """Summary task schema has summary_content as required string"""
        content_prop = SUMMARY_TASK_SCHEMA["properties"]["summary_content"]
        assert content_prop["type"] == "string"
        assert "summary_content" in SUMMARY_TASK_SCHEMA["required"]

    def test_schema_disallows_additional_properties(self):
        """Summary task schema prevents extra properties"""
        assert SUMMARY_TASK_SCHEMA.get("additionalProperties") is False


class TestSchemaJsonSerialization:
    """Tests for schema JSON serialization functions"""

    def test_main_task_schema_json_is_valid_json(self):
        """get_main_task_schema_json returns valid JSON"""
        json_str = get_main_task_schema_json()
        parsed = json.loads(json_str)

        assert parsed == MAIN_TASK_SCHEMA

    def test_summary_task_schema_json_is_valid_json(self):
        """get_summary_task_schema_json returns valid JSON"""
        json_str = get_summary_task_schema_json()
        parsed = json.loads(json_str)

        assert parsed == SUMMARY_TASK_SCHEMA

    def test_main_task_schema_json_is_compact(self):
        """get_main_task_schema_json returns compact JSON without spaces"""
        json_str = get_main_task_schema_json()

        # Compact JSON has no spaces after colons or commas
        assert ": " not in json_str
        assert ", " not in json_str

    def test_summary_task_schema_json_is_compact(self):
        """get_summary_task_schema_json returns compact JSON without spaces"""
        json_str = get_summary_task_schema_json()

        # Compact JSON has no spaces after colons or commas
        assert ": " not in json_str
        assert ", " not in json_str
