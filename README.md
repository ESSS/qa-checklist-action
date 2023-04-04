# qa-checklist-action

Action to make QA checks in PRs.

When a pull request is opened or reopened, we check if the JIRA issue associated with the branch is of
type `Story` -- if that's the case, we post a new comment containing a check-list of QA tasks that need
to be done in order to merge the PR.

To configure, add a new workflow in `.github/workflows`, configuring it like this:

```yaml
name: qa-checklist

on:
  pull_request:
     types: [opened, reopened]


jobs:
  qa-checklist:
    runs-on: ubuntu-latest

    steps:
      - uses: ESSS/qa-checklist-action@v1
        with:
          # jira_url is optional, defaulting to the URL below.
          jira_url: https://eden.esss.co/jira
          jira_username: ${{ secrets.JIRA_BOT_USER }}
          jira_password: ${{ secrets.JIRA_BOT_PASSWORD }}
          github_token: ${{ secrets.EDEN_GITHUB_TOKEN }}
          ping_users: user1,user2
```
