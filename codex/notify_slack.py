#!/usr/bin/env python3
"""Send concise Codex turn-completion notifications to Slack."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EVENT_TYPE = "agent-turn-complete"
ENV_PREFIX = "CODEX_SLACK_NOTIFY_"
WEBHOOK_ENV_VAR = f"{ENV_PREFIX}WEBHOOK_URL"
BOT_TOKEN_ENV_VAR = f"{ENV_PREFIX}BOT_TOKEN"
CHANNEL_ENV_VAR = f"{ENV_PREFIX}CHANNEL_ID"
PREVIEW_LENGTH_ENV_VAR = f"{ENV_PREFIX}PREVIEW_LENGTH"
SLACK_WEB_API_URL = "https://slack.com/api/chat.postMessage"
DEFAULT_PREVIEW_LENGTH = 200
MAX_PREVIEW_LENGTH = 1500
DETAIL_CHUNK_LENGTH = 3000


def escape_slack_text(value: object) -> str:
    """Escape characters that Slack treats as mrkdwn control characters."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def preview_text(value: object, limit: int) -> tuple[str, bool]:
    """Return a single-line preview and whether it was shortened."""
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + "...", True


def notification_request(notification: dict[str, Any]) -> str:
    messages = notification.get("input-messages")
    if isinstance(messages, list):
        parts = [
            message.strip() if isinstance(message, str) else json.dumps(message, ensure_ascii=False)
            for message in messages
        ]
        request = "\n\n".join(part for part in parts if part)
        return request or "Request unavailable."
    if messages:
        return str(messages).strip() or "Request unavailable."
    return "Request unavailable."


def git_output(cwd: str, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", cwd, *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=2,
    )
    return result.stdout.strip()


