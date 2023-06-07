"""
Unit tests for the auth_to_github() function.

This module contains a set of unit tests to verify the behavior of the auth_to_github() function.
The function is responsible for connecting to GitHub.com or GitHub Enterprise,
depending on environment variables.

The tests cover different scenarios, such as successful authentication with both enterprise URL
and token, authentication with only a token, missing environment variables, and authentication
failures.

To run the tests, execute this module as the main script.

Example:
    $ pytest test_auth_to_github.py

"""

import io
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import github3.github

from stale_repos import (
    auth_to_github,
    get_inactive_repos,
    output_to_json,
    write_to_markdown,
)


class AuthToGithubTestCase(unittest.TestCase):
    """
    Unit test case for the auth_to_github() function.

    This test case class contains a set of individual test methods to verify the behavior
    of the auth_to_github() function. The function is responsible for connecting to
    GitHub.com or GitHub Enterprise based on environment variables.

    The test methods cover different scenarios, such as successful authentication with both
    enterprise URL and token, authentication with only a token, missing environment variables,
    and authentication failures.

    Test methods:
        - test_auth_to_github_with_enterprise_url_and_token: Tests authentication with both
          enterprise URL and token.
        - test_auth_to_github_with_token: Tests authentication with only a token.
        - test_auth_to_github_without_environment_variables: Tests authentication with
          missing environment variables.
        - test_auth_to_github_without_enterprise_url: Tests authentication without an
          enterprise URL.
        - test_auth_to_github_authentication_failure: Tests authentication failure.

    """

    @patch.dict(
        os.environ, {"GH_ENTERPRISE_URL": "https://example.com", "GH_TOKEN": "abc123"}
    )
    def test_auth_to_github_with_enterprise_url_and_token(self):
        """
        Test authentication with both enterprise URL and token.

        This test verifies that when both the GH_ENTERPRISE_URL and GH_TOKEN environment
        variables are set, the auth_to_github() function returns a connection object of
        type github3.github.GitHubEnterprise.

        """
        connection = auth_to_github()
        self.assertIsInstance(connection, github3.github.GitHubEnterprise)

    @patch.dict(os.environ, {"GH_TOKEN": "abc123"})
    def test_auth_to_github_with_token(self):
        """
        Test authentication with only a token.

        This test verifies that when only the GH_TOKEN environment variable is set,
        the auth_to_github() function returns a connection object of type github3.github.GitHub.

        """
        connection = auth_to_github()
        self.assertIsInstance(connection, github3.github.GitHub)

    @patch.dict(os.environ, {"GH_ENTERPRISE_URL": "", "GH_TOKEN": ""})
    def test_auth_to_github_without_environment_variables(self):
        """
        Test authentication with missing environment variables.

        This test verifies that when both the GH_ENTERPRISE_URL and GH_TOKEN environment
        variables are empty, the auth_to_github() function raises a ValueError.

        """
        with self.assertRaises(ValueError):
            auth_to_github()

    @patch("github3.login")
    def test_auth_to_github_without_enterprise_url(self, mock_login):
        """
        Test authentication without an enterprise URL.

        This test verifies that when the GH_ENTERPRISE_URL environment variable is empty,
        and the GH_TOKEN environment variable is set, the auth_to_github() function returns
        a connection object of type github3.github.GitHub.

        """
        mock_login.return_value = None
        with patch.dict(os.environ, {"GH_ENTERPRISE_URL": "", "GH_TOKEN": "abc123"}):
            with self.assertRaises(ValueError):
                auth_to_github()

    @patch("github3.login")
    def test_auth_to_github_authentication_failure(self, mock_login):
        """
        Test authentication failure.

        This test verifies that when the GH_ENTERPRISE_URL environment variable is empty,
        the GH_TOKEN environment variable is set, and the authentication process fails,
        the auth_to_github() function raises a ValueError.

        """
        mock_login.return_value = None
        with patch.dict(os.environ, {"GH_ENTERPRISE_URL": "", "GH_TOKEN": "abc123"}):
            with self.assertRaises(ValueError):
                auth_to_github()


