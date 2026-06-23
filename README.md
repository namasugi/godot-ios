# godot-ios

Godot 4 プロジェクト共通の iOS ツールキット。**1コピーを全プロジェクトで共有**する。
各ゲームプロジェクトには固有設定を置かない（bundle id 等はプロジェクトの `export_presets.cfg` から自動導出）。

## 構成

```
bin/    実行コマンド（PATH へ symlink して使う）
  ios-export          デバッグエクスポート（向き正規化込み）
  ios-export-release  リリースエクスポート（TestFlight/App Store 提出用）
  ios-run             実機 iPhone へ export→build→install→launch（ワンコマンド）
  asc-audit           App Store Connect 提出項目の未入力監査
  asc-attach [build]  最新 VALID ビルドを編集中バージョンへ添付
lib/    共有ロジック（python/sh）。bin から呼ばれる
skill/  Claude Code 用スキル（~/.claude/skills へ symlink）
```

## セットアップ

```bash
# 1. CLI を PATH へ（~/.local/bin が PATH 上にある前提）
for f in bin/*; do ln -sf "$PWD/$f" ~/.local/bin/"$(basename "$f")"; done

# 2. ASC 認証（アカウント単位・全アプリ共通・リポジトリ外）
mkdir -p ~/.appstoreconnect/private_keys
cp asc_auth.env.example ~/.appstoreconnect/asc_auth.env   # 各値を記入、.p8 を private_keys/ へ

# 3. Claude スキル（任意・Claude から駆動したい場合）
ln -sfn "$PWD/skill" ~/.claude/skills/godot-ios-appstore
```

`asc-*` は初回実行時に `.venv/`（pyjwt/requests/cryptography）を自動作成する。

## 使い方（任意の Godot プロジェクト内で）

```bash
cd ~/work/godot/<game>     # project.godot のあるディレクトリ配下ならどこでも可
ios-run                    # 実機デプロイ
ios-export-release         # 提出用 .xcodeproj 生成 → Xcode で Archive/アップロード
asc-audit                  # 提出項目の未入力チェック
asc-attach                 # アップロード済みビルドをバージョンへ添付
```

## プロジェクト固有の上書き（任意）

向きやプリセット名を変えたいプロジェクトだけ `<project>/tools/ios.env` を置く:

```bash
IOS_ORIENT=1       # 0=landscape 1=portrait … 6=sensor(全方向)
IOS_PRESET=iOS
GODOT_BIN=godot
```

## 設計メモ

- **bundle id**: `export_presets.cfg` の `application/bundle_identifier` から自動導出。プロジェクトに重複設定を持たない。
- **ASC 認証**: Apple Developer **アカウント単位**なので `~/.appstoreconnect/` に1つだけ。全アプリで共通。
- **秘密情報**（`.p8` / `asc_auth.env`）は `.gitignore` 済み。リポジトリには `asc_auth.env.example` のみ → public 公開可。
