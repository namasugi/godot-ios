# godot-ios

Godot 4 プロジェクト共通の **iOS デプロイ & App Store Connect 提出ツールキット**。
macOS + Xcode 前提。**1コピーを全プロジェクトで共有**する設計で、各ゲームプロジェクトには固有設定を
ほぼ置かない（bundle id 等はプロジェクトの `export_presets.cfg` から自動導出）。無料 Personal Team でも
実機デプロイできる。

## できること

| コマンド | 内容 |
|---|---|
| `ios-run [UDID]` | 実機 iPhone へ export→build→install→launch（ワンコマンド。USB / Wi-Fi 両対応） |
| `ios-export` | デバッグ用 `.xcodeproj` を生成（向き enum を正規化） |
| `ios-export-release` | リリース用 `.xcodeproj` を生成（TestFlight / App Store 提出用） |
| `asc-audit` | App Store Connect の提出項目（カテゴリ/年齢/著作権/説明/スクショ/価格/IAP）の未入力を監査 |
| `asc-attach [build]` | アップロード済みの VALID ビルドを編集中バージョンへ添付 |
| `asc-bundle-register` | Bundle ID（App ID）を登録 |
| `asc-version-new [版]` | 新しい appStoreVersion（提出用バージョン）を作成 |
| `asc-meta-set <json>` | メタデータ（著作権/カテゴリ/各言語の説明・キーワード等）を JSON から一括投入 |
| `asc-submit` | 編集中バージョンを審査に提出 |
| `godot-ios-setup` | App Store Connect API 認証を対話で設定（`asc-*` 利用前に一度） |

> **書き込み系（`asc-bundle-register` / `asc-version-new` / `asc-meta-set` / `asc-submit`）は既定で dry-run**
> （送信内容を表示するだけ）。実際に App Store Connect を変更するには `--yes` を付ける。

## 前提条件

用途で必要なものが分かれる。**実機テストだけなら無料アカウントでOK**、提出には有料登録が要る。

**共通（必須）**

- macOS + **Xcode 本体**（Command Line Tools のみでは不可。`xcode-select -p` が `…/Xcode.app/…` を指す）
- **Godot 4** が `godot` で起動できる（PATH 上）
- 対象 Godot バージョンと一致する **iOS エクスポートテンプレート**（未導入の入れ方は `godot-ios:deploy` スキル参照）
- 各プロジェクトに **iOS エクスポートプリセット**（`export_presets.cfg`。雛形 `skills/deploy/preset.cfg.template`）

**実機デプロイのみ（`ios-run` / `ios-export`）**

- Apple ID（**無料 Personal Team で可**）。ただし証明書は7日で失効、プロビジョニングに実機が必須

**App Store / TestFlight 提出（`ios-export-release` / `asc-*`）**

- **有料 Apple Developer Program**（年額）への登録
- **App Store Connect API キー**（`.p8`）＋ Key ID / Issuer ID → `godot-ios-setup`（または `/godot-ios:setup`）で設定
- **python3**（`asc-*` が依存 venv の自動作成に使用）

## インストール

### A. Claude Code プラグインとして（推奨）