def project_context(cwd: str) -> tuple[str, str]:
    fallback_project = Path(cwd).name or cwd or "unknown"
    try:
        root = git_output(cwd, "rev-parse", "--show-toplevel")
        project = Path(root).name or fallback_project
        try:
            branch = git_output(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            commit = git_output(cwd, "rev-parse", "--short", "HEAD")
            branch = f"detached@{commit}"
        return project, branch
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return fallback_project, "-"


def escaped_chunks(value: str, limit: int = DETAIL_CHUNK_LENGTH) -> list[str]:
    """Escape Slack control characters and split without dropping content."""
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for character in value:
        escaped = escape_slack_text(character)
        if current and current_length + len(escaped) > limit:
            chunks.append("".join(current))
            current = []
            current_length = 0
        current.append(escaped)
        current_length += len(escaped)

    if current:
        chunks.append("".join(current))
    return chunks or [""]


def detail_messages(
    request: str,
    result: str,
    request_shortened: bool,
    result_shortened: bool,
) -> list[str]:
    sections: list[str] = []
    if request_shortened:
        sections.append(f"*Full Request:*\n{request}")
    if result_shortened:
        sections.append(f"*Full Result:*\n{result}")
    if not sections:
        return []

    chunks = escaped_chunks("\n\n".join(sections))
    if len(chunks) == 1:
        return chunks
    return [
        f"*Full details ({index}/{len(chunks)}):*\n{chunk}"
        for index, chunk in enumerate(chunks, start=1)
    ]


def build_messages(
    notification: dict[str, Any],
    preview_length: int,
    completed_at: str | None = None,
) -> tuple[str, list[str]]:
    cwd = str(notification.get("cwd") or "")
    project, branch = project_context(cwd)
    request = notification_request(notification)
    result = str(notification.get("last-assistant-message") or "Result unavailable.").strip()
    request_preview, request_shortened = preview_text(request, preview_length)
    result_preview, result_shortened = preview_text(result, preview_length)
    completed = completed_at or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    parent = "\n".join(
        (
            "✅ Codex task completed",
            f"Project: {escape_slack_text(project)}",
            f"Branch: {escape_slack_text(branch)}",
            f"Request: {escape_slack_text(request_preview)}",
            f"Result: {escape_slack_text(result_preview)}",
            f"Completed: {completed}",
        )
    )
    details = detail_messages(request, result, request_shortened, result_shortened)
    return parent, details


def preview_length_from_environment() -> int:
    raw_value = os.environ.get(PREVIEW_LENGTH_ENV_VAR)
    if raw_value is None:
        return DEFAULT_PREVIEW_LENGTH
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{PREVIEW_LENGTH_ENV_VAR} must be an integer") from error
    if not 1 <= value <= MAX_PREVIEW_LENGTH:
        raise ValueError(
            f"{PREVIEW_LENGTH_ENV_VAR} must be between 1 and {MAX_PREVIEW_LENGTH}"
        )
    return value


def post_to_webhook(webhook_url: str, message: str) -> None:
    body = json.dumps({"text": message}, ensure_ascii=False).encode("utf-8")
    request = Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        response_body = response.read().decode("utf-8", errors="replace").strip()
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Slack returned HTTP {response.status}")
        if response_body not in ("", "ok"):
            raise RuntimeError(f"Slack rejected the webhook request: {response_body}")


def post_to_slack_api(
    bot_token: str,
    channel: str,
    message: str,
    thread_ts: str | None = None,
) -> str:
    payload = {
        "channel": channel,
        "text": message,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    request = Request(
        SLACK_WEB_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        response_body = response.read().decode("utf-8", errors="replace")
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Slack returned HTTP {response.status}")

    try:
        result = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise RuntimeError("Slack API returned invalid JSON") from error
    if not isinstance(result, dict) or not result.get("ok"):
        api_error = (
            result.get("error", "unknown_error")
            if isinstance(result, dict)
            else "unknown_error"
        )
        raise RuntimeError(f"Slack API error: {api_error}")

    timestamp = result.get("ts")
    if not isinstance(timestamp, str) or not timestamp:
        raise RuntimeError("Slack API response did not include a message timestamp")
    return timestamp


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: codex-slack-notify '<notification-json>'", file=sys.stderr)
        return 2

    try:
        notification = json.loads(argv[1])
    except json.JSONDecodeError as error:
        print(f"codex-slack-notify: invalid notification JSON: {error}", file=sys.stderr)
        return 2

    if not isinstance(notification, dict):
        print("codex-slack-notify: notification must be a JSON object", file=sys.stderr)
        return 2

    if notification.get("type") != EVENT_TYPE:
        return 0

    try:
        parent, details = build_messages(notification, preview_length_from_environment())
        bot_token = os.environ.get(BOT_TOKEN_ENV_VAR)
        channel = os.environ.get(CHANNEL_ENV_VAR)
        webhook_url = os.environ.get(WEBHOOK_ENV_VAR)

        if bot_token and channel:
            parent_timestamp = post_to_slack_api(bot_token, channel, parent)
            for detail in details:
                post_to_slack_api(bot_token, channel, detail, thread_ts=parent_timestamp)
        elif webhook_url:
            if bot_token or channel:
                print(
                    f"codex-slack-notify: both {BOT_TOKEN_ENV_VAR} and {CHANNEL_ENV_VAR} "
                    "are required for thread replies; using the webhook fallback",
                    file=sys.stderr,
                )
            post_to_webhook(webhook_url, parent)
            if details:
                print(
                    "codex-slack-notify: preview was sent, but full details require "
                    f"{BOT_TOKEN_ENV_VAR} and {CHANNEL_ENV_VAR}",
                    file=sys.stderr,
                )
        else:
            print(
                f"codex-slack-notify: configure either {WEBHOOK_ENV_VAR}, or both "
                f"{BOT_TOKEN_ENV_VAR} and {CHANNEL_ENV_VAR}",
                file=sys.stderr,
            )
            return 2
    except (HTTPError, URLError, OSError, RuntimeError, ValueError) as error:
        print(f"codex-slack-notify: failed to send notification: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
