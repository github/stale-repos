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

import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

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
        github_connection = Mock()
        organization = "example"
        inactive_days_threshold = 30

        repo1 = Mock()
        repo1.pushed_at = (datetime.now() - timedelta(days=40)).isoformat()
        repo1.html_url = "https://github.com/example/repo1"
        repo2 = Mock()
        repo2.pushed_at = (datetime.now() - timedelta(days=20)).isoformat()
        repo2.html_url = "https://github.com/example/repo2"
        repo3 = Mock()
        repo3.pushed_at = None
        repo3.html_url = "https://github.com/example/repo3"

        github_connection.repositories_by.return_value = [repo1, repo2, repo3]

        expected_output = [
            f"{repo1.html_url}: 40 days inactive",
        ]

        with unittest.mock.patch("builtins.print") as mock_print:  # type: ignore
            print_inactive_repos(
                github_connection, inactive_days_threshold, organization
            )

            mock_print.assert_called_once_with("\n".join(expected_output))

    def test_print_inactive_repos_with_no_inactive_repos(self):
        """Test printing no inactive repos.

        This test verifies that the print_inactive_repos() function
        does not print anything when there are no repositories that
        exceed the specified threshold.

        """
        github_connection = Mock()
        organization = "example"
        inactive_days_threshold = 30

        repo1 = Mock()
        repo1.pushed_at = (datetime.now() - timedelta(days=20)).isoformat()
        repo2 = Mock()
        repo2.pushed_at = (datetime.now() - timedelta(days=10)).isoformat()

        github_connection.repositories_by.return_value = [repo1, repo2]

        with unittest.mock.patch("builtins.print") as mock_print:  # type: ignore
            print_inactive_repos(
                github_connection, inactive_days_threshold, organization
            )

            mock_print.assert_not_called()


if __name__ == "__main__":
    unittest.main()
