---
name: godot-ios-appstore
description: Submit a Godot 4 iOS app to App Store Connect / TestFlight via the ASC API. Generate a release export, audit which submission fields are still missing (categories, age rating, copyright, descriptions, screenshots, price, IAP), and attach an uploaded build to the editing version. Use when the user wants to prepare an App Store / TestFlight submission, check what's missing before submitting, attach a build, or build a release .xcodeproj. For plain on-device testing use the `ios-run` command instead.
---

# Godot 4 → App Store Connect 提出

このプラグインの `bin/` は有効化中 Bash の PATH に自動追加されるので、コマンドは**ベア名でそのまま実行**できる
（`asc-audit` 等）。見つからない場合のみ `"${CLAUDE_PLUGIN_ROOT}/bin/asc-audit"` のように絶対参照する。

**プロジェクト非依存**：bundle id は実行中プロジェクトの `export_presets.cfg` から自動導出。コマンドは対象
Godot プロジェクトの **cwd 内**（`project.godot` のあるディレクトリ配下）で実行すること。

前提チェック（不足なら案内）:
- `asc-*` は App Store Connect API 認証が必要 → `~/.appstoreconnect/asc_auth.env` と `.p8` がある
  （無ければ: `asc_auth.env.example` を `~/.appstoreconnect/asc_auth.env` にコピーして記入、`.p8` を
  `~/.appstoreconnect/private_keys/` へ。詳細は README）
- 初回実行時に依存（pyjwt/requests/cryptography）の venv を自動作成する（要 `python3`）

## 1. リリースビルドを作る

```bash
ios-export-release            # build/ios/<App>.xcodeproj を生成（向きは縦=1 既定、IOS_ORIENT で上書き）
```

生成された `.xcodeproj` を Xcode で開き **Product → Archive → Distribute → App Store Connect** でアップロード。
（CLI 末尾の archive 失敗は無害。署名付き Archive は Xcode GUI で行う。）

## 2. 提出項目の未入力を洗い出す

```bash
asc-audit
```

App情報（カテゴリ/コンテンツ権利/年齢）・バージョン（著作権/ビルド添付/リリースタイプ）・言語別
（説明/キーワード/プロモ/サポートURL/スクショ枚数）・価格・IAP を ✅/❌ で一覧する。❌ を App Store Connect の
Web UI で埋める。

## 3. アップロード済みビルドをバージョンへ添付

アップロード後 ASC 側の processing が VALID になってから:

```bash
asc-attach            # 最新の VALID ビルドを編集中バージョンへ添付
asc-attach 12         # build 番号を指定する場合
```

`⏳ VALID ビルドがまだありません` が出たら processing 中。数分待って再実行。

## 注意

- **認証エラー**: `~/.appstoreconnect/asc_auth.env` の KEY_ID / ISSUER_ID / KEY_PATH と `.p8` の存在を確認。
- **アプリが見つからない**: `export_presets.cfg` の bundle id が App Store Connect 上のアプリと一致しているか。
- **実機テスト**（提出ではない日常デプロイ）は `ios-run`（export→build→install→launch のワンコマンド）を使う。