class GetInactiveReposTestCase(unittest.TestCase):
    """
    Unit test case for the get_inactive_repos() function.

    This test case class verifies the behavior and correctness of the get_inactive_repos()
    function, which gets the URL and days inactive for repositories that exceed the
    specified threshold.

    ...

    Test methods:
        - test_print_inactive_repos_with_inactive_repos: Tests printing of inactive repos
          that exceed the threshold.
        - test_print_inactive_repos_with_no_inactive_repos: Tests printing of no inactive repos.

    """

    def setUp(self):
        """Set up the environment variables for the test case."""
        os.environ["EXEMPT_TOPICS"] = "topic1,topic2"

    def tearDown(self):
        """Tear down the environment variables for the test case."""
        del os.environ["EXEMPT_TOPICS"]

    def test_get_inactive_repos_with_inactive_repos(self):
        """Test that get_inactive_repos returns the expected list of inactive repos.

        This test uses a MagicMock object to simulate a GitHub API connection with a list
        of repositories with varying levels of inactivity. It then calls the get_inactive_repos
        function with the mock GitHub API connection and a threshold of 30 days. Finally, it
        checks that the function returns the expected list of inactive repos.

        """
        # Create a MagicMock object to simulate a GitHub API connection
        mock_github = MagicMock()

        # Create a MagicMock object to simulate the organization object returned by the
        # GitHub API connection
        mock_org = MagicMock()

        # Create MagicMock objects to simulate the repositories returned by the organization object
        forty_days_ago = datetime.now(timezone.utc) - timedelta(days=40)
        twenty_days_ago = datetime.now(timezone.utc) - timedelta(days=20)
        mock_repo1 = MagicMock(
            html_url="https://github.com/example/repo1",
            pushed_at=twenty_days_ago.isoformat(),
            archived=False,
        )
        mock_repo1.topics().names = []
        mock_repo2 = MagicMock(
            html_url="https://github.com/example/repo2",
            pushed_at=forty_days_ago.isoformat(),
            archived=False,
        )
        mock_repo2.topics().names = []
        mock_repo3 = MagicMock(
            html_url="https://github.com/example/repo3",
            pushed_at=forty_days_ago.isoformat(),
            archived=True,
        )
        mock_repo3.topics().names = []

        # Set up the MagicMock objects to return the expected values when called
        mock_github.organization.return_value = mock_org
        mock_org.repositories.return_value = [
            mock_repo1,
            mock_repo2,
            mock_repo3,
        ]

        # Call the get_inactive_repos function with the mock GitHub API
        # connection and a threshold of 30 days
        inactive_repos = get_inactive_repos(mock_github, 30, "example")

        # Check that the function returns the expected list of inactive repos
        expected_inactive_repos = [
            ("https://github.com/example/repo2", 40),
        ]
        assert inactive_repos == expected_inactive_repos

    def test_get_inactive_repos_with_no_inactive_repos(self):
        """Test getting with no inactive repos.

        This test verifies that the get_inactive_repos() function
        does not show anything when there are no repositories that
        exceed the specified threshold.

        """
        mock_github = MagicMock()
        mock_org = MagicMock()

        # Create a mock repository objects
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        mock_repo1 = MagicMock(
            pushed_at=thirty_days_ago.isoformat(),
            html_url="https://github.com/example/repo",
            archived=False,
        )
        mock_repo2 = MagicMock(
            pushed_at=None,
            html_url="https://github.com/example/repo2",
            archived=False,
        )

        mock_github.organization.return_value = mock_org
        mock_org.repositories.return_value = [
            mock_repo1,
            mock_repo2,
        ]

        # Call the function with a threshold of 40 days
        inactive_days_threshold = 40
        organization = "example"
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            get_inactive_repos(mock_github, inactive_days_threshold, organization)
            output = mock_stdout.getvalue()

        # Check that the output contains the expected repo URL and days inactive
        expected_output = (
            f"Exempt topics: ['topic1', 'topic2']\n"
            f"Found 0 stale repos in {organization}\n"
        )
        self.assertEqual(expected_output, output)

    def test_get_inactive_repos_with_exempt_topics(self):
        """Test that the get_inactive_repos function does not return exempt repos."""

        mock_github = MagicMock()
        mock_org = MagicMock()

        # create a mock repository with exempt topics
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        mock_repo1 = MagicMock(
            pushed_at=thirty_days_ago.isoformat(),
            html_url="https://github.com/example/repo",
            archived=False,
        )
        mock_repo1.topics().names = ["topic1", "topic2"]

        mock_repo2 = MagicMock(
            pushed_at=thirty_days_ago.isoformat(),
            html_url="https://github.com/example/repo2",
            archived=False,
        )
        mock_repo2.topics().names = ["topic3", "topic4"]

        mock_github.organization.return_value = mock_org
        mock_org.repositories.return_value = [
            mock_repo1,
            mock_repo2,
        ]

        # Call the function with a threshold of 20 days
        inactive_days_threshold = 20
        organization = "example"
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            get_inactive_repos(mock_github, inactive_days_threshold, organization)
            output = mock_stdout.getvalue()

        # Check that the output contains the expected repo URL and days inactive
        expected_output = (
            f"Exempt topics: ['topic1', 'topic2']\n"
            f"https://github.com/example/repo is exempt from stale repo check\n"
            f"https://github.com/example/repo2: 30 days inactive\n"
            f"Found 1 stale repos in {organization}\n"
        )
        self.assertEqual(expected_output, output)

    def test_get_inactive_repos_with_no_organization_set(self):
        """Test that get_inactive_repos returns the expected list of inactive repos
        when no organization is set.

        This test uses a MagicMock object to simulate a GitHub API connection with a list
        of repositories with varying levels of inactivity. It then calls the get_inactive_repos
        function with the mock GitHub API connection and a threshold of 30 days where
        organization is set to None. Finally, it checks that the function returns the
        expected list of inactive repos.

        """
        # Create a MagicMock object to simulate a GitHub API connection
        mock_github = MagicMock()

        # Create MagicMock objects to simulate the repositories returned by the organization object
        forty_days_ago = datetime.now(timezone.utc) - timedelta(days=40)
        twenty_days_ago = datetime.now(timezone.utc) - timedelta(days=20)
        mock_repo1 = MagicMock(
            html_url="https://github.com/example/repo1",
            pushed_at=twenty_days_ago.isoformat(),
            archived=False,
        )
        mock_repo1.topics().names = []
        mock_repo2 = MagicMock(
            html_url="https://github.com/example/repo2",
            pushed_at=forty_days_ago.isoformat(),
            archived=False,
        )
        mock_repo2.topics().names = []
        mock_repo3 = MagicMock(
            html_url="https://github.com/example/repo3",
            pushed_at=forty_days_ago.isoformat(),
            archived=True,
        )
        mock_repo3.topics().names = []

        # Set up the MagicMock objects to return the expected values when called
        mock_github.repositories.return_value = [
            mock_repo1,
            mock_repo2,
            mock_repo3,
        ]

        # Call the get_inactive_repos function with the mock GitHub API
        # connection and a threshold of 30 days
        inactive_repos = get_inactive_repos(mock_github, 30, None)

        # Check that the function returns the expected list of inactive repos
        expected_inactive_repos = [
            ("https://github.com/example/repo2", 40),
        ]
        assert inactive_repos == expected_inactive_repos


