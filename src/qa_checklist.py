import argparse
import re
import sys
from typing import Sequence

import github3
import requests


def get_jira_issue_type(
    jira_url: str, issue_id: str, username: str, password: str
) -> str:
    """Gets the issue type of the given JIRA issue, as a string."""
    auth = (username, password)
    resp = requests.get(jira_url + f"/rest/api/2/issue/{issue_id}", auth=auth)
    resp.raise_for_status()
    return resp.json()["fields"]["issuetype"]["name"]


def post_qa_comment(
    *,
    ping_users: Sequence[str],
    reason: str,
    token: str,
    owner: str,
    repository: str,
    number: int,
) -> None:
    """Post a comment indicating that manual QA is required."""
    gh = github3.login(token=token)
    pr = gh.pull_request(owner, repository, number)
    lines = [
        "## QA Check ##",
        "",
        reason,
        "",
        "- [ ] Manual QA required.",
        "",
        "cc " + ", ".join(f"@{x}" for x in ping_users) + ".",
    ]
    text = "\n".join(lines)
    pr.create_comment(text)


def extract_issue_id(branch: str) -> str | None:
    """
    Given a branch name, extract a JIRA issue id from there, or None if could not find a matching
    issue schema.
    """
    if m := re.search(r"([A-Z]+-\d+)", branch):
        return m.group(1)
    else:
        return None


def entry_point(
    *,
    branch: str,
    ping_users: Sequence[str],
    token: str,
    owner: str,
    repository: str,
    number: int,
    jira_url: str,
    jira_username: str,
    jira_password: str,
) -> None:
    """Main job of this action."""
    issue_id = extract_issue_id(branch)
    print(f"Branch: {branch}")
    print(f"Issue: {issue_id}")
    if issue_id is None:
        print("Could not extract an issue from branch name, quitting...")
        return

    issue_type = get_jira_issue_type(
        jira_url=jira_url,
        issue_id=issue_id,
        username=jira_username,
        password=jira_password,
    )
    print(f"Issue type: {issue_type}")
    if issue_type != "Story":
        print("Not a Story, quitting...")
        return

    reason = (
        f"Issue {issue_id} is of type {issue_type}, so we require manual QA to be done."
    )
    print(f"About to post to {owner}/{repository}, PR#{number}")
    post_qa_comment(
        ping_users=ping_users,
        reason=reason,
        token=token,
        owner=owner,
        repository=repository,
        number=number,
    )
    print("Posted successfully.")


def main(argv: Sequence[str]) -> None:
    """Main function, we extract all arguments and pass them along entry_point()."""
    parser = argparse.ArgumentParser()
    parser.add_argument("branch")
    parser.add_argument("ping_users")
    parser.add_argument("token")
    parser.add_argument("jira_url")
    parser.add_argument("jira_username")
    parser.add_argument("jira_password")
    parser.add_argument("slug")
    parser.add_argument("number", type=int)
    ns = parser.parse_args(argv[1:])
    owner, repository = ns.slug.split("/")
    entry_point(
        branch=ns.branch,
        ping_users=tuple(x.strip() for x in ns.ping_users.split(",")),
        token=ns.token,
        owner=owner,
        repository=repository,
        number=ns.number,
        jira_url=ns.jira_url,
        jira_username=ns.jira_username,
        jira_password=ns.jira_password,
    )


if __name__ == "__main__":
    main(sys.argv)
