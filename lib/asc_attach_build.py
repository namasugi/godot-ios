#!/usr/bin/env python3
"""App Store Connect: 最新の処理済みビルドを編集中バージョンに添付する。
bundle id は実行中の Godot プロジェクトの export_presets.cfg から自動導出する。
通常は `asc-attach [build番号]`（bin ラッパー）経由で実行する。引数なしなら最新の VALID ビルドを添付。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asc_common as A
from asc_common import BASE


def main():
    import requests
    want = sys.argv[1] if len(sys.argv) > 1 else None
    H = A.headers()
    g = lambda u, **k: requests.get(u, headers=H, **k).json()

    app = A.app_id(H, A.bundle_id())["id"]
    vers = g(f"{BASE}/apps/{app}/appStoreVersions", params={"limit": 5})["data"]
    v = next((x for x in vers if x["attributes"]["appStoreState"] == "PREPARE_FOR_SUBMISSION"), vers[0])
    vid = v["id"]
    print(f"version {v['attributes']['versionString']} (id={vid})")

    builds = g(f"{BASE}/builds", params={"filter[app]": app, "sort": "-uploadedDate", "limit": 10})["data"]
    print("最近のビルド:")
    chosen = None
    for b in builds:
        a = b["attributes"]
        print(f"  build {a.get('version')}  state={a.get('processingState')}  expired={a.get('expired')}")
        if want:
            if a.get("version") == want and a.get("processingState") == "VALID":
                chosen = chosen or b["id"]
        elif a.get("processingState") == "VALID" and not a.get("expired") and chosen is None:
            chosen = b["id"]

    if not chosen:
        print("\n⏳ 添付可能な VALID ビルドがまだありません（処理中なら数分待って再実行）。")
        sys.exit(2)

    body = {"data": {"type": "builds", "id": chosen}}
    r = requests.patch(f"{BASE}/appStoreVersions/{vid}/relationships/build",
                       headers={**H, "Content-Type": "application/json"}, json=body)
    if r.status_code in (200, 204):
        print(f"\n✅ ビルドを添付しました (build id={chosen})")
    else:
        print(f"\n✗ 添付失敗 HTTP {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
