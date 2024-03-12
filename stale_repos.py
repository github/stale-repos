#!/usr/bin/env python
""" Find stale repositories in a GitHub organization. """
import fnmatch
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
    if exempt_repos and any(
        fnmatch.fnmatchcase(repo.name, pattern) for pattern in exempt_repos
    ):
        print(f"{repo.html_url} is exempt from stale repo check")
        return True
    try:
        if exempt_topics and any(
            topic in exempt_topics for topic in repo.topics().names
        ):
            print(f"{repo.html_url} is exempt from stale repo check")
            return True
    except github3.exceptions.NotFoundError as error_code:
        if error_code.code == 404:
            print(
                f"{repo.html_url} does not have topics enabled and may be a private temporary fork"
            )

    return False


def get_inactive_repos(github_connection, inactive_days_threshold, organization):
    """Return and print out the repo url and days inactive if it's over
       the threshold (inactive_days).

    Args:
        github_connection: The GitHub connection object.
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        organization: The name of the organization to retrieve repositories from.

    Returns:
        A list of tuples containing the repo, days inactive, the date of the last push and
        repository visibility (public/private).

    """
    inactive_repos = []
    if organization:
        repos = github_connection.organization(organization).repositories()
    else:
        repos = github_connection.repositories(type="owner")

    exempt_topics = os.getenv("EXEMPT_TOPICS")
    if exempt_topics:
        exempt_topics = exempt_topics.replace(" ", "").split(",")
        print(f"Exempt topics: {exempt_topics}")

    exempt_repos = os.getenv("EXEMPT_REPOS")
    if exempt_repos:
        exempt_repos = exempt_repos.replace(" ", "").split(",")
        print(f"Exempt repos: {exempt_repos}")

    for repo in repos:
        # check if repo is exempt from stale repo check
        if is_repo_exempt(repo, exempt_repos, exempt_topics):
            continue

        # Get last active date
        active_date = get_active_date(repo)
        if active_date is None:
            continue

        active_date_disp = active_date.date().isoformat()
        days_inactive = (datetime.now(timezone.utc) - active_date).days
        visibility = "private" if repo.private else "public"
        if days_inactive > int(inactive_days_threshold) and not repo.archived:
            inactive_repos.append(
                (repo.html_url, days_inactive, active_date_disp, visibility)
            )
            print(f"{repo.html_url}: {days_inactive} days inactive")  # type: ignore
    if organization:
        print(f"Found {len(inactive_repos)} stale repos in {organization}")
    else:
        print(f"Found {len(inactive_repos)} stale repos")
    return inactive_repos


def get_active_date(repo):
    """Get the last activity date of the repository.

    Args:
        repo: A Github repository object.

    Returns:
        A date object representing the last activity date of the repository.
    """
    activity_method = os.getenv("ACTIVITY_METHOD", "pushed").lower()
    try:
        if activity_method == "default_branch_updated":
            commit = repo.branch(repo.default_branch).commit
            active_date = parse(commit.commit.as_dict()["committer"]["date"])
        elif activity_method == "pushed":
            last_push_str = repo.pushed_at  # type: ignored
            if last_push_str is None:
                return None
            active_date = parse(last_push_str)
        else:
            raise ValueError(
                f"""
                ACTIVITY_METHOD environment variable has unsupported value: '{activity_method}'.
                Allowed values are: 'pushed' and 'default_branch_updated'
                """
            )
    except github3.exceptions.GitHubException:
        print(f"{repo.html_url} had an exception trying to get the activity date.")
        return None
    return active_date


def write_to_markdown(inactive_repos, inactive_days_threshold, file=None):
    """Write the list of inactive repos to a markdown file.

    Args:
        inactive_repos: A list of tuples containing the repo, days inactive,
            the date of the last push, and repository visibility (public/private).
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        file: A file object to write to. If None, a new file will be created.

    """
    inactive_repos.sort(key=lambda x: x[1], reverse=True)
    with file or open("stale_repos.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write("# Inactive Repositories\n\n")
        markdown_file.write(
            f"The following repos have not had a push event for more than "
            f"{inactive_days_threshold} days:\n\n"
        )
        markdown_file.write(
            "| Repository URL | Days Inactive | Last Push Date | Visibility |\n"
        )
        markdown_file.write("| --- | --- | --- | ---: |\n")
        for repo_url, days_inactive, last_push_date, visibility in inactive_repos:
            markdown_file.write(
                f"| {repo_url} | {days_inactive} | {last_push_date} | {visibility} |\n"
            )
    print("Wrote stale repos to stale_repos.md")


def output_to_json(inactive_repos, file=None):
    """Convert the list of inactive repos to a json string.

    Args:
        inactive_repos: A list of tuples containing the repo,
            days inactive, the date of the last push, and
            visiblity of the repository (public/private).

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
    for repo_url, days_inactive, last_push_date, visibility in inactive_repos:
        inactive_repos_json.append(
            {
                "url": repo_url,
                "daysInactive": days_inactive,
                "lastPushDate": last_push_date,
                "visibility": visibility,
            }
        )
    inactive_repos_json = json.dumps(inactive_repos_json)

    # add output to github action output
    # pylint: disable=unspecified-encoding
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as file_handle:
            print(f"inactiveRepos={inactive_repos_json}", file=file_handle)

    with file or open("stale_repos.json", "w", encoding="utf-8") as json_file:
        json_file.write(inactive_repos_json)

    print("Wrote stale repos to stale_repos.json")

    return inactive_repos_json


def get_int_env_var(env_var_name):
    """Get an integer environment variable.

    Args:
        env_var_name: The name of the environment variable to retrieve.

    Returns:
        The value of the environment variable as an integer or None.
    """
    env_var = os.environ.get(env_var_name)
    if env_var is None or not env_var.strip():
        return None
    try:
        return int(env_var)
    except ValueError:
        return None


def auth_to_github():
    """Connect to GitHub.com or GitHub Enterprise, depending on env variables."""
    gh_app_id = get_int_env_var("GH_APP_ID")
    gh_app_private_key_bytes = os.environ.get("GH_APP_PRIVATE_KEY", "").encode("utf8")
    gh_app_installation_id = get_int_env_var("GH_APP_INSTALLATION_ID")
    ghe = os.getenv("GH_ENTERPRISE_URL", default="").strip()
    token = os.getenv("GH_TOKEN")

    if gh_app_id and gh_app_private_key_bytes and gh_app_installation_id:
        gh = github3.github.GitHub()
        gh.login_as_app_installation(
            gh_app_private_key_bytes, gh_app_id, gh_app_installation_id
        )
        github_connection = gh
    elif ghe and token:
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
