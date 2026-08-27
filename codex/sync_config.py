#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tomlkit>=0.13,<1",
# ]
# ///

from __future__ import annotations

import argparse
import copy
from datetime import datetime
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from collections.abc import Iterator

from tomlkit import dumps, parse, table
from tomlkit.exceptions import NonExistentKey, TOMLKitError
from tomlkit.items import InlineTable, Item, Table


MANAGED_PATHS = (
    ("model",),
    ("model_reasoning_effort",),
    ("personality",),
    ("web_search",),
    ("service_tier",),
    ("approvals_reviewer",),
    ("features", "multi_agent"),
    ("features", "js_repl"),
    ("features", "hooks"),
    ("tui", "theme"),
    ("tui", "status_line"),
    ("tui", "status_line_use_colors"),
)
MANAGED_PATH_SET = frozenset(MANAGED_PATHS)
MANAGED_TABLE_PREFIXES = frozenset(
    path[:-1] for path in MANAGED_PATHS if len(path) > 1
)
MISSING = object()


class SyncError(ValueError):
    """Raised when a shared config cannot be applied safely."""


def iter_shared_nodes(
    container: object, prefix: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], bool]]:
    """Yield each shared table and leaf path for schema validation."""
    body = getattr(container, "body", ())
    for key, value in body:
        if key is None:
            continue
        path = prefix + (key.key,)
        if isinstance(value, (Table, InlineTable)):
            yield path, True
            yield from iter_shared_nodes(value.value, path)
        else:
            yield path, False


def validate_shared_config(shared: object) -> None:
    for path, is_table in iter_shared_nodes(shared):
        dotted_path = ".".join(path)
        if is_table:
            if path not in MANAGED_TABLE_PREFIXES:
                raise SyncError(f"unsupported shared table: {dotted_path}")
        elif path not in MANAGED_PATH_SET:
            raise SyncError(f"unsupported shared key: {dotted_path}")


def lookup_item(document: object, path: tuple[str, ...]) -> tuple[object, object]:
    """Return the parent container and item, or MISSING if the item is absent."""
    container = document
    for segment in path[:-1]:
        try:
            current = container.item(segment)
        except NonExistentKey:
            return MISSING, MISSING
        if not isinstance(current, (Table, InlineTable)):
            return MISSING, MISSING
        container = current.value

    try:
        return container, container.item(path[-1])
    except NonExistentKey:
        return container, MISSING


def ensure_parent(document: object, path: tuple[str, ...]) -> object:
    container = document
    for segment in path[:-1]:
        try:
            current = container.item(segment)
        except NonExistentKey:
            container[segment] = table()
            current = container.item(segment)
        if not isinstance(current, (Table, InlineTable)):
            dotted_path = ".".join(path[:-1])
            raise SyncError(f"target path is not a table: {dotted_path}")
        container = current.value
    return container


def item_value(value: Item) -> object:
    return value.unwrap()


def apply_shared_config(shared: object, target: object) -> bool:
    changed = False
    for path in MANAGED_PATHS:
        _, shared_item = lookup_item(shared, path)
        target_parent, target_item = lookup_item(target, path)

        if shared_item is MISSING:
            if target_item is not MISSING:
                target_parent.remove(path[-1])
                changed = True
            continue

        if (
            target_item is not MISSING
            and item_value(target_item) == item_value(shared_item)
        ):
            continue

        target_parent = ensure_parent(target, path)
        target_parent[path[-1]] = copy.deepcopy(shared_item)
        changed = True

    return changed


def unique_backup_path(target: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = target.with_name(f"{target.name}.pre-dotfiles-{timestamp}")
    candidate = base
    suffix = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = target.with_name(
            f"{target.name}.pre-dotfiles-{timestamp}-{suffix}"
        )
        suffix += 1
    return candidate


def write_target(target: Path, content: bytes, mode: int) -> Path | None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if target.exists():
        backup_path = unique_backup_path(target)
        shutil.copy2(target, backup_path)

    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.tmp-", dir=target.parent
    )
    try:
        os.fchmod(temp_fd, mode)
        with os.fdopen(temp_fd, "wb") as stream:
            temp_fd = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
        temp_name = ""
    finally:
        if temp_fd != -1:
            os.close(temp_fd)
        if temp_name:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    return backup_path


def sync(shared_path: Path, target_path: Path) -> int:
    shared = parse(shared_path.read_text(encoding="utf-8"))
    validate_shared_config(shared)

    if target_path.exists():
        target_bytes = target_path.read_bytes()
        target = parse(target_bytes.decode("utf-8"))
        target_mode = stat.S_IMODE(target_path.stat().st_mode)
    else:
        target_bytes = b""
        target = parse("")
        target_mode = 0o600

    changed = apply_shared_config(shared, target)
    if not changed:
        print(f"No changes: {target_path}")
        return 0

    rendered = dumps(target).encode("utf-8")
    if rendered == target_bytes:
        print(f"No changes: {target_path}")
        return 0

    backup_path = write_target(target_path, rendered, target_mode)
    if backup_path is None:
        print(f"Created: {target_path}")
    else:
        print(f"Backed up: {target_path} -> {backup_path}")
        print(f"Updated: {target_path}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize portable Codex settings into a local config."
    )
    parser.add_argument("shared", type=Path, help="shared TOML config path")
    parser.add_argument("target", type=Path, help="local TOML config path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        return sync(args.shared, args.target)
    except (OSError, UnicodeError, TOMLKitError, SyncError) as error:
        print(f"sync_config.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