class WriteToMarkdownTestCase(unittest.TestCase):
    """
    Unit test case for the write_to_markdown() function.
    """

    def test_write_to_markdown(self):
        """Test that the write_to_markdown function writes the expected data to a file.

        This test creates a list of inactive repos and a mock file object using MagicMock.
        It then calls the write_to_markdown function with the list of inactive repos and
        the mock file object. Finally, it uses the assert_has_calls method to check that
        the mock file object was called with the expected data.

        """

        # Create a list of inactive repos
        inactive_repos = [
            ("https://github.com/example/repo2", 40),
            ("https://github.com/example/repo1", 30),
        ]

        inactive_days_threshold = 365

        # Create a mock file object
        mock_file = MagicMock()

        # Call the write_to_markdown function with the mock file object
        write_to_markdown(inactive_repos, inactive_days_threshold, file=mock_file)

        # Check that the mock file object was called with the expected data
        expected_calls = [
            call.write("# Inactive Repositories\n\n"),
            call.write(
                "The following repos have not had a push event for more than 365 days:\n\n"
            ),
            call.write("| Repository URL | Days Inactive |\n"),
            call.write("| --- | ---: |\n"),
            call.write("| https://github.com/example/repo2 | 40 |\n"),
            call.write("| https://github.com/example/repo1 | 30 |\n"),
        ]
        mock_file.__enter__.return_value.assert_has_calls(expected_calls)


class OutputToJson(unittest.TestCase):
    """
    Unit test case for the output_to_json() function.
    """

    def test_output_to_json(self):
        """Test that output_to_json returns the expected json string.

        This test creates a list of inactive repos and calls the
        output_to_json function with the list. It then checks that the
        function returns the expected json string.

        """
        # Create a list of inactive repos
        inactive_repos = [
            ("https://github.com/example/repo1", 31),
            ("https://github.com/example/repo2", 30),
            ("https://github.com/example/repo3", 29),
        ]

        # Call the output_to_json function with the list of inactive repos
        expected_json = json.dumps(
            [
                {"url": "https://github.com/example/repo1", "daysInactive": 31},
                {"url": "https://github.com/example/repo2", "daysInactive": 30},
                {"url": "https://github.com/example/repo3", "daysInactive": 29},
            ]
        )
        actual_json = output_to_json(inactive_repos)
        assert actual_json == expected_json
    
    def test_json_file(self):
        """Test that output_to_json writes JSON data to a file
        
        This test checks that output_to_json correctly writes its JSON data
        to a file named "stale_repos.json"
        """
        # Create a list of inactive repos
        inactive_repos = [
            ("https://github.com/example/repo1", 31),
            ("https://github.com/example/repo2", 30),
            ("https://github.com/example/repo3", 29),
        ]

        # Call the output_to_json function with the list of inactive repos
        expected_json = json.dumps(
            [
                {"url": "https://github.com/example/repo1", "daysInactive": 31},
                {"url": "https://github.com/example/repo2", "daysInactive": 30},
                {"url": "https://github.com/example/repo3", "daysInactive": 29},
            ]
        )

        mock_file = MagicMock()
         # Check that the mock file object was called with the expected data
        expected_calls = [
            call.write(expected_json),
        ]

        output_to_json(inactive_repos, mock_file)
        mock_file.__enter__.return_value.assert_has_calls(expected_calls)
        


if __name__ == "__main__":
    unittest.main()
