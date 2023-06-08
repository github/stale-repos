# Stale Repos Action
(Used by the `github` organization!)

This project identifies and reports repositories with no activity for configurable amount of time, in order to surface inactive repos to be considered for archival.
The current approach assumes that the repos that you want to evaluate are available in a single GitHub organization.
For the purpose of this action, a repository is considered inactive if it has not had a `push` in a configurable amount of days.

This action was developed by GitHub so that we can keep our open source projects well maintained, and it was made open source in the hopes that it would help you too!
We are actively using and are archiving things in batches since there are many repositories on our report.
To find out more about how GitHub manages its open source, check out the [github-ospo repository](https://github.com/github/github-ospo).

If you are looking to identify stale pull requests and issues, check out [actions/stale](https://github.com/actions/stale)

## Support

If you need support using this project or have questions about it, please [open up an issue in this repository](https://github.com/github/stale-repos/issues).
Requests made directly to GitHub staff or support team will be redirected here to open an issue.
GitHub SLA's and support/services contracts do not apply to this repository.

## Use as a GitHub Action

1. Create a repository to host this GitHub Action or select an existing repository.
1. Create the env values from the sample workflow below (GH_TOKEN, ORGANIZATION, EXEMPT_TOPICS) with your information as plain text or repository secrets. More info on creating secrets can be found [here](https://docs.github.com/en/actions/security-guides/encrypted-secrets).
Note: Your GitHub token will need to have read access to all the repositories in the organization that you want evaluated
1. Copy the below example workflow to your repository and put it in the `.github/workflows/` directory with the file extension `.yml` (ie. `.github/workflows/stale_repos.yml`)

### Configuration

Below are the allowed configuration options:

| field                 | required | default | description |
|-----------------------|----------|---------|-------------|
| `GH_TOKEN`            | true     |         | The GitHub Token used to scan repositories. Must have read access to all repositories you are interested in scanning. If you are writing to an issue, then the token you pass to that part of the workflow will need issue write permissions for repo where you run the workflow from. |
| `ORGANIZATION`        | false    |         | The organization to scan for stale repositories. If no organization is provided, this tool will search through repositories owned by the GH_TOKEN owner |
| `INACTIVE_DAYS`       | true     |         | The number of days used to determine if repository is stale, based on `push` events |
| `EXEMPT_TOPICS`       | false    |         | Comma separated list of topics to exempt from being flagged as stale |
| `GH_ENTERPRISE_URL`   | false    | `""`    | URL of GitHub Enterprise instance to use for auth instead of github.com |

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
        EXEMPT_TOPICS: "keep,template"
        INACTIVE_DAYS: 365

    - name: Create issue
      uses: peter-evans/create-issue-from-file@v4
      with:
        title: Stale repository report
        content-filepath: ./stale_repos.md
        assignees: <YOUR_GITHUB_HANDLE_HERE>
        token: ${{ secrets.GH_TOKEN }}

```

### Example stale_repos.md output

```markdown
# Inactive Repositories

The following repos have not had a push event for more than 3 days:

| Repository URL | Days Inactive |
| --- | ---: |
| https://github.com/github/.github | 5 |
```

### Using JSON instead of Markdown

The action outputs inactive repos in JSON format for further actions as seen below or use the JSON contents from the file: `stale_repos.json`.

Example usage:
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
      id: stale-repos
      uses: docker://ghcr.io/github/stale_repos:v1
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
        ORGANIZATION: ${{ secrets.ORGANIZATION }}
        EXEMPT_TOPICS: "keep,template"
        INACTIVE_DAYS: 365

    - name: Print output of stale_repos tool
      run: echo "${{ steps.stale-repos.outputs.inactiveRepos }}"
    - uses: actions/github-script@v6
      with:
        script: |
          const repos = ${{ steps.stale-repos.outputs.inactiveRepos }}
          for (const repo of repos) {
            console.log(repo);
            const issue = await github.rest.issues.create({
              owner: <ORG_OWNER>,
              repo: <REPOSITORY>,
              title: 'Stale repo' + repo.url,
              body: 'This repo is stale. Please contact the owner to make it active again.',
            });
            console.log(issue);
          }
        github-token: ${{ secrets.GH_TOKEN }}
```
## Local usage without Docker

1. Copy `.env-example` to `.env`
1. Fill out the `.env` file with a _token_ from a user that has access to the organization to scan (listed below). Tokens should have admin:org or read:org access.
1. Fill out the `.env` file with the desired _inactive_days_ value. This should be a whole positive number representing the amount of inactivity that you want for flagging stale repos.
1. (Optional) Fill out the `.env` file with the [repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics) _exempt_topics_ that you want to filter out from the stale repos report. This should be a comma separated list of topics.
1. (Optional) Fill out the `.env` file with the exact _organization_ that you want to search in
1. (Optional) Fill out the `.env` file with the exact _URL_ of the GitHub Enterprise that you want to search in. Keep empty if you want to search in the  public `github.com`.
1. `pip install -r requirements.txt`
1. Run `python3 ./stale_repos.py`, which will output a list of repositories and the length of their inactivity

## License

[MIT](LICENSE)
