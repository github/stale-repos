#!/usr/bin/env python
""" Find stale repositories in a GitHub organization. """

import os
from datetime import datetime
from os.path import dirname, join

import github3
from dateutil.parser import parse
from dotenv import load_dotenv


def main():
    """
    Iterate over all repositories in the specified organization on GitHub,
    calculate the number of days since each repository was last pushed to,
    and print out the URL of any repository that has been inactive for more
    days than the specified threshold.

    The following environment variables must be set:
    - GH_TOKEN: a personal access token for the GitHub API
    - INACTIVE_DAYS: the number of days after which a repository is considered stale
    - ORGANIZATION: the name of the organization to search for repositories in

    If GH_ENTERPRISE_URL is set, the script will authenticate to a GitHub Enterprise
    instance instead of GitHub.com.
    """
    # Load env variables from file
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    # Auth to GitHub.com
    github_connection = auth_to_github()

    # Set the threshold for inactive days
    inactive_days_threshold = os.getenv("INACTIVE_DAYS")
    if not inactive_days_threshold:
        raise ValueError("INACTIVE_DAYS environment variable not set")

    # Set the organization
    organization = os.getenv("ORGANIZATION")
    if not organization:
        raise ValueError("ORGANIZATION environment variable not set")

    # Iterate over repos in the org, acquire inactive days,
    # and print out the repo url and days inactive if it's over the threshold (inactive_days)
    print_inactive_repos(github_connection, inactive_days_threshold, organization)


def print_inactive_repos(github_connection, inactive_days_threshold, organization):
    """Print out the repo url and days inactive if it's over the threshold (inactive_days).

    Args:
        github_connection: The GitHub connection object.
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        organization: The name of the organization to retrieve repositories from.

    """
    for repo in github_connection.repositories_by(organization):
        last_push_str = repo.pushed_at  # type: ignore
        if last_push_str is None:
            continue
        last_push = parse(last_push_str)
        days_inactive = (datetime.now() - last_push).days
        if days_inactive > int(inactive_days_threshold):
            print(f"{repo.html_url}: {days_inactive} days inactive")  # type: ignore


def auth_to_github():
    """Connect to GitHub.com or GitHub Enterprise, depending on env variables."""
    ghe = os.getenv("GH_ENTERPRISE_URL", default="").strip()
    token = os.getenv("GH_TOKEN")
    if ghe and token:
        github_connection = github3.github.GitHubEnterprise(ghe, token=token)
    elif token:
        github_connection = github3.login(token=os.getenv("GH_TOKEN"))
    else:
        raise ValueError("GH_TOKEN environment variable not set")

    if not github_connection:
        raise ValueError("Unable to authenticate to GitHub")
    return github_connection  # type: ignore


if __name__ == "__main__":
    main()
