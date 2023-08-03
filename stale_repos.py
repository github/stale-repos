#!/usr/bin/env python
""" Find stale repositories in a GitHub organization. """

import json
import os
from datetime import datetime, timezone
from os.path import dirname, join

import github3
from dateutil.parser import parse
from dotenv import load_dotenv


def main():  # pragma: no cover
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
    print("Starting stale repo search...")

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
        print(
            "ORGANIZATION environment variable not set, searching all repos owned by token owner"
        )

    # Iterate over repos in the org, acquire inactive days,
    # and print out the repo url and days inactive if it's over the threshold (inactive_days)
    inactive_repos = get_inactive_repos(
        github_connection, inactive_days_threshold, organization
    )

    if inactive_repos:
        output_to_json(inactive_repos)
        write_to_markdown(inactive_repos, inactive_days_threshold)
    else:
        print("No stale repos found")


def is_repo_exempt(repo, exempt_repos, exempt_topics):
    """Check if a repo is exempt from the stale repo check.

    Args:
        repo: The repository to check.
        exempt_repos: A list of repos to exempt from the stale repo check.
        exempt_topics: A list of topics to exempt from the stale repo check.

    Returns:
        True if the repo is exempt from the stale repo check, False otherwise.
    """
    if exempt_repos and any(repo.name == exempt_repo for exempt_repo in exempt_repos):
        print(f"{repo.html_url} is exempt from stale repo check")
        return True
    if exempt_topics and any(topic in exempt_topics for topic in repo.topics().names):
        print(f"{repo.html_url} is exempt from stale repo check")
        return True
    return False


def get_inactive_repos(github_connection, inactive_days_threshold, organization):
    """Return and print out the repo url and days inactive if it's over
       the threshold (inactive_days).

    Args:
        github_connection: The GitHub connection object.
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        organization: The name of the organization to retrieve repositories from.

    Returns:
        A list of tuples containing the repo, days inactive, and the date of the last push.

    """
    inactive_repos = []
    if organization:
        repos = github_connection.organization(organization).repositories()
    else:
        repos = github_connection.repositories(type="owner")

    exempt_topics = os.getenv("EXEMPT_TOPICS")
    if exempt_topics:
        exempt_topics = exempt_topics.split(",")
        print(f"Exempt topics: {exempt_topics}")

    exempt_repos = os.getenv("EXEMPT_REPOS")
    if exempt_repos:
        exempt_repos = exempt_repos.split(",")
        print(f"Exempt repos: {exempt_repos}")

    for repo in repos:
        # check if repo is exempt from stale repo check
        if is_repo_exempt(repo, exempt_repos, exempt_topics):
            continue

        # Get last push date
        last_push_str = repo.pushed_at  # type: ignore
        if last_push_str is None:
            continue
        last_push = parse(last_push_str)
        last_push_disp_date = last_push.date().isoformat()

        days_inactive = (datetime.now(timezone.utc) - last_push).days
        if days_inactive > int(inactive_days_threshold) and not repo.archived:
            inactive_repos.append((repo.html_url, days_inactive, last_push_disp_date))
            print(f"{repo.html_url}: {days_inactive} days inactive")  # type: ignore
    if organization:
        print(f"Found {len(inactive_repos)} stale repos in {organization}")
    else:
        print(f"Found {len(inactive_repos)} stale repos")
    return inactive_repos


def write_to_markdown(inactive_repos, inactive_days_threshold, file=None):
    """Write the list of inactive repos to a markdown file.

    Args:
        inactive_repos: A list of tuples containing the repo, days inactive,
            and the date of the last push.
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        file: A file object to write to. If None, a new file will be created.

    """
    inactive_repos.sort(key=lambda x: x[1], reverse=True)
    with file or open("stale_repos.md", "w", encoding="utf-8") as file:
        file.write("# Inactive Repositories\n\n")
        file.write(
            f"The following repos have not had a push event for more than "
            f"{inactive_days_threshold} days:\n\n"
        )
        file.write("| Repository URL | Days Inactive | Last Push Date |\n")
        file.write("| --- | --- | ---: |\n")
        for repo_url, days_inactive, last_push_date in inactive_repos:
            file.write(f"| {repo_url} | {days_inactive} | {last_push_date} |\n")
    print("Wrote stale repos to stale_repos.md")


def output_to_json(inactive_repos, file=None):
    """Convert the list of inactive repos to a json string.

    Args:
        inactive_repos: A list of tuples containing the repo,
            days inactive, and the date of the last push.

    Returns:
        JSON formatted string of the list of inactive repos.

    """
    # json structure is like following
    # [
    #   {
    #     "url": "https://github.com/owner/repo",
    #     "daysInactive": 366,
    #     "lastPushDate": "2020-01-01"
    #   }
    # ]
    inactive_repos_json = []
    for repo_url, days_inactive, last_push_date in inactive_repos:
        inactive_repos_json.append(
            {
                "url": repo_url,
                "daysInactive": days_inactive,
                "lastPushDate": last_push_date,
            }
        )
    inactive_repos_json = json.dumps(inactive_repos_json)

    # add output to github action output
    # pylint: disable=unspecified-encoding
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as file_handle:
            print(f"inactiveRepos={inactive_repos_json}", file=file_handle)

    with file or open("stale_repos.json", "w", encoding="utf-8") as file:
        file.write(inactive_repos_json)

    print("Wrote stale repos to stale_repos.json")

    return inactive_repos_json


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
