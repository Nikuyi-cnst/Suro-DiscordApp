import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import github_inquiries as github
with patch("dotenv.load_dotenv"):
    import Index


def response(status=200, payload=None, headers=None):
    result = Mock(spec=github.requests.Response)
    result.status_code = status
    result.headers = headers or {}
    result.json.return_value = payload
    return result


def public_repository(**overrides):
    return {
        "full_name": github.GITHUB_REPOSITORY,
        "private": False,
        "visibility": "public",
        "has_issues": True,
        "archived": False,
        **overrides,
    }


class GitHubInquiryTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "example-not-a-real-token", "GITHUB_REPOSITORY": github.GITHUB_REPOSITORY},
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.get = patch.object(github.requests, "get").start()
        self.post = patch.object(github.requests, "post").start()
        self.addCleanup(patch.stopall)
        self.get.return_value = response(payload=public_repository())
        self.post.return_value = response(201, {"number": 42, "html_url": f"{github.ISSUES_URL}/42"})

    def test_creates_public_issue_with_only_content_and_display_name(self):
        result = github.create_inquiry_issue("  문의 내용\n두 번째 줄  ", "작성자")

        self.assertEqual(result, f"{github.ISSUES_URL}/42")
        self.get.assert_called_once_with(
            github.API_URL,
            headers={
                "Authorization": "Bearer example-not-a-real-token",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=(5, 20),
            allow_redirects=False,
        )
        self.post.assert_called_once()
        arguments = self.post.call_args
        self.assertEqual(arguments.args, (f"{github.API_URL}/issues",))
        self.assertEqual(arguments.kwargs["timeout"], (5, 20))
        self.assertFalse(arguments.kwargs["allow_redirects"])
        self.assertEqual(arguments.kwargs["headers"], self.get.call_args.kwargs["headers"])
        payload = arguments.kwargs["json"]
        self.assertEqual(set(payload), {"title", "body"})
        self.assertEqual(payload["title"], "[문의] 문의 내용 두 번째 줄")
        self.assertEqual(
            payload["body"],
            "### 문의 내용\n\n```\n문의 내용\n두 번째 줄\n```\n\n### 작성자 표시 이름\n\n```\n작성자\n```",
        )

    def test_optional_image_is_included_without_download(self):
        url = "https://cdn.discordapp.com/attachments/111/222/image.png?ex=abc&hm=def"
        github.create_inquiry_issue("문의", "표시 이름", url)
        self.assertIn(f"![첨부 이미지](<{url}>)", self.post.call_args.kwargs["json"]["body"])

    def test_code_fences_cannot_be_broken_by_content_or_name(self):
        github.create_inquiry_issue("```\n@someone\n````", "```\n<script>test</script>")
        body = self.post.call_args.kwargs["json"]["body"]
        self.assertIn("`````\n```\n@someone\n````\n`````", body)
        self.assertIn("````\n```\n<script>test</script>\n````", body)

    def test_title_is_bounded_single_line_and_does_not_mention_users(self):
        github.create_inquiry_issue("@someone\n" + "긴" * 990, "작성자")
        title = self.post.call_args.kwargs["json"]["title"]
        self.assertLessEqual(len(title), 105)
        self.assertNotIn("\n", title)
        self.assertNotIn("@someone", title)

    def test_invalid_content_is_rejected_before_network_calls(self):
        for content in ("", " \n ", "a" * 1001):
            with self.subTest(content_length=len(content)), self.assertRaises(github.InquiryError):
                github.create_inquiry_issue(content, "작성자")
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_exact_content_limit_is_accepted(self):
        github.create_inquiry_issue("가" * 1000, "작성자")
        self.post.assert_called_once()

    def test_missing_or_invalid_configuration_never_sends_requests(self):
        configurations = (
            {"GITHUB_TOKEN": ""},
            {"GITHUB_TOKEN": "invalid\nheader"},
            {"GITHUB_TOKEN": "비밀"},
            {"GITHUB_REPOSITORY": ""},
            {"GITHUB_REPOSITORY": "other/repository"},
            {"GITHUB_REPOSITORY": "https://evil.invalid"},
        )
        for configuration in configurations:
            with self.subTest(configuration=list(configuration)), patch.dict(os.environ, configuration):
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, "configuration")
                self.assertNotIn("example-not-a-real-token", str(captured.exception))
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_non_public_wrong_archived_or_disabled_repository_never_receives_issue(self):
        overrides = (
            {"private": True},
            {"visibility": "private"},
            {"has_issues": False},
            {"archived": True},
            {"full_name": "other/repository"},
            {"full_name": None},
            {"private": None},
        )
        for values in overrides:
            with self.subTest(values=values):
                self.get.return_value = response(payload=public_repository(**values))
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, "repository")
        self.post.assert_not_called()

    def test_rejects_invalid_or_foreign_attachment_links(self):
        for url in (
            "http://cdn.discordapp.com/attachments/1/2/a.png",
            "https://evil.invalid/a.png",
            "https://cdn.discordapp.com@evil.invalid/attachments/1/2/a.png",
            "https://cdn.discordapp.com/attachments/a.png>bad",
            "https://cdn.discordapp.com/attachments/a\nbad",
            "https://[invalid",
        ):
            with self.subTest(url=url), self.assertRaises(github.InquiryError) as captured:
                github.create_inquiry_issue("문의", "작성자", url)
            self.assertEqual(captured.exception.code, "attachment")
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_repository_http_errors_do_not_post_or_expose_response_body(self):
        for status in (301, 401, 403, 404, 410, 422, 429, 500):
            with self.subTest(status=status):
                self.get.return_value = response(status, {"message": "example-not-a-real-token"})
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertNotIn("example-not-a-real-token", str(captured.exception))
        self.post.assert_not_called()

    def test_creation_http_errors_are_not_retried(self):
        for status, expected in ((302, "http"), (401, "permissions"), (403, "permissions"),
                                 (422, "http"), (429, "rate_limit"), (500, "uncertain"), (200, "uncertain")):
            with self.subTest(status=status):
                self.post.reset_mock()
                self.post.return_value = response(status)
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, expected)
                self.post.assert_called_once()

    def test_rate_limit_headers_are_respected(self):
        for headers in ({"X-RateLimit-Remaining": "0"}, {"Retry-After": "60"}):
            with self.subTest(headers=headers):
                self.post.return_value = response(403, headers=headers)
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, "rate_limit")

    def test_network_errors_are_sanitized_and_post_failures_are_ambiguous(self):
        for error in (github.requests.Timeout, github.requests.ConnectionError, github.requests.exceptions.InvalidHeader):
            with self.subTest(error=error):
                self.get.side_effect = error("example-not-a-real-token")
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, "network")
                self.assertNotIn("example-not-a-real-token", str(captured.exception))
                self.post.assert_not_called()
        self.get.side_effect = None
        self.post.side_effect = github.requests.Timeout("example-not-a-real-token")
        with self.assertRaises(github.InquiryError) as captured:
            github.create_inquiry_issue("문의", "작성자")
        self.assertEqual(captured.exception.code, "uncertain")
        self.assertIn(github.ISSUES_URL, str(captured.exception))
        self.assertNotIn("example-not-a-real-token", str(captured.exception))
        self.post.assert_called_once()

    def test_bad_json_and_incomplete_responses_are_not_success(self):
        for payload in (None, [], {}, {"private": False}):
            with self.subTest(repository_payload=payload):
                self.get.return_value = response(payload=payload)
                with self.assertRaises(github.InquiryError):
                    github.create_inquiry_issue("문의", "작성자")
        self.get.return_value = response()
        self.get.return_value.json.side_effect = ValueError("example-not-a-real-token")
        with self.assertRaises(github.InquiryError):
            github.create_inquiry_issue("문의", "작성자")
        self.post.assert_not_called()
        self.get.return_value = response(payload=public_repository())
        for payload in (None, [], {}, {"number": True}, {"number": -1},
                        {"number": 42, "html_url": "https://evil.invalid/issues/42"}):
            with self.subTest(issue_payload=payload):
                self.post.return_value = response(201, payload)
                with self.assertRaises(github.InquiryError) as captured:
                    github.create_inquiry_issue("문의", "작성자")
                self.assertEqual(captured.exception.code, "uncertain")
        self.post.return_value = response(201)
        self.post.return_value.json.side_effect = ValueError("example-not-a-real-token")
        with self.assertRaises(github.InquiryError) as captured:
            github.create_inquiry_issue("문의", "작성자")
        self.assertEqual(captured.exception.code, "uncertain")


class InquiryCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.interaction = SimpleNamespace(
            user=SimpleNamespace(id=123456789, display_name="공개 표시 이름"),
            guild_id=987654321,
            guild=SimpleNamespace(name="비공개 서버"),
            response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            client=SimpleNamespace(fetch_user=AsyncMock()),
        )

    async def submit(self, content="문의 내용", attachment=None):
        await Index.inquiry_command.callback(cast(Index.discord.Interaction, self.interaction), content, attachment)

    async def test_no_attachment_is_optional_and_uses_display_name_only(self):
        with patch.object(Index, "create_inquiry_issue", return_value=f"{github.ISSUES_URL}/42") as create:
            await self.submit()
        create.assert_called_once_with("문의 내용", "공개 표시 이름", None)
        self.interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        self.interaction.response.send_message.assert_not_awaited()
        self.interaction.followup.send.assert_awaited_once_with(
            f"문의가 GitHub 공개 이슈로 등록되었습니다.\n{github.ISSUES_URL}/42", ephemeral=True,
        )
        self.interaction.client.fetch_user.assert_not_awaited()

    async def test_valid_image_url_is_passed_without_downloading(self):
        attachment = SimpleNamespace(
            content_type="image/png",
            url="https://cdn.discordapp.com/attachments/1/2/a.png",
            to_file=AsyncMock(),
        )
        with patch.object(Index, "create_inquiry_issue", return_value=f"{github.ISSUES_URL}/42") as create:
            await self.submit("  내용  ", attachment)
        create.assert_called_once_with("내용", "공개 표시 이름", attachment.url)
        attachment.to_file.assert_not_awaited()

    async def test_bad_content_is_rejected_before_defer_or_github(self):
        with patch.object(Index, "create_inquiry_issue") as create:
            for content in (" \n", "a" * 1001):
                with self.subTest(length=len(content)):
                    await self.submit(content)
        create.assert_not_called()
        self.interaction.response.defer.assert_not_awaited()
        self.assertEqual(self.interaction.response.send_message.await_count, 2)
        self.interaction.followup.send.assert_not_awaited()

    async def test_non_image_and_missing_content_type_are_rejected(self):
        with patch.object(Index, "create_inquiry_issue") as create:
            for content_type in ("text/plain", None):
                await self.submit(attachment=SimpleNamespace(content_type=content_type))
        create.assert_not_called()
        self.interaction.response.defer.assert_not_awaited()
        self.assertEqual(self.interaction.response.send_message.await_count, 2)

    async def test_failure_is_logged_safely_and_never_reported_as_success(self):
        with (
            patch.object(Index, "create_inquiry_issue", side_effect=github.InquiryError("permissions", "권한 확인 필요")),
            self.assertLogs(Index.logger, level="WARNING") as logs,
        ):
            await self.submit("민감한 문의")
        self.interaction.followup.send.assert_awaited_once_with("권한 확인 필요", ephemeral=True)
        output = "\n".join(logs.output)
        self.assertIn("code=permissions", output)
        self.assertNotIn("민감한 문의", output)
        self.assertNotIn("example-not-a-real-token", output)

    def test_command_metadata_says_public_and_attachment_is_not_required(self):
        parameters = {parameter.name: parameter for parameter in Index.inquiry_command.parameters}
        self.assertTrue(parameters["content"].required)
        self.assertFalse(parameters["attachment"].required)
        self.assertIn("공개", Index.inquiry_command.description)
        self.assertIn("선택", parameters["attachment"].description)
        self.assertIn("公開", Index.Help_Message_JPN)
        self.assertIn("선택", Index.Help_Message_KOR)


if __name__ == "__main__":
    unittest.main()
