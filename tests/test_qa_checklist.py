import json
from pathlib import Path

import attr
import github3
import responses
from pytest_mock import MockerFixture
from pytest_regressions.file_regression import FileRegressionFixture

from qa_checklist import extract_issue_id
from qa_checklist import get_jira_issue_type
from qa_checklist import post_qa_comment


@responses.activate
def test_get_jira_issue_type(datadir: Path) -> None:
    response_data = json.loads((datadir / "response.json").read_text(encoding="UTF-8"))
    jira_url = "https://jira.com"
    issue_id = "SSRL-4612"

    responses.get(
        url=f"{jira_url}/rest/api/2/issue/{issue_id}",
        json=response_data,
    )

    issue_type = get_jira_issue_type(
        jira_url, issue_id, username="jira-bot", password="PASSWORD"
    )
    assert issue_type == "Story"


def test_post_qa_comment(
    mocker: MockerFixture, file_regression: FileRegressionFixture
) -> None:
    @attr.s(auto_attribs=True)
    class FakePullRequest:
        comment: str | None = None

        def create_comment(self, text: str) -> None:
            self.comment = text

    @attr.s(auto_attribs=True)
    class FakeGitHub:
        def __attrs_post_init__(self) -> None:
            self.pr = FakePullRequest()

        def pull_request(
            self, owner: str, repository: str, number: int
        ) -> FakePullRequest:
            assert owner == "ESSS"
            assert repository == "alfasim"
            assert number == 105
            return self.pr

    fake_gh = FakeGitHub()
    mocker.patch.object(github3, "login", return_value=fake_gh)

    post_qa_comment(
        ping_users=("user1", "user2"),
        reason="Because issue is of type Story.",
        token="GITHU_TOKEN",
        owner="ESSS",
        repository="alfasim",
        number=105,
    )
    assert fake_gh.pr.comment is not None
    file_regression.check(fake_gh.pr.comment)


def test_extract_issue_id() -> None:
    assert extract_issue_id("fb-XP-1023-foobar") == "XP-1023"
    assert extract_issue_id("fb_XP-1023_foobar") == "XP-1023"
    assert extract_issue_id("fb_xp-1023_foobar") is None
