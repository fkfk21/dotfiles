#!/usr/bin/env python3
"""Send concise Codex turn-completion notifications to Slack."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
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
RECENT_SUBAGENT_WINDOW_SECONDS = 600


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    texts = [
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    return "\n".join(text for text in texts if text).strip()


def session_metadata(transcript_path: Path) -> dict[str, Any] | None:
    try:
        with transcript_path.open(encoding="utf-8") as transcript:
            first_line = transcript.readline()
    except OSError:
        return None

    try:
        record = json.loads(first_line)
    except json.JSONDecodeError:
        return None
    if not isinstance(record, dict) or record.get("type") != "session_meta":
        return None
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else None


def is_luna_worker_metadata(metadata: dict[str, Any]) -> bool:
    if metadata.get("agent_role") == "luna_worker":
        return True
    source = metadata.get("source")
    if not isinstance(source, dict):
        return False
    subagent = source.get("subagent")
    if not isinstance(subagent, dict):
        return False
    spawn = subagent.get("thread_spawn")
    return isinstance(spawn, dict) and spawn.get("agent_role") == "luna_worker"


def reversed_transcript_records(
    transcript_path: Path,
) -> Iterator[dict[str, Any]]:
    try:
        with transcript_path.open("rb") as transcript:
            transcript.seek(0, os.SEEK_END)
            position = transcript.tell()
            remainder = b""
            while position:
                chunk_size = min(position, 64 * 1024)
                position -= chunk_size
                transcript.seek(position)
                lines = (transcript.read(chunk_size) + remainder).split(b"\n")
                remainder = lines[0]
                for line in reversed(lines[1:]):
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(record, dict):
                        yield record
            if remainder:
                try:
                    record = json.loads(remainder)
                except json.JSONDecodeError:
                    return
                if isinstance(record, dict):
                    yield record
    except OSError:
        return


def latest_transcript_message(transcript_path: Path, role: str) -> str:
    for record in reversed_transcript_records(transcript_path):
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if (
            isinstance(payload, dict)
            and payload.get("type") == "message"
            and payload.get("role") == role
        ):
            return message_text(payload)
    return ""


def notification_from_stop_hook(hook: dict[str, Any]) -> dict[str, Any] | None:
    if hook.get("hook_event_name") != "Stop":
        return None

    transcript_value = hook.get("transcript_path")
    transcript_path = (
        Path(transcript_value) if isinstance(transcript_value, str) else None
    )
    if transcript_path is not None:
        metadata = session_metadata(transcript_path)
        if metadata is not None:
            source = metadata.get("source")
            if metadata.get("thread_source") in {"subagent", "guardian_review"} or (
                isinstance(source, dict) and "subagent" in source
            ):
                return None
        request = latest_transcript_message(transcript_path, "user")
    else:
        request = ""

    return {
        "type": EVENT_TYPE,
        "cwd": hook.get("cwd"),
        "input-messages": [request or "Request unavailable."],
        "last-assistant-message": hook.get("last_assistant_message"),
    }


def codex_sessions_directory() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home) if codex_home else Path.home() / ".codex") / "sessions"


def session_paths_for_id(sessions_directory: Path, thread_id: str) -> list[Path]:
    return list(sessions_directory.glob(f"*/*/*/*{thread_id}.jsonl"))


def recent_session_paths(
    sessions_directory: Path,
    now: datetime,
) -> list[Path]:
    paths: list[Path] = []
    cutoff = now.timestamp() - RECENT_SUBAGENT_WINDOW_SECONDS
    for day_offset in (0, 1):
        day = now - timedelta(days=day_offset)
        day_directory = sessions_directory / day.strftime("%Y/%m/%d")
        for path in day_directory.glob("rollout-*.jsonl"):
            try:
                if path.stat().st_mtime >= cutoff:
                    paths.append(path)
            except OSError:
                continue
    return paths


def transcript_contains_turn(transcript_path: Path, turn_id: str) -> bool:
    try:
        with transcript_path.open(encoding="utf-8") as transcript:
            for line in transcript:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("type") == "turn_context":
                    payload = record.get("payload")
                    if isinstance(payload, dict) and payload.get("turn_id") == turn_id:
                        return True
    except OSError:
        return False
    return False


def is_luna_worker_notification(
    notification: dict[str, Any],
    sessions_directory: Path | None = None,
    now: datetime | None = None,
) -> bool:
    thread_id_value = notification.get("thread-id") or notification.get("thread_id")
    thread_id = str(thread_id_value) if thread_id_value else ""
    turn_id_value = notification.get("turn-id") or notification.get("turn_id")
    turn_id = str(turn_id_value) if turn_id_value else ""
    sessions_directory = sessions_directory or codex_sessions_directory()

    if thread_id:
        for path in session_paths_for_id(sessions_directory, thread_id):
            metadata = session_metadata(path)
            if metadata is not None and is_luna_worker_metadata(metadata):
                return True

    if not turn_id:
        return False

    current_time = now or datetime.now().astimezone()
    for path in recent_session_paths(sessions_directory, current_time):
        metadata = session_metadata(path)
        if metadata is None or not is_luna_worker_metadata(metadata):
            continue
        if transcript_contains_turn(path, turn_id):
            return True
    return False


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
        for message in reversed(messages):
            if message is None:
                continue
            request = (
                message.strip()
                if isinstance(message, str)
                else json.dumps(message, ensure_ascii=False)
            )
            if request:
                return request
        return "Request unavailable."
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
    directory = cwd or "unknown"
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
            f"Directory: {escape_slack_text(directory)}",
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
    hook_mode = len(argv) == 1
    if len(argv) not in (1, 2):
        print(
            "usage: codex-slack-notify ['<notification-json>']",
            file=sys.stderr,
        )
        return 2

    raw_notification = sys.stdin.read() if hook_mode else argv[1]
    try:
        notification = json.loads(raw_notification)
    except json.JSONDecodeError as error:
        print(f"codex-slack-notify: invalid notification JSON: {error}", file=sys.stderr)
        return 2

    if not isinstance(notification, dict):
        print("codex-slack-notify: notification must be a JSON object", file=sys.stderr)
        return 2

    if hook_mode:
        converted_notification = notification_from_stop_hook(notification)
        if converted_notification is None:
            print("{}")
            return 0
        notification = converted_notification
    else:
        if notification.get("type") != EVENT_TYPE:
            return 0
        if is_luna_worker_notification(notification):
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

    if hook_mode:
        print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
