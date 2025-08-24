"""Markdown utilities for stale repository reporting."""

import os


def write_to_markdown(
    inactive_repos,
    inactive_days_threshold,
    additional_metrics=None,
    workflow_summary_enabled=False,
    file=None,
):
    """Write the list of inactive repos to a markdown file.

    Args:
        inactive_repos: A list of dictionaries containing the repo, days inactive,
            the date of the last push, repository visibility (public/private),
            days since the last release, and days since the last pr
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        additional_metrics: A list of additional metrics to include in the report.
        workflow_summary_enabled: If True, adds the report to GitHub Actions workflow summary.
        file: A file object to write to. If None, a new file will be created.

    """
    inactive_repos = sorted(
        inactive_repos, key=lambda x: x["days_inactive"], reverse=True
    )

    # Generate markdown content
    content = generate_markdown_content(
        inactive_repos, inactive_days_threshold, additional_metrics
    )

    # Write to file
    with file or open("stale_repos.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write(content)
    print("Wrote stale repos to stale_repos.md")

    # Write to GitHub step summary if enabled
    if workflow_summary_enabled and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(
            os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8"
        ) as summary_file:
            summary_file.write(content)
        print("Added stale repos to workflow summary")


def generate_markdown_content(
    inactive_repos, inactive_days_threshold, additional_metrics=None
):
    """Generate markdown content for the inactive repos report.

    Args:
        inactive_repos: A list of dictionaries containing the repo, days inactive,
            the date of the last push, repository visibility (public/private),
            days since the last release, and days since the last pr
        inactive_days_threshold: The threshold (in days) for considering a repo as inactive.
        additional_metrics: A list of additional metrics to include in the report.

    Returns:
        str: The generated markdown content.
    """
    content = "# Inactive Repositories\n\n"
    content += (
        f"The following repos have not had a push event for more than "
        f"{inactive_days_threshold} days:\n\n"
    )
    content += "| Repository URL | Days Inactive | Last Push Date | Visibility |"

    # Include additional metrics columns if configured
    if additional_metrics:
        if "release" in additional_metrics:
            content += " Days Since Last Release |"
        if "pr" in additional_metrics:
            content += " Days Since Last PR |"
    content += "\n| --- | --- | --- | --- |"
    if additional_metrics:
        if "release" in additional_metrics:
            content += " --- |"
        if "pr" in additional_metrics:
            content += " --- |"
    content += "\n"

    for repo_data in inactive_repos:
        content += (
            f"| {repo_data['url']} "
            f"| {repo_data['days_inactive']} "
            f"| {repo_data['last_push_date']} "
            f"| {repo_data['visibility']} |"
        )
        if additional_metrics:
            if "release" in additional_metrics:
                content += f" {repo_data['days_since_last_release']} |"
            if "pr" in additional_metrics:
                content += f" {repo_data['days_since_last_pr']} |"
        content += "\n"

    return content
