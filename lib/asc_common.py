"""App Store Connect API の共通ヘルパ（プロジェクト非依存）。

- プロジェクトルート: 環境変数 GODOT_IOS_PROJECT（bin ラッパーが設定）か、cwd から project.godot を探索。
- bundle id: <root>/export_presets.cfg の application/bundle_identifier から自動導出。
- 認証: ~/.appstoreconnect/asc_auth.env（ASC_AUTH_ENV で上書き可）。リポジトリには含めない。
"""
import json
import os
import re
import time

import jwt
import requests

BASE = "https://api.appstoreconnect.apple.com/v1"


def project_root():
    d = os.environ.get("GODOT_IOS_PROJECT") or os.getcwd()
    d = os.path.abspath(d)
    while d != "/":
        if os.path.exists(os.path.join(d, "project.godot")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("✗ project.godot が見つかりません（Godot プロジェクト内で実行してください）")


def bundle_id(root=None):
    root = root or project_root()
    cfg = os.path.join(root, "export_presets.cfg")
    if not os.path.exists(cfg):
        raise SystemExit(f"✗ export_presets.cfg がありません: {cfg}")
    for line in open(cfg):
        m = re.search(r'application/bundle_identifier="([^"]+)"', line)
        if m:
            return m.group(1)
    raise SystemExit("✗ export_presets.cfg に bundle_identifier がありません（iOSプリセット未作成？）")


def auth_env():
    path = os.environ.get("ASC_AUTH_ENV") or os.path.expanduser("~/.appstoreconnect/asc_auth.env")
    if not os.path.exists(path):
        raise SystemExit(
            f"✗ 認証ファイルがありません: {path}\n"
            "  asc_auth.env.example をコピーして ~/.appstoreconnect/asc_auth.env を作成してください。"
        )
    e = {}
    for line in open(path):
        m = re.match(r'\s*(ASC_\w+)="?([^"#\n]+)"?', line)
        if m:
            e[m.group(1)] = m.group(2).strip()
    missing = [k for k in ("ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_KEY_PATH") if k not in e]
    if missing:
        raise SystemExit(f"✗ {path} に {', '.join(missing)} がありません")
    return e


def token(e=None):
    e = e or auth_env()
    now = int(time.time())
    key = open(os.path.expanduser(e["ASC_KEY_PATH"])).read()
    return jwt.encode(
        {"iss": e["ASC_ISSUER_ID"], "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        key, algorithm="ES256", headers={"kid": e["ASC_KEY_ID"], "typ": "JWT"},
    )


def headers():
    return {"Authorization": f"Bearer {token()}"}


def app_id(H, bundle):
    data = requests.get(f"{BASE}/apps", headers=H, params={"filter[bundleId]": bundle}).json().get("data")
    if not data:
        raise SystemExit(f"✗ bundle {bundle} に対応するアプリが App Store Connect に見つかりません")
    return data[0]


# ---- export_presets.cfg から派生する値 -------------------------------------

def _preset(root, key):
    cfg = os.path.join(root or project_root(), "export_presets.cfg")
    for line in open(cfg):
        m = re.search(rf'{re.escape(key)}="([^"]*)"', line)
        if m:
            return m.group(1)
    return None


def scheme_name(root=None):
    """export_path のベース名（= Xcode scheme / アプリ名）。bundleId 登録の name 既定に使う。"""
    p = _preset(root, "export_path")
    if p:
        return os.path.basename(p).rsplit(".xcodeproj", 1)[0]
    return None


def short_version(root=None):
    return _preset(root, "application/short_version") or "1.0.0"


# ---- 書き込み（dry-run 安全弁つき） ----------------------------------------

def mutate(H, method, url, body=None):
    """POST/PATCH/DELETE を実行。ASC_DRY_RUN=1 のときは送信せず内容を表示する。
    返り値: パース済み JSON（204/ dry-run のときは None）。失敗時は SystemExit。"""
    if os.environ.get("ASC_DRY_RUN") == "1":
        print(f"[dry-run] {method} {url}")
        if body is not None:
            print(json.dumps(body, ensure_ascii=False, indent=2))
        return None
    h = dict(H)
    if body is not None:
        h["Content-Type"] = "application/json"
    r = requests.request(method, url, headers=h, json=body)
    if r.status_code >= 400:
        raise SystemExit(f"✗ {method} {url} → HTTP {r.status_code}: {r.text}")
    return r.json() if r.text.strip() else None


def editable_version(H, app):
    """編集中（PREPARE_FOR_SUBMISSION）の appStoreVersion を返す。無ければ最新。"""
    vers = requests.get(f"{BASE}/apps/{app}/appStoreVersions",
                        headers=H, params={"limit": 5}).json().get("data", [])
    if not vers:
        raise SystemExit("✗ appStoreVersion がありません（先に asc-version-new でバージョン作成）")
    return next((v for v in vers if v["attributes"]["appStoreState"] == "PREPARE_FOR_SUBMISSION"), vers[0])


def require_yes(execute, what):
    """非 dry-run 実行前のガード。--yes が無ければ dry-run に倒し、実行方法を案内する。"""
    if not execute:
        print(f"※ これは dry-run です（{what} は送信しません）。実際に実行するには --yes を付けてください。")
