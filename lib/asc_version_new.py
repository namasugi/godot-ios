#!/usr/bin/env python3
"""App Store Connect: 新しい appStoreVersion（提出用バージョン）を作成する。
通常は `asc-version-new [版番号] [--yes]`（bin ラッパー）経由で実行する。
  版番号  省略時は export_presets.cfg の application/short_version。
  --yes   実際に作成する（無指定なら dry-run）。
アプリレコード自体は API で作成できないため、事前に App Store Connect の Web UI で
「＋ → 新規 App」を済ませておくこと。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asc_common as A
from asc_common import BASE


def main():
    import requests
    argv = sys.argv[1:]
    execute = "--yes" in argv
    os.environ["ASC_DRY_RUN"] = "0" if execute else "1"
    pos = [a for a in argv if not a.startswith("--")]

    H = A.headers()
    app = A.app_id(H, A.bundle_id())["id"]
    version = pos[0] if pos else A.short_version()

    # 既存バージョンと重複チェック
    vers = requests.get(f"{BASE}/apps/{app}/appStoreVersions",
                        headers=H, params={"limit": 10}).json().get("data", [])
    dup = next((v for v in vers if v["attributes"]["versionString"] == version), None)
    if dup:
        print(f"• バージョン {version} は既に存在します (state={dup['attributes']['appStoreState']})")
        return

    body = {"data": {"type": "appStoreVersions",
                     "attributes": {"platform": "IOS", "versionString": version},
                     "relationships": {"app": {"data": {"type": "apps", "id": app}}}}}
    print(f"バージョン作成: {version} (platform=IOS, app={app})")
    res = A.mutate(H, "POST", f"{BASE}/appStoreVersions", body)
    if res:
        print(f"✅ 作成しました (id={res['data']['id']})")
    A.require_yes(execute, "作成")


if __name__ == "__main__":
    main()
