#!/usr/bin/env bash
# godot-ios セットアップ: bin を PATH へ、skill を Claude へ symlink、ASC 認証の雛形を用意する。
# 上書き先は環境変数で変更可: BIN_DIR / SKILLS_DIR / AUTH_DIR
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
SKILLS_DIR="${SKILLS_DIR:-$HOME/.claude/skills}"
AUTH_DIR="${AUTH_DIR:-$HOME/.appstoreconnect}"

# 1. CLI を PATH へ symlink
mkdir -p "$BIN_DIR"
for f in "$HERE"/bin/*; do ln -sf "$f" "$BIN_DIR/$(basename "$f")"; done
echo "✓ bin -> $BIN_DIR"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "  ⚠ $BIN_DIR が PATH にありません。shell の rc に追加してください:"
     echo "     export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

# 2. Claude Code スキルを symlink（~/.claude が無い環境ならスキップ）
if [ -d "$HOME/.claude" ]; then
  mkdir -p "$SKILLS_DIR"
  ln -sfn "$HERE/skill" "$SKILLS_DIR/godot-ios-appstore"
  echo "✓ skill -> $SKILLS_DIR/godot-ios-appstore"
else
  echo "• ~/.claude が無いのでスキル symlink はスキップ（CLI のみ利用）"
fi

# 3. ASC 認証の置き場所と雛形（アカウント単位・リポジトリ外）
mkdir -p "$AUTH_DIR/private_keys"
if [ ! -f "$AUTH_DIR/asc_auth.env" ]; then
  cp "$HERE/asc_auth.env.example" "$AUTH_DIR/asc_auth.env"
  echo "✓ 認証雛形を作成: $AUTH_DIR/asc_auth.env"
  echo "  → 各値を記入し、AuthKey_XXXX.p8 を $AUTH_DIR/private_keys/ へ置いてください。"
else
  echo "• 既存の認証を保持: $AUTH_DIR/asc_auth.env"
fi

echo "done. 任意の Godot プロジェクト内で 'ios-run' / 'asc-audit' 等が使えます。"
