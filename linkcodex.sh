#!/usr/bin/env bash

set -euo pipefail

DOTFILES_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_DIR="$DOTFILES_DIR/codex"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
NOTIFY_SETTING='notify = ["codex-slack-notify"]'

backup_and_link() {
    local source_path="$1"
    local target_path="$2"
    local current_target
    local backup_path

    if [ ! -e "$source_path" ]; then
        echo "Missing source: $source_path" >&2
        return 1
    fi

    mkdir -p -- "$(dirname -- "$target_path")"

    if [ -L "$target_path" ]; then
        current_target="$(readlink -f -- "$target_path" || true)"
        if [ "$current_target" = "$(readlink -f -- "$source_path")" ]; then
            echo "Already linked: $target_path"
            return 0
        fi
    fi

    if [ -e "$target_path" ] || [ -L "$target_path" ]; then
        backup_path="${target_path}.pre-dotfiles-${TIMESTAMP}"
        if [ -e "$backup_path" ] || [ -L "$backup_path" ]; then
            backup_path="${backup_path}.$$"
        fi
        mv -- "$target_path" "$backup_path"
        echo "Backed up: $target_path -> $backup_path"
    fi

    ln -s -- "$source_path" "$target_path"
    echo "Linked: $target_path -> $source_path"
}

link_if_tracked() {
    local relative_path="$1"
    local source_path="$SOURCE_DIR/$relative_path"

    if [ -e "$source_path" ]; then
        backup_and_link "$source_path" "$TARGET_DIR/$relative_path"
    fi
}

configure_notify() {
    local config_path="$TARGET_DIR/config.toml"
    local existing_setting
    local temp_path
    local backup_path

    if [ -f "$TARGET_DIR/hooks.json" ] &&
        grep -Fq 'codex-slack-notify' "$TARGET_DIR/hooks.json"; then
        echo "Notification hook already exists: $TARGET_DIR/hooks.json"
        return 0
    fi

    if [ ! -e "$config_path" ] && [ ! -L "$config_path" ]; then
        (
            umask 077
            printf '%s\n' "$NOTIFY_SETTING" > "$config_path"
        )
        echo "Created Codex config with notification setting: $config_path"
        return 0
    fi

    if [ ! -f "$config_path" ]; then
        echo "Codex config is not a regular file: $config_path" >&2
        return 1
    fi

    existing_setting="$(
        awk '
            /^[[:space:]]*\[/ { exit }
            /^[[:space:]]*notify[[:space:]]*=/ { print; exit }
        ' "$config_path"
    )"

    if [ -n "$existing_setting" ]; then
        if printf '%s\n' "$existing_setting" |
            grep -Eq '^[[:space:]]*notify[[:space:]]*=[[:space:]]*\[[[:space:]]*"codex-slack-notify"[[:space:]]*\][[:space:]]*(#.*)?$'; then
            echo "Notification setting already exists: $config_path"
            return 0
        fi

        echo "A different root-level notify setting already exists in $config_path:" >&2
        echo "  $existing_setting" >&2
        echo "Leaving it unchanged." >&2
        return 1
    fi

    temp_path="$(mktemp "${config_path}.tmp.XXXXXX")"
    if ! awk -v setting="$NOTIFY_SETTING" '
        BEGIN { inserted = 0 }
        !inserted && /^[[:space:]]*\[/ {
            print setting
            print ""
            inserted = 1
        }
        { print }
        END {
            if (!inserted) {
                if (NR > 0) {
                    print ""
                }
                print setting
            }
        }
    ' "$config_path" > "$temp_path"; then
        rm -f -- "$temp_path"
        return 1
    fi

    chmod --reference="$config_path" "$temp_path"
    backup_path="${config_path}.pre-dotfiles-${TIMESTAMP}"
    if [ -e "$backup_path" ] || [ -L "$backup_path" ]; then
        backup_path="${backup_path}.$$"
    fi
    cp -pL -- "$config_path" "$backup_path"
    mv -- "$temp_path" "$config_path"

    echo "Backed up Codex config: $backup_path"
    echo "Added notification setting to the root section: $config_path"
}

mkdir -p -- "$TARGET_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required to synchronize Codex shared config." >&2
    exit 1
fi
uv run --script "$SOURCE_DIR/sync_config.py" \
    "$SOURCE_DIR/config.shared.toml" "$TARGET_DIR/config.toml"

backup_and_link "$SOURCE_DIR/notify_slack.py" "$HOME/.local/bin/codex-slack-notify"
configure_notify

link_if_tracked "AGENTS.md"
link_if_tracked "hooks.json"
link_if_tracked "requirements.toml"

if [ -d "$SOURCE_DIR/skills" ]; then
    for skill_path in "$SOURCE_DIR"/skills/*; do
        if [ -e "$skill_path" ]; then
            backup_and_link "$skill_path" "$TARGET_DIR/skills/$(basename -- "$skill_path")"
        fi
    done
fi

echo "Codex dotfiles are configured. Restart Codex to load config changes."