このリポジトリは [Claude Code](https://claude.com/claude-code) のマーケットプレイス兼プラグイン。
Claude Code 内で:

```text
/plugin marketplace add namasugi/godot-ios
/plugin install godot-ios@godot-ios
```

有効化すると `bin/`（`ios-run` / `asc-audit` 等）が Bash の PATH に自動追加され、スキル
`godot-ios:deploy`（実機デプロイ）/ `godot-ios:appstore`（提出）/ `godot-ios:setup`（認証設定）も自動で
取り込まれる。**手動 symlink 不要**。

提出系 `asc-*` を使うなら、インストール後に Claude Code 内で **`/godot-ios:setup`** を実行して認証を設定する
（対話で Key ID / Issuer ID / .p8 パスを聞かれ、`~/.appstoreconnect/asc_auth.env` を作成・検証する）。未設定の
まま Godot プロジェクトを開くと、セッション開始時に一度だけ設定を促すメッセージが出る（実機デプロイには不要）。

### B. 手動 CLI / 非 Claude 環境

```bash
git clone https://github.com/namasugi/godot-ios.git
cd godot-ios
./install.sh
```

`install.sh` がやること（上書き先は `BIN_DIR` / `SKILLS_DIR` / `AUTH_DIR` で変更可）:

- `bin/*` を `~/.local/bin` へ symlink（PATH に通っている前提）
- `skills/appstore` を `~/.claude/skills/godot-ios-appstore` へ symlink（Claude Code 利用時。
  ローカルで本体を編集しながら使いたい開発者向け。プラグイン版 A とは排他に使う）
- `~/.appstoreconnect/` に認証の置き場所と `asc_auth.env` 雛形を用意

### ASC 認証（`asc-*` を使う場合のみ）

App Store Connect API キーは **Apple Developer アカウント単位**（全アプリ共通）。`~/.appstoreconnect/` に
1つだけ置き、リポジトリには含めない。

1. App Store Connect → ユーザーとアクセス → 統合 → App Store Connect API で API キーを発行
2. ダウンロードした `AuthKey_XXXX.p8` を `~/.appstoreconnect/private_keys/` へ
3. `~/.appstoreconnect/asc_auth.env` に Key ID / Issuer ID / キーのパスを記入（`asc_auth.env.example` 参照）

`asc-*` は初回実行時に toolkit 内 `.venv`（pyjwt / requests / cryptography）を自動作成する（要 `python3`）。

## 使い方（任意の Godot プロジェクト内で）

`project.godot` のあるディレクトリ配下ならどこでも:

```bash
cd path/to/your-godot-game
ios-run                    # 実機デプロイ
ios-export-release         # 提出用 .xcodeproj 生成 → Xcode で Archive / アップロード
asc-audit                  # 提出項目の未入力チェック
asc-attach                 # アップロード済みビルドをバージョンへ添付
```

### 前提（iOS エクスポートプリセット）

各プロジェクトの `export_presets.cfg` に iOS プリセットが必要。最低限のキー:

```ini
export_path="build/ios/MyGame.xcodeproj"
application/bundle_identifier="com.example.mygame"
application/app_store_team_id="ABCDE12345"      # 空だと署名失敗
application/min_ios_version="14.0"              # Metal は iOS 14+ 必須
application/targeted_device_family=0            # 0=iPhone / 1=iPad / 2=両方
```

### プロジェクト固有の上書き（任意）

向きやプリセット名を変えたいプロジェクトだけ `<project>/tools/ios.env` を置く:

```bash
IOS_ORIENT=1       # 0=landscape 1=portrait 2=reverse_landscape 3=reverse_portrait
                   # 4=sensor_landscape 5=sensor_portrait 6=sensor(全方向)
IOS_PRESET=iOS
GODOT_BIN=godot
```

## App Store 提出フロー（API 自動化）

新規アプリの **アプリレコード作成だけは公式 API で不可**（`apps` に POST が無い）。最初の1回だけ
App Store Connect の Web UI で「＋ → 新規 App」を作る。その前後は API で自動化できる:

```bash
asc-bundle-register --yes              # 1. Bundle ID を登録（Web UI でアプリ作成する前に）
#   --- App Store Connect の Web UI で「新規 App」を作成（1回だけ・手作業）---
asc-version-new 1.0.0 --yes            # 2. 提出バージョンを作成
asc-meta-set metadata.json --yes       # 3. 著作権/カテゴリ/各言語メタデータを投入
ios-export-release                     # 4. リリースビルド生成 → Xcode で Archive/アップロード
asc-attach --yes                       # 5. 処理済みビルドをバージョンへ添付
asc-audit                              # 6. 未入力(❌)が無いか最終チェック
asc-submit --yes                       # 7. 審査に提出
```

`--yes` を外すと各ステップは **dry-run**（送信せず内容表示）になるので、まず付けずに確認 → `--yes` で実行が安全。
`asc-meta-set` の JSON 形式は `asc-meta-set`（引数なし）で表示されるヘルプ参照。

## 設計

- **bundle id**: `export_presets.cfg` の `application/bundle_identifier` から自動導出。プロジェクトに重複設定を持たない。
- **ASC 認証**: Apple Developer アカウント単位なので `~/.appstoreconnect/` に1つだけ。全アプリで共通。
- **秘密情報**（`.p8` / `asc_auth.env`）は `.gitignore` 済み。リポジトリには `asc_auth.env.example` のみ。
- **更新**: 中央リポを `git pull` すれば全プロジェクトに即反映（symlink 運用のため再インストール不要）。

## 構成

```
.claude-plugin/
  plugin.json        Claude Code プラグイン定義
  marketplace.json   このリポジトリをマーケットプレイスとして公開（source: "./"）
  hooks/hooks.json   SessionStart で認証未設定を一度だけ案内（Godotプロジェクト時のみ）
skills/
  deploy/    実機デプロイ＋初回セットアップのスキル（preset.cfg.template 同梱）
  appstore/  App Store Connect 提出フローのスキル
  setup/     ASC 認証を対話設定するスキル（/godot-ios:setup）
bin/    実行コマンド（プラグイン有効化で自動 PATH / 手動は symlink）
lib/    共有ロジック（python / sh）。bin から呼ばれる
install.sh           手動セットアップ（symlink + 認証雛形）
asc_auth.env.example 認証の雛形
```

## ライセンス

MIT
