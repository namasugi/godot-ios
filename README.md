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

`ios-*` は Godot CLI と Xcode のみ。`asc-*` は App Store Connect API（JWT 認証）を使う。

## インストール

```bash
git clone https://github.com/namasugi/godot-ios.git
cd godot-ios
./install.sh
```

`install.sh` がやること（上書き先は `BIN_DIR` / `SKILLS_DIR` / `AUTH_DIR` で変更可）:

- `bin/*` を `~/.local/bin` へ symlink（PATH に通っている前提）
- `skill/` を `~/.claude/skills/godot-ios-appstore` へ symlink（[Claude Code](https://claude.com/claude-code) 利用時）
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

## 設計

- **bundle id**: `export_presets.cfg` の `application/bundle_identifier` から自動導出。プロジェクトに重複設定を持たない。
- **ASC 認証**: Apple Developer アカウント単位なので `~/.appstoreconnect/` に1つだけ。全アプリで共通。
- **秘密情報**（`.p8` / `asc_auth.env`）は `.gitignore` 済み。リポジトリには `asc_auth.env.example` のみ。
- **更新**: 中央リポを `git pull` すれば全プロジェクトに即反映（symlink 運用のため再インストール不要）。

## 構成

```
bin/    実行コマンド（PATH へ symlink）
lib/    共有ロジック（python / sh）。bin から呼ばれる
skill/  Claude Code 用スキル（~/.claude/skills へ symlink）
install.sh  セットアップ（symlink + 認証雛形）
asc_auth.env.example  認証の雛形
```

## ライセンス

MIT
