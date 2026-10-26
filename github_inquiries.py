"""Create public Suro inquiry issues without exposing API credentials in errors."""

import os
import re
from urllib.parse import urlsplit

import requests


GITHUB_REPOSITORY = "Nikuyi-cnst/Suro-DiscordApp"
ISSUES_URL = f"https://github.com/{GITHUB_REPOSITORY}/issues"
API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
REQUEST_TIMEOUT = (5, 20)


class InquiryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _code_block(value: str) -> str:
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", value)), default=0))
    return f"{fence}\n{value}\n{fence}"


def _image_link(url: str) -> str:
    try:
        parsed = urlsplit(url)
    except ValueError:
        raise InquiryError("attachment", "첨부 이미지 링크를 확인할 수 없습니다. 이미지를 다시 첨부해주세요.") from None
    if (
        parsed.scheme != "https"
        or parsed.netloc not in {"cdn.discordapp.com", "media.discordapp.net"}
        or not parsed.path.startswith("/attachments/")
        or any(character.isspace() or ord(character) < 32 or character in '<>\\\"' for character in url)
    ):
        raise InquiryError("attachment", "첨부 이미지 링크를 확인할 수 없습니다. 이미지를 다시 첨부해주세요.")
    return f"![첨부 이미지](<{url}>)"


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    if (
        not token
        or not token.isascii()
        or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in token)
        or repository.casefold() != GITHUB_REPOSITORY.casefold()
    ):
        raise InquiryError(
            "configuration",
            "GitHub 문의 설정이 올바르지 않습니다. 봇 관리자에게 GITHUB_TOKEN과 GITHUB_REPOSITORY 설정 확인을 요청해주세요.",
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _check_status(response: requests.Response, expected: int, *, creating: bool = False) -> None:
    status = response.status_code
    if status == expected:
        return
    if status in {403, 429} and (
        status == 429
        or response.headers.get("X-RateLimit-Remaining") == "0"
        or "Retry-After" in response.headers
    ):
        raise InquiryError("rate_limit", "GitHub 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")
    if status in {401, 403, 404, 410}:
        raise InquiryError(
            "permissions",
            "GitHub 저장소 또는 이슈 작성 권한을 확인할 수 없습니다. 봇 관리자에게 문의해주세요.",
        )
    if creating and (status >= 500 or 200 <= status < 300):
        raise InquiryError(
            "uncertain",
            f"GitHub 이슈 생성 결과를 확인하지 못했습니다. 중복 접수 방지를 위해 먼저 {ISSUES_URL} 에서 확인해주세요.",
        )
    raise InquiryError("http", f"GitHub 문의 요청이 거절되었습니다 (HTTP {status}). 봇 관리자에게 문의해주세요.")


def _payload(response: requests.Response, *, creating: bool = False) -> dict:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if not isinstance(payload, dict):
        if creating:
            raise InquiryError("uncertain", f"이슈 생성 결과를 확인하지 못했습니다. 재접수 전에 {ISSUES_URL} 에서 확인해주세요.")
        raise InquiryError("response", "GitHub 저장소 정보를 확인할 수 없습니다. 잠시 후 다시 시도해주세요.")
    return payload


def create_inquiry_issue(content: str, display_name: str, image_url: str | None = None) -> str:
    """Return a verified issue URL. Never retry an ambiguous issue-creation request."""
    message = content.strip()
    if not message or len(message) > 1000:
        raise InquiryError("content", "문의 내용을 1~1000자로 입력해주세요.")
    body = f"### 문의 내용\n\n{_code_block(message)}\n\n### 작성자 표시 이름\n\n{_code_block(display_name)}"
    if image_url is not None:
        body += f"\n\n### 첨부 이미지\n\n{_image_link(image_url)}"
    headers = _headers()
    try:
        response = requests.get(API_URL, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=False)
    except requests.RequestException:
        raise InquiryError("network", "GitHub 저장소에 연결하지 못했습니다. 잠시 후 다시 시도해주세요.") from None
    _check_status(response, 200)
    repository = _payload(response)
    full_name = repository.get("full_name")
    if (
        repository.get("private") is not False
        or repository.get("visibility") != "public"
        or not isinstance(full_name, str)
        or full_name.casefold() != GITHUB_REPOSITORY.casefold()
        or repository.get("has_issues") is not True
        or repository.get("archived") is not False
    ):
        raise InquiryError(
            "repository",
            "공개 이슈를 접수할 수 있는 저장소가 아닙니다. 봇 관리자에게 공개 여부와 Issues 설정 확인을 요청해주세요.",
        )
    title = "[문의] " + " ".join(message.split()).replace("@", "@\u200b")[:100]
    try:
        response = requests.post(
            f"{API_URL}/issues",
            headers=headers,
            json={"title": title, "body": body},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise InquiryError(
            "uncertain",
            f"연결 오류로 이슈 생성 결과를 확인하지 못했습니다. 재접수 전에 {ISSUES_URL} 에서 확인해주세요.",
        ) from None
    _check_status(response, 201, creating=True)
    issue = _payload(response, creating=True)
    number = issue.get("number")
    expected_url = f"{ISSUES_URL}/{number}"
    if type(number) is not int or number <= 0 or issue.get("html_url") != expected_url:
        raise InquiryError("uncertain", f"이슈 생성 결과를 확인하지 못했습니다. 재접수 전에 {ISSUES_URL} 에서 확인해주세요.")
    return expected_url
