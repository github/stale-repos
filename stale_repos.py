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

import auth


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

    token = os.getenv("GH_TOKEN")
    gh_app_id = os.getenv("GH_APP_ID")
    gh_app_installation_id = os.getenv("GH_APP_INSTALLATION_ID")
    gh_app_private_key = os.getenv("GH_APP_PRIVATE_KEY").encode("utf8")
    ghe = os.getenv("GH_ENTERPRISE_URL")
    gh_app_enterprise_only = os.getenv("GITHUB_APP_ENTERPRISE_ONLY")

    # Auth to GitHub.com or GHE
    github_connection = auth.auth_to_github(
        token,
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key,
        ghe,
        gh_app_enterprise_only,
    )

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

    # Fetch additional metrics configuration
    additional_metrics = os.getenv("ADDITIONAL_METRICS", "").split(",")

    # Iterate over repos in the org, acquire inactive days,
    # and print out the repo url and days inactive if it's over the threshold (inactive_days)
    inactive_repos = get_inactive_repos(
        github_connection, inactive_days_threshold, organization, additional_metrics
    )

    if inactive_repos:
        output_to_json(inactive_repos)
        write_to_markdown(inactive_repos, inactive_days_threshold, additional_metrics)
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


def get_inactive_repos(
    github_connection, inactive_days_threshold, organization, additional_metrics=None
):
    """Return and print out the repo url and days inactive if it's over
       the threshold (inactive_days).

    Args:
        github_connection: The GitHub connection object.
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        organization: The name of the organization to retrieve repositories from.
        additional_metrics: A list of additional metrics to include in the report.

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
        if repo.archived:
            continue
        if is_repo_exempt(repo, exempt_repos, exempt_topics):
            continue

        # Get last active date
        active_date = get_active_date(repo)
        if active_date is None:
            continue

        active_date_disp = active_date.date().isoformat()
        days_inactive = (datetime.now(timezone.utc) - active_date).days
        visibility = "private" if repo.private else "public"
        if days_inactive > int(inactive_days_threshold):
            repo_data = set_repo_data(
                repo, days_inactive, active_date_disp, visibility, additional_metrics
            )
            inactive_repos.append(repo_data)
    if organization:
        print(f"Found {len(inactive_repos)} stale repos in {organization}")
    else:
        print(f"Found {len(inactive_repos)} stale repos")
    return inactive_repos


def get_days_since_last_release(repo):
    """Get the number of days since the last release of the repository.

    Args:
        repo: A Github repository object.

    Returns:
        The number of days since the last release.
    """
    try:
        last_release = next(repo.releases())
        return (datetime.now(timezone.utc) - last_release.created_at).days
    except StopIteration:
        return None


def get_days_since_last_pr(repo):
    """Get the number of days since the last pull request was made in the repository.

    Args:
        repo: A Github repository object.

    Returns:
        The number of days since the last pull request was made.
    """
    try:
        last_pr = next(repo.pull_requests(state="all"))
        return (datetime.now(timezone.utc) - last_pr.created_at).days
    except StopIteration:
        return None


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
        print(
            f"{repo.html_url} had an exception trying to get the activity date.\
 Potentially caused by ghost user."
        )
        return None
    return active_date


def write_to_markdown(
    inactive_repos, inactive_days_threshold, additional_metrics=None, file=None
):
    """Write the list of inactive repos to a markdown file.

    Args:
        inactive_repos: A list of dictionaries containing the repo, days inactive,
            the date of the last push, repository visibility (public/private),
            days since the last release, and days since the last pr
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        additional_metrics: A list of additional metrics to include in the report.
        file: A file object to write to. If None, a new file will be created.

    """
    inactive_repos = sorted(
        inactive_repos, key=lambda x: x["days_inactive"], reverse=True
    )
    with file or open("stale_repos.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write("# Inactive Repositories\n\n")
        markdown_file.write(
            f"The following repos have not had a push event for more than "
            f"{inactive_days_threshold} days:\n\n"
        )
        markdown_file.write(
            "| Repository URL | Days Inactive | Last Push Date | Visibility |"
        )
        # Include additional metrics columns if configured
        if additional_metrics:
            if "release" in additional_metrics:
                markdown_file.write(" Days Since Last Release |")
            if "pr" in additional_metrics:
                markdown_file.write(" Days Since Last PR |")
        markdown_file.write("\n| --- | --- | --- | --- |")
        if additional_metrics:
            if "release" in additional_metrics:
                markdown_file.write(" --- |")
            if "pr" in additional_metrics:
                markdown_file.write(" --- |")
        markdown_file.write("\n")
        for repo_data in inactive_repos:
            markdown_file.write(
                f"| {repo_data['url']} \
| {repo_data['days_inactive']} \
| {repo_data['last_push_date']} \
| {repo_data['visibility']} |"
            )
            if additional_metrics:
                if "release" in additional_metrics:
                    markdown_file.write(f" {repo_data['days_since_last_release']} |")
                if "pr" in additional_metrics:
                    markdown_file.write(f" {repo_data['days_since_last_pr']} |")
            markdown_file.write("\n")
    print("Wrote stale repos to stale_repos.md")


def output_to_json(inactive_repos, file=None):
    """Convert the list of inactive repos to a json string.

    Args:
        inactive_repos: A list of dictionaries containing the repo,
            days inactive, the date of the last push,
            visiblity of the repository (public/private),
            days since the last release, and days since the last pr.

    Returns:
        JSON formatted string of the list of inactive repos.

    """
    # json structure is like following
    # [
    #   {
    #     "url": "https://github.com/owner/repo",
    #     "daysInactive": 366,
    #     "lastPushDate": "2020-01-01"
    #     "daysSinceLastRelease": "5"
    #     "daysSinceLastPR": "10"
    #   }
    # ]
    # Instead of looping through an array and then using json dump
    # why not just   inactive_repos_json = json.dumps(inactive_repos)
    # and then remove line 323-335 NOTE: FOR ADAM AND BORIS
    inactive_repos_json = []
    for repo_data in inactive_repos:
        repo_json = {
            "url": repo_data["url"],
            "daysInactive": repo_data["days_inactive"],
            "lastPushDate": repo_data["last_push_date"],
            "visibility": repo_data["visibility"],
        }
        if "release" in repo_data:
            repo_json["daysSinceLastRelease"] = repo_data["days_since_last_release"]
        if "pr" in repo_data:
            repo_json["daysSinceLastPR"] = repo_data["days_since_last_pr"]
        inactive_repos_json.append(repo_json)
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


def set_repo_data(
    repo, days_inactive, active_date_disp, visibility, additional_metrics
):
    """
    Constructs a dictionary with repository data
    including optional metrics based on additional metrics specified.

    Args:
        repo: The repository object.
        days_inactive: Number of days the repository has been inactive.
        active_date_disp: The display string of the last active date.
        visibility: The visibility status of the repository (e.g., private or public).
        additional_metrics: A list of strings indicating which additional metrics to include.

    Returns:
        A dictionary with the repository data.
    """
    repo_data = {
        "url": repo.html_url,
        "days_inactive": days_inactive,
        "last_push_date": active_date_disp,
        "visibility": visibility,
    }
    # Fetch and include additional metrics if configured
    repo_data["days_since_last_release"] = None
    repo_data["days_since_last_pr"] = None
    repo_data["committer"] = get_committer(repo)
    repo_data["owner"] = get_owner(repo)
    if additional_metrics:
        if "release" in additional_metrics:
            try:
                repo_data["days_since_last_release"] = get_days_since_last_release(repo)
            except github3.exceptions.GitHubException:
                print(
                    f"{repo.html_url} had an exception trying to get the last release.\
 Potentially caused by ghost user."
                )
        if "pr" in additional_metrics:
            try:
                repo_data["days_since_last_pr"] = get_days_since_last_pr(repo)
            except github3.exceptions.GitHubException:
                print(
                    f"{repo.html_url} had an exception trying to get the last PR.\
 Potentially caused by ghost user."
                )
    print(f"{repo.html_url}: {days_inactive} days inactive")  # type: ignore
    return repo_data


def get_committer(repo):
    """Get the committer of the last commit on the default branch.

    Args:
        repo: A Github repository object.

    Returns:
        A dictionary with the committer's name and email.
    """
    try:
        commit = repo.branch(repo.default_branch).commit
        return {"login": commit.author.login}
    except github3.exceptions.GitHubException:
        print(f"{repo.html_url} had an exception trying to get the committer.")
        return None


def get_owner(repo):
    """Get the owner of the repository.

    Args:
        repo: A Github repository object.

    Returns:
        A dictionary with the owner's name and email.
    """
    try:
        owner = repo.owner
        return {"name": owner.name, "email": owner.email}
    except github3.exceptions.GitHubException:
        print(f"{repo.html_url} had an exception trying to get the owner.")
        return None


if __name__ == "__main__":
    main()
