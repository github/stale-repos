"""Unit tests for the markdown module."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

from markdown import write_to_markdown


class WriteToMarkdownTestCase(unittest.TestCase):
    """
    Unit test case for the write_to_markdown() function.
    """

    def test_write_to_markdown(self):
        """Test that the write_to_markdown function writes the expected data to a file.

        This test creates a list of inactive repos and a mock file object using
        MagicMock. It then calls the write_to_markdown function with the list of
        inactive repos and the mock file object. Finally, it uses the assert_has_calls
        method to check that the mock file object was called with the expected data.

        """
        forty_days_ago = datetime.now(timezone.utc) - timedelta(days=40)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        # Create an unsorted list of inactive repos
        inactive_repos = [
            {
                "url": "https://github.com/example/repo1",
                "days_inactive": 30,
                "last_push_date": thirty_days_ago.date().isoformat(),
                "visibility": "private",
                "days_since_last_release": None,
                "days_since_last_pr": None,
            },
            {
                "url": "https://github.com/example/repo2",
                "days_inactive": 40,
                "last_push_date": forty_days_ago.date().isoformat(),
                "visibility": "public",
                "days_since_last_release": None,
                "days_since_last_pr": None,
            },
        ]

        inactive_days_threshold = 365

        # Create a mock file object
        mock_file = MagicMock()

        # Call the write_to_markdown function with the mock file object
        write_to_markdown(
            inactive_repos,
            inactive_days_threshold,
            additional_metrics=["release", "pr"],
            file=mock_file,
        )

        # Check that the mock file object was called with the expected data
        expected_content = (
            "# Inactive Repositories\n\n"
            "The following repos have not had a push event for more than 365 days:\n\n"
            "| Repository URL | Days Inactive | Last Push Date | Visibility |"
            " Days Since Last Release | Days Since Last PR |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| https://github.com/example/repo2 | 40 | {forty_days_ago.date().isoformat()}"
            " | public | None | None |\n"
            f"| https://github.com/example/repo1 | 30 | {thirty_days_ago.date().isoformat()}"
            " | private | None | None |\n"
        )
        expected_calls = [
            call.write(expected_content),
        ]
        mock_file.__enter__.return_value.assert_has_calls(expected_calls)


class WriteToMarkdownWithWorkflowSummaryTestCase(unittest.TestCase):
    """
    Unit test case for the write_to_markdown() function with workflow summary enabled.
    """

    @patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": "/tmp/test_summary.md"})
    def test_write_to_markdown_with_workflow_summary_enabled(self):
        """Test that the write_to_markdown function writes to both file and workflow
        summary when enabled.

        This test creates a list of inactive repos and calls the write_to_markdown
        function with workflow_summary_enabled=True. It verifies that the content is
        written to both the regular file and the GitHub step summary file.

        """
        forty_days_ago = datetime.now(timezone.utc) - timedelta(days=40)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        # Create an unsorted list of inactive repos
        inactive_repos = [
            {
                "url": "https://github.com/example/repo1",
                "days_inactive": 30,
                "last_push_date": thirty_days_ago.date().isoformat(),
                "visibility": "private",
                "days_since_last_release": None,
                "days_since_last_pr": None,
            },
            {
                "url": "https://github.com/example/repo2",
                "days_inactive": 40,
                "last_push_date": forty_days_ago.date().isoformat(),
                "visibility": "public",
                "days_since_last_release": None,
                "days_since_last_pr": None,
            },
        ]

        inactive_days_threshold = 365

        # Create mock file objects
        mock_file = MagicMock()
        mock_summary_file = MagicMock()

        with patch("builtins.open", create=True) as mock_open:
            # Configure the mock to return different objects for different files
            def open_side_effect(
                filename, mode, **_kwargs
            ):  # pylint: disable=unused-argument
                if filename == "/tmp/test_summary.md":
                    return mock_summary_file
                return mock_file

            mock_open.side_effect = open_side_effect

            # Call the write_to_markdown function with workflow summary enabled
            write_to_markdown(
                inactive_repos,
                inactive_days_threshold,
                additional_metrics=["release", "pr"],
                workflow_summary_enabled=True,
            )

            # Check that both files were written to
            expected_content = (
                "# Inactive Repositories\n\n"
                "The following repos have not had a push event for more than 365 days:\n\n"
                "| Repository URL | Days Inactive | Last Push Date | Visibility |"
                " Days Since Last Release | Days Since Last PR |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                f"| https://github.com/example/repo2 | 40 | {forty_days_ago.date().isoformat()}"
                " | public | None | None |\n"
                f"| https://github.com/example/repo1 | 30 | {thirty_days_ago.date().isoformat()}"
                " | private | None | None |\n"
            )

            # Verify regular file was written
            mock_file.__enter__.return_value.write.assert_called_once_with(
                expected_content
            )
            # Verify summary file was written
            mock_summary_file.__enter__.return_value.write.assert_called_once_with(
                expected_content
            )

    def test_write_to_markdown_with_workflow_summary_disabled(self):
        """Test that when workflow_summary_enabled is False, only the regular file
        is written."""
        inactive_repos = [
            {
                "url": "https://github.com/example/repo1",
                "days_inactive": 30,
                "last_push_date": "2025-01-01",
                "visibility": "private",
            }
        ]

        # Create a mock file object
        mock_file = MagicMock()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value = mock_file

            # Call the write_to_markdown function with workflow summary disabled
            write_to_markdown(
                inactive_repos,
                365,
                workflow_summary_enabled=False,
            )

            # Verify only one file was opened (the regular stale_repos.md file)
            mock_open.assert_called_once_with("stale_repos.md", "w", encoding="utf-8")

    @patch.dict(os.environ, {}, clear=True)
    def test_write_to_markdown_with_workflow_summary_enabled_but_no_env_var(self):
        """Test that when GITHUB_STEP_SUMMARY is not set, only the regular file is written."""
        inactive_repos = [
            {
                "url": "https://github.com/example/repo1",
                "days_inactive": 30,
                "last_push_date": "2025-01-01",
                "visibility": "private",
            }
        ]

        # Create a mock file object
        mock_file = MagicMock()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value = mock_file

            # Call the write_to_markdown function with workflow summary enabled but no env var
            write_to_markdown(
                inactive_repos,
                365,
                workflow_summary_enabled=True,
            )

            # Verify only one file was opened (the regular stale_repos.md file)
            mock_open.assert_called_once_with("stale_repos.md", "w", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
