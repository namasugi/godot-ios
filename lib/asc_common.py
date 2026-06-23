"""App Store Connect API の共通ヘルパ（プロジェクト非依存）。

- プロジェクトルート: 環境変数 GODOT_IOS_PROJECT（bin ラッパーが設定）か、cwd から project.godot を探索。
- bundle id: <root>/export_presets.cfg の application/bundle_identifier から自動導出。
- 認証: ~/.appstoreconnect/asc_auth.env（ASC_AUTH_ENV で上書き可）。リポジトリには含めない。
"""
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
