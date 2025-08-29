"""A module for managing environment variables used in GitHub metrics calculation.

This module defines a class for encapsulating environment variables
and a function to retrieve these variables.

Functions:
    get_bool_env_var: Gets a boolean environment variable.
"""

import os
from os.path import dirname, join

from dotenv import load_dotenv


class EnvVars:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """
    Environment variables

    Attributes:
        gh_app_id (int | None): The GitHub App ID to use for authentication
        gh_app_installation_id (int | None): The GitHub App Installation ID to use for
            authentication
        gh_app_private_key_bytes (bytes): The GitHub App Private Key as bytes to use for
            authentication
        gh_token (str | None): GitHub personal access token (PAT) for API authentication
        ghe (str): The GitHub Enterprise URL to use for authentication
        skip_empty_reports (bool): If true, Skips report creation when no stale
            repositories are identified
        workflow_summary_enabled (bool): If true, adds the markdown report to GitHub
            Actions workflow summary
    """

    def __init__(
        self,
        gh_app_id: int | None,
        gh_app_installation_id: int | None,
        gh_app_private_key_bytes: bytes,
        gh_app_enterprise_only: bool,
        gh_token: str | None,
        ghe: str | None,
        skip_empty_reports: bool,
        workflow_summary_enabled: bool,
    ):
        self.gh_app_id = gh_app_id
        self.gh_app_installation_id = gh_app_installation_id
        self.gh_app_private_key_bytes = gh_app_private_key_bytes
        self.gh_app_enterprise_only = gh_app_enterprise_only
        self.gh_token = gh_token
        self.ghe = ghe
        self.skip_empty_reports = skip_empty_reports
        self.workflow_summary_enabled = workflow_summary_enabled

    def __repr__(self):
        return (
            f"EnvVars("
            f"{self.gh_app_id},"
            f"{self.gh_app_installation_id},"
            f"{self.gh_app_private_key_bytes},"
            f"{self.gh_app_enterprise_only},"
            f"{self.gh_token},"
            f"{self.ghe},"
            f"{self.skip_empty_reports},"
            f"{self.workflow_summary_enabled},"
        )


def get_bool_env_var(env_var_name: str, default: bool = False) -> bool:
    """Get a boolean environment variable.

    Args:
        env_var_name: The name of the environment variable to retrieve.
        default: The default value to return if the environment variable is not set.

    Returns:
        The value of the environment variable as a boolean.
    """
    ev = os.environ.get(env_var_name, "")
    if ev == "" and default:
        return default
    return ev.strip().lower() == "true"


def get_int_env_var(env_var_name: str) -> int | None:
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


def get_env_vars(
    test: bool = False,
) -> EnvVars:
    """
    get_env_vars: Gets the environment variables.

    Args:
        test: True if this is a test run; False otherwise.

    Returns:
        The environment variables.
    """

    if not test:
        # Load from .env file if it exists and not testing
        dotenv_path = join(dirname(__file__), ".env")
        load_dotenv(dotenv_path)

    gh_token = os.getenv("GH_TOKEN", "")
    gh_app_id = get_int_env_var("GH_APP_ID")
    gh_app_installation_id = get_int_env_var("GH_APP_INSTALLATION_ID")
    gh_app_private_key_bytes = os.getenv("GH_APP_PRIVATE_KEY", "").encode("utf8")
    ghe = os.getenv("GH_ENTERPRISE_URL")
    gh_app_enterprise_only = get_bool_env_var("GITHUB_APP_ENTERPRISE_ONLY")
    skip_empty_reports = get_bool_env_var("SKIP_EMPTY_REPORTS", True)
    workflow_summary_enabled = get_bool_env_var("WORKFLOW_SUMMARY_ENABLED")

    if gh_app_id and (not gh_app_private_key_bytes or not gh_app_installation_id):
        raise ValueError(
            "GH_APP_ID set and GH_APP_INSTALLATION_ID or GH_APP_PRIVATE_KEY variable not set"
        )

    if (
        not gh_app_id
        and not gh_app_private_key_bytes
        and not gh_app_installation_id
        and not gh_token
    ):
        raise ValueError("GH_TOKEN environment variable not set")

    return EnvVars(
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key_bytes,
        gh_app_enterprise_only,
        gh_token,
        ghe,
        skip_empty_reports,
        workflow_summary_enabled,
    )
