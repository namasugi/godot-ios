---
name: godot-ios-deploy
description: Set up and deploy a Godot 4 project to a physical iPhone/iPad via Xcode + CLI (free Personal Team friendly). Covers export-template install, iOS export preset, code signing, and one-command build→install→launch over USB or Wi-Fi. Use when the user wants to test a Godot game on a real iOS device, set up iOS export, fix iOS signing/orientation/device-family issues, or deploy/install to iPhone.
---

# Godot 4 → iPhone 実機デプロイ

macOS + Xcode 前提。Godot プロジェクトを実機 iPhone/iPad へ。**無料 Personal Team** でも動く手順。
初回セットアップと、以降のワンコマンド反映の2段構え。

実機デプロイは **godot-ios ツールキットの `ios-run` コマンド**で行う（このスキルと同じ `godot-ios` プラグインに
同梱。有効化中は `bin/` が PATH に自動追加され、`ios-run` / `ios-export` をベア名で叩ける。手動インストール時は
`./install.sh` で PATH に通す）。**プロジェクトへスクリプトをコピーする必要はない**——コマンドが cwd の Godot
プロジェクトを自動検出し、`export_presets.cfg` から bundle id / scheme を導出する。

## 0. 環境チェック（不足を順に潰す）

```bash
godot --version                                  # 例: 4.6.3.stable …（テンプレ版を一致させる）
xcode-select -p                                  # /Applications/Xcode.app/... を指すべき
xcodebuild -version                              # 動けばOK
ls ~/Library/Application\ Support/Godot/export_templates/   # <version>/ios.zip が要る
```

- **xcode-select が CommandLineTools を指す** → ユーザーに sudo を依頼（自分では実行不可）:
  `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer && sudo xcodebuild -license accept`
- **エクスポートテンプレート未導入** → Godot のバージョン文字列（`X.Y.Z.stable`）と一致する tpz を入れる:
  ```bash
  V=4.6.3   # godot --version の数字部分
  curl -L -o /tmp/tpl.tpz "https://github.com/godotengine/godot/releases/download/${V}-stable/Godot_v${V}-stable_export_templates.tpz"
  mkdir -p /tmp/tplx && unzip -q /tmp/tpl.tpz -d /tmp/tplx
  DEST="$HOME/Library/Application Support/Godot/export_templates/${V}.stable"
  mkdir -p "$DEST" && cp -R /tmp/tplx/templates/. "$DEST/"   # version.txt が "X.Y.Z.stable" と一致するか確認
  ```
- **Apple ID 未登録** → ユーザーが Xcode → Settings → Accounts で追加（無料 Personal Team でOK）。GUI操作。

## 1. 署名情報を集める

- **Team ID**（10文字）を Xcode 設定から拾う（証明書がまだ無くても入っている）:
  ```bash
  defaults read com.apple.dt.Xcode IDEProvisioningTeamByIdentifier 2>/dev/null | grep -E "teamID|teamName|isFree"
  ```
- **Bundle ID** はユーザーに確認（逆ドメイン、例 `com.example.mygame`。ハイフン可）。

## 2. iOS エクスポートプリセットを作る

プロジェクト直下に `export_presets.cfg` を作成（既にあれば iOS プリセットを追記）。テンプレ
`${CLAUDE_SKILL_DIR}/preset.cfg.template` をコピーし、`<PLACEHOLDERS>` を置換して最低限これらを埋める：

- `export_path="build/ios/<AppName>.xcodeproj"`（AppName 任意。scheme 名にもなる）
- `application/bundle_identifier="<BUNDLE_ID>"`
- `application/app_store_team_id="<TEAM_ID>"`  ← 空だと「Team ID が指定されていません」で失敗
- `application/min_ios_version="14.0"`  ← **Metal は iOS 14+ 必須**（12 等だと設定エラー）
- `application/targeted_device_family=0`  ← **0=iPhone / 1=iPad / 2=両方**（下の落とし穴参照）
- `exclude_filter="tmp/*,.shots/*,_shot_*.png,_shot_*.png.import"` ← 作業スクラッチを pck から除外

