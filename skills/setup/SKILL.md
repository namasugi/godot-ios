---
name: godot-ios-setup
description: Configure App Store Connect API credentials for the godot-ios tools (writes ~/.appstoreconnect/asc_auth.env). Run once after installing the plugin, or when asc-audit / asc-attach report missing or invalid credentials. Collects the Key ID, Issuer ID, and .p8 key path, then verifies them. Not needed for on-device deploy (ios-run).
allowed-tools: Bash, AskUserQuestion
---

# App Store Connect 認証セットアップ

godot-ios の `asc-*`（提出系）が使う ASC API 認証を `~/.appstoreconnect/asc_auth.env` に作成する。
（`ios-run` など実機デプロイには ASC 認証は不要。）対話で3つの値を集め、検証まで行う。

1. まず取得元を案内する:
   App Store Connect → ユーザーとアクセス → 統合(Integrations) → App Store Connect API でキーを発行し、
   `AuthKey_XXXX.p8` をダウンロード。発行画面の **Key ID**、ページ上部の **Issuer ID** を控える。
   `.p8` は `~/.appstoreconnect/private_keys/` へ置くよう促す。

2. `AskUserQuestion` で次の3つを尋ねる（ユーザーがその場で値を入力できるよう free-text で受ける）:
   - **Key ID**（例 `ABCDE12345`）
   - **Issuer ID**（例 `12345678-90ab-cdef-1234-567890abcdef`）
   - **.p8 のパス**（例 `~/.appstoreconnect/private_keys/AuthKey_ABCDE12345.p8`）

3. 集めた値で書き込み＋検証コマンドを実行する:
   ```bash
   ASC_KEY_ID="<key id>" ASC_ISSUER_ID="<issuer id>" ASC_KEY_PATH="<.p8 path>" godot-ios-setup
   ```
   `✓ JWT 署名OK` が出れば成功。`⚠` が出たら .p8 のパス/中身を一緒に確認する。

4. 仕上げに、対象 Godot プロジェクト内で `asc-audit` を実行して疎通を確認するとよい。

メモ: 値はローカルの `~/.appstoreconnect/asc_auth.env`（パーミッション 600）に保存。リポジトリには
含めない（`.gitignore` 済み）。ターミナルから直接 `godot-ios-setup` を実行すれば `read -p` で対話入力もできる。
