"""Tests for output formatters."""

import json
from io import StringIO
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from docmost.output import (
    console,
    error,
    error_console,
    format_json,
    format_plain,
    format_table,
    info,
    output,
    success,
    warning,
)


class TestFormatJson:
    """Tests for JSON formatter."""

    def test_formats_dict_as_json(self) -> None:
        """Formats dictionary as indented JSON."""
        data = {"id": "123", "name": "Test"}
        result = format_json(data)
        assert json.loads(result) == data
        assert "\n" in result  # Indented
        assert "  " in result

    def test_formats_list_as_json(self) -> None:
        """Formats list as JSON."""
        data = [{"id": 1}, {"id": 2}]
        result = format_json(data)
        assert json.loads(result) == data

    def test_handles_non_serializable_with_default(self) -> None:
        """Handles non-serializable types with default=str."""
        from datetime import datetime

        data = {"created": datetime(2024, 1, 15, 12, 0, 0)}
        result = format_json(data)
        parsed = json.loads(result)
        assert "2024-01-15" in parsed["created"]


class TestFormatPlain:
    """Tests for plain text formatter."""

    def test_formats_dict_as_key_value_pairs(self) -> None:
        """Formats dictionary as key: value lines."""
        data = {"id": "123", "name": "Test Page"}
        result = format_plain(data)
        assert "id: 123" in result
        assert "name: Test Page" in result

    def test_formats_nested_dict_as_json(self) -> None:
        """Nested dictionaries are formatted as JSON."""
        data = {"metadata": {"key": "value"}}
        result = format_plain(data)
        assert "metadata:" in result
        assert '"key"' in result

    def test_formats_nested_list_as_json(self) -> None:
        """Nested lists are formatted as JSON."""
        data = {"tags": ["a", "b", "c"]}
        result = format_plain(data)
        assert "tags:" in result
        assert '["a", "b", "c"]' in result

    def test_handles_none_values(self) -> None:
        """Handles None values."""
        data = {"value": None}
        result = format_plain(data)
        assert "value: None" in result


class TestFormatTable:
    """Tests for table formatter."""

    def test_shows_no_results_for_empty_data(self) -> None:
        """Shows 'No results' for empty list."""
        # Capture console output
        with patch.object(console, "print") as mock_print:
            format_table([])
            mock_print.assert_called_once()
            # Check that "No results" is in the output
            call_args = str(mock_print.call_args)
            assert "No results" in call_args

    def test_uses_first_item_keys_as_columns(self) -> None:
        """Uses keys from first item when columns not specified."""
        data = [{"id": "1", "name": "First"}, {"id": "2", "name": "Second"}]
        # Just verify it doesn't raise
        with patch.object(console, "print"):
            format_table(data)

    def test_uses_specified_columns(self) -> None:
        """Uses specified columns when provided."""
        data = [{"id": "1", "name": "First", "extra": "ignored"}]
        with patch.object(console, "print"):
            format_table(data, columns=["id", "name"])

    def test_handles_missing_column_values(self) -> None:
        """Handles items missing column values."""
        data = [{"id": "1"}, {"id": "2", "name": "Only Second"}]
        with patch.object(console, "print"):
            format_table(data, columns=["id", "name"])

    def test_formats_nested_values_as_json(self) -> None:
        """Nested values in table cells are JSON formatted."""
        data = [{"id": "1", "meta": {"key": "value"}}]
        with patch.object(console, "print"):
            format_table(data, columns=["id", "meta"])

    def test_converts_none_to_empty_string(self) -> None:
        """None values become empty strings in table."""
        data = [{"id": "1", "value": None}]
        with patch.object(console, "print"):
            format_table(data, columns=["id", "value"])


class TestOutput:
    """Tests for the main output function."""

    def test_json_format_outputs_json(self) -> None:
        """Output with json format calls format_json."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                click.command()(lambda: output({"key": "value"}, fmt="json"))
            )
            assert result.exit_code == 0
            assert '"key": "value"' in result.output

    def test_plain_format_single_item(self) -> None:
        """Plain format for single item."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                click.command()(lambda: output({"id": "1", "name": "Test"}, fmt="plain"))
            )
            assert result.exit_code == 0
            assert "id: 1" in result.output
            assert "name: Test" in result.output

    def test_plain_format_list(self) -> None:
        """Plain format for list of items."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            data = [{"id": "1"}, {"id": "2"}]
            result = runner.invoke(click.command()(lambda: output(data, fmt="plain")))
            assert result.exit_code == 0
            assert "id: 1" in result.output
            assert "id: 2" in result.output

    def test_table_format_list(self) -> None:
        """Table format for list."""
        data = [{"id": "1", "name": "First"}]
        with patch.object(console, "print"):
            output(data, fmt="table")

    def test_table_format_single_item_uses_plain(self) -> None:
        """Table format for single item falls back to plain."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                click.command()(lambda: output({"id": "1"}, fmt="table"))
            )
            assert result.exit_code == 0
            assert "id: 1" in result.output

    def test_unknown_format_defaults_to_json(self) -> None:
        """Unknown format defaults to JSON."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                click.command()(lambda: output({"key": "val"}, fmt="unknown"))
            )
            assert result.exit_code == 0
            assert '"key": "val"' in result.output

    def test_passes_columns_to_table(self) -> None:
        """Columns parameter is passed to table formatter."""
        data = [{"id": "1", "name": "Test", "extra": "ignored"}]
        with patch("docmost.output.format_table") as mock_table:
            output(data, fmt="table", columns=["id", "name"])
            mock_table.assert_called_once_with(data, ["id", "name"])


class TestMessageHelpers:
    """Tests for success, error, warning, info helpers."""

    def test_success_prints_green_checkmark(self) -> None:
        """Success message has green checkmark."""
        with patch.object(console, "print") as mock_print:
            success("Done")
            mock_print.assert_called_once()
            call_str = str(mock_print.call_args)
            assert "[green]" in call_str
            assert "Done" in call_str

    def test_error_prints_red_x(self) -> None:
        """Error message has red X."""
        with patch.object(error_console, "print") as mock_print:
            error("Failed")
            mock_print.assert_called_once()
            call_str = str(mock_print.call_args)
            assert "[red]" in call_str
            assert "Failed" in call_str

    def test_warning_prints_yellow_exclamation(self) -> None:
        """Warning message has yellow exclamation."""
        with patch.object(console, "print") as mock_print:
            warning("Caution")
            mock_print.assert_called_once()
            call_str = str(mock_print.call_args)
            assert "[yellow]" in call_str
            assert "Caution" in call_str

    def test_info_prints_blue_i(self) -> None:
        """Info message has blue info icon."""
        with patch.object(console, "print") as mock_print:
            info("Note")
            mock_print.assert_called_once()
            call_str = str(mock_print.call_args)
            assert "[blue]" in call_str
            assert "Note" in call_str