`.gitignore` に `/build/` を追加（エクスポート生成物）。

## 3. 実機へ（ワンコマンド）

```bash
cd path/to/your-godot-game     # project.godot のあるディレクトリ配下
ios-run                        # 接続iPhone自動検出 → export→build→install→launch
ios-run <UDID>                 # 端末を明示指定する場合
```

`ios-run` は `export_presets.cfg` から bundle id / scheme を自動導出し、`generic/platform=ios` ではなく
**特定デバイスUDID**へビルドする（無料 Team のデバイス登録はこれが必須）。向きやプリセット名を変えたい
プロジェクトだけ `<project>/tools/ios.env`（`IOS_ORIENT` / `IOS_PRESET` / `GODOT_BIN`）を置く。

## 落とし穴（このスキルの肝）

- **向きが横1方向に化ける**: Godot は `display/window/handheld/orientation` を **int enum** として読む。
  project.godot に文字列 `="sensor"` があるとパース失敗で **Info.plist が landscape 1方向だけ**になる
  （実行時の回転は効くので気づきにくい）。`ios-export`（`ios-run` が内部で呼ぶ）がエクスポート直前に
  **int 6（=sensor/全4方向）** へ正規化して回避。エディタは文字列に戻しがちなので、project.godot 側は触らず
  毎回スクリプトで上書きで良い。
- **targeted_device_family の番号ズレ**: Godot の `=1` は **iPad**（pbxproj `TARGETED_DEVICE_FAMILY="2"`）。
  iPhone は **`=0`**。間違えると `iPhone doesn't match any of <App>.app's targeted device families` で起動不可。
- **Metal は iOS 14+**: `min_ios_version` が 12 等だと「MetalレンダラーにはiOS 14以降が必要」で設定エラー。
- **CLIエクスポート末尾の archive 失敗は無害**: `godot --export-debug` は最後に `xcodebuild ... -destination
  generic/platform=ios archive` を走らせる。無料 Team＋汎用ターゲットでは署名できず失敗するが、`.xcodeproj`/`.pck`
  はその手前で生成済み。実機ビルドは `ios-run`（特定デバイス指定の `build`）で行う。
- **pck 肥大**: `tmp/` 等にある venv/numpy・バックアップ画像まで pck に入る。`exclude_filter` で除外。

## 無料 Personal Team の現実

初回デプロイで順に出る壁（`ios-run` のエラーメッセージで判別）:
1. **Team ID 未指定** → プリセットに記入。
2. **デバイス未接続/未登録** → 無料 Team はプロファイル生成に**実機が要る**。USB接続し、`generic` ではなく
   **そのデバイスUDID**へビルド（`ios-run` が対応済み）。
3. **Developer Mode disabled** → iPhone 設定 → プライバシーとセキュリティ → デベロッパモード → オン → **再起動**。
4. **untrusted / プロファイル未信頼** → 初回起動前に iPhone 設定 → 一般 → VPNとデバイス管理 → 開発者を**信頼**。
5. **device locked** → 自動起動だけ失敗（インストールは成功）。ロック解除してアイコンをタップ。

**証明書は7日で失効** → 7日ごとに `ios-run` 再実行で更新（USB/Wi-Fi どちらでも）。
TestFlight / App Store 提出は **godot-ios-appstore** スキル（`ios-export-release` / `asc-*`）を使う。

## ワイヤレス（ケーブルレス）

**一度USBでペアリング**すれば、以降は同一Wi-Fiで無線デプロイできる（Xcode 16 / CoreDevice は自動。旧来の
「Connect via network」手動チェックは不要なことが多い）。確認: USBを抜いて `xcrun devicectl list devices` に
iPhone が `connected` で残れば無線OK。あとは `ios-run` がそのまま無線で通る（同一Wi-Fi・端末ロック解除）。
無線で見えない時だけ Xcode → Window → Devices and Simulators → 端末 → 「Connect via network」を有効化。

## コード更新後（日常運用）

```bash
ios-run          # これだけ。USB/Wi-Fi どちらでも
```
