# Shared helpers for the godot-ios toolkit.
# Sourced by the bin/ wrappers. Requires GODOT_IOS_HOME to be set by the caller.

# Walk up from $1 (default: cwd) to the nearest Godot project (has project.godot).
find_project_root() {
  local d="${1:-$PWD}"
  d="$(cd "$d" 2>/dev/null && pwd)" || return 1
  while [[ "$d" != "/" ]]; do
    [[ -f "$d/project.godot" ]] && { printf '%s\n' "$d"; return 0; }
    d="$(dirname "$d")"
  done
  echo "✗ project.godot が見つかりません（Godotプロジェクト内で実行してください）" >&2
  return 1
}

# Source an optional per-project override file (tools/ios.env) for IOS_ORIENT/IOS_PRESET/GODOT_BIN.
load_project_env() {
  [[ -f "tools/ios.env" ]] && source "tools/ios.env" || true
}

# Lazily create the toolkit's own venv with the ASC Python deps. Prints the python path.
# As a Claude Code plugin, prefer CLAUDE_PLUGIN_DATA so the venv survives plugin version bumps
# (the plugin dir itself is re-copied to a new cache path on each update).
ensure_venv() {
  local v="${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/venv}"
  v="${v:-$GODOT_IOS_HOME/.venv}"
  if [[ ! -x "$v/bin/python" ]]; then
    echo "[godot-ios] 初回セットアップ: venv を作成中 ($v)" >&2
    python3 -m venv "$v" >&2
    "$v/bin/pip" install -q --upgrade pip >&2
    "$v/bin/pip" install -q pyjwt requests cryptography >&2
  fi
  printf '%s\n' "$v/bin/python"
}
