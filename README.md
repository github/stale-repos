# Stale Repos Action

This project identifies and reports repositories with no activity for configurable amount of time, in order to surface inactive repos to be considered for archival. The current approach assumes that the repos that you want to evaluate are available in a single GitHub organization.

## Support

If you need support using this project or have questions about it, please [open up an issue in this repository](https://github.com/github/stale_repos/issues). Requests made directly to GitHub staff or support team will be redirected here to open an issue. GitHub SLA's and support/services contracts do not apply to this repository.

## Use as a GitHub Action

1. Create a repository to host this GitHub Action or select an existing repository.
1. Create the env values from the sample workflow below (GH_TOKEN, ORGANIZATION) with your information as repository secrets. More info on creating secrets can be found [here](https://docs.github.com/en/actions/security-guides/encrypted-secrets).
Note: Your GitHub token will need to have read/write access to all the repositories in the organization that you want evaluated
1. Copy the below example workflow to your repository and put it in the `.github/workflows/` directory with the file extension `.yml` (ie. `.github/workflows/stale_repos.yml`)

### Example workflow

```yaml
name: stale repo identifier

on:
  workflow_dispatch:
  schedule:
    - cron: '3 2 1 * *'

jobs:
  build:
    name: stale repo identifier
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Run stale_repos tool
      uses: docker://ghcr.io/github/stale_repos:v1
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
        ORGANIZATION: ${{ secrets.ORGANIZATION }}
        INACTIVE_DAYS: 365

    - name: Create issue
      uses: peter-evans/create-issue-from-file@v4
      with:
        title: Stale repository report
        content-filepath: ./stale_repos.md
        assignees: <YOUR_GITHUB_HANDLE_HERE>

```

### Example stale_repos.md output

```markdown
# Inactive Repositories

| Repository URL | Days Inactive |
| --- | ---: |
| https://github.com/github/.github | 5 |
```

## Local usage without Docker

1. Copy `.env-example` to `.env`
1. Fill out the `.env` file with a _token_ from a user that has access to the organization to scan (listed below). Tokens should have admin:org or read:org access.
1. Fill out the `.env` file with the desired _inactive_days_ value. This should be a whole positive number representing the amount of inactivity that you want for flagging stale repos.
1. Fill out the `.env` file with the exact _organization_ that you want to search in
1. (Optional) Fill out the `.env` file with the exact _URL_ of the GitHub Enterprise that you want to search in. Keep empty if you want to search in the  public `github.com`.
1. `pip install -r requirements.txt`
1. Run `python3 ./stale_repos.py`, which will output a list of repositories and the length of their inactivity

## License

[MIT](LICENSE)
