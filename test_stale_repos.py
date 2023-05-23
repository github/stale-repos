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
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import github3.github
from stale_repos import auth_to_github, print_inactive_repos


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


class PrintInactiveReposTestCase(unittest.TestCase):
    """
    Unit test case for the print_inactive_repos() function.

    This test case class verifies the behavior and correctness of the print_inactive_repos()
    function, which prints the URL and days inactive for repositories that exceed the
    specified threshold.

    ...

    Test methods:
        - test_print_inactive_repos_with_inactive_repos: Tests printing of inactive repos
          that exceed the threshold.
        - test_print_inactive_repos_with_no_inactive_repos: Tests printing of no inactive repos.

    """

    def test_print_inactive_repos_with_inactive_repos(self):
        """Test printing inactive repos that exceed the threshold.

        This test verifies that the print_inactive_repos() function correctly prints the URL and
        days inactive for repositories that have been inactive for more than the specified
        threshold.

        """
        # Create a mock GitHub connection object
        github_connection = MagicMock()

        # Create a mock repository object with a last push time of 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mock_repo = MagicMock()
        mock_repo.pushed_at = thirty_days_ago.isoformat()
        mock_repo.html_url = "https://github.com/example/repo"
        github_connection.repositories_by.return_value = [mock_repo]

        # Call the function with a threshold of 20 days
        inactive_days_threshold = 20
        organization = "example"
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_inactive_repos(
                github_connection, inactive_days_threshold, organization
            )
            output = mock_stdout.getvalue()

        # Check that the output contains the expected repo URL and days inactive
        expected_output = f"{mock_repo.html_url}: 30 days inactive\nFound 1 stale repos in {organization}\n"
        self.assertEqual(expected_output, output)

    def test_print_inactive_repos_with_no_inactive_repos(self):
        """Test printing no inactive repos.

        This test verifies that the print_inactive_repos() function
        does not print anything when there are no repositories that
        exceed the specified threshold.

        """
        github_connection = MagicMock()

        # Create a mock repository object with a last push time of 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mock_repo = MagicMock()
        mock_repo.pushed_at = thirty_days_ago.isoformat()
        mock_repo.html_url = "https://github.com/example/repo"
        github_connection.repositories_by.return_value = [mock_repo]

        # Call the function with a threshold of 40 days
        inactive_days_threshold = 40
        organization = "example"
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_inactive_repos(
                github_connection, inactive_days_threshold, organization
            )
            output = mock_stdout.getvalue()

        # Check that the output contains the expected repo URL and days inactive
        expected_output = f"Found 0 stale repos in {organization}\n"
        self.assertEqual(expected_output, output)


if __name__ == "__main__":
    unittest.main()
