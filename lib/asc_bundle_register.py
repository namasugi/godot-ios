#!/usr/bin/env python3
"""App Store Connect: Bundle ID（App ID）を登録する。
bundle id は export_presets.cfg から自動導出。既に登録済みなら何もしない。
通常は `asc-bundle-register [--name=...] [--yes]`（bin ラッパー）経由で実行する。
  --name=  Bundle ID の表示名（既定は scheme 名）。英数字とスペースのみ。
  --yes    実際に登録する（無指定なら dry-run で内容のみ表示）。
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
    name = next((a.split("=", 1)[1] for a in argv if a.startswith("--name=")), None)

    H = A.headers()
    bundle = A.bundle_id()
    name = name or A.scheme_name() or bundle.rsplit(".", 1)[-1]

    existing = requests.get(f"{BASE}/bundleIds", headers=H,
                            params={"filter[identifier]": bundle}).json().get("data")
    if existing:
        print(f"• Bundle ID は既に登録済み: {bundle} (id={existing[0]['id']})")
        return

    body = {"data": {"type": "bundleIds",
                     "attributes": {"identifier": bundle, "name": name, "platform": "IOS"}}}
    print(f"Bundle ID 登録: identifier={bundle}  name={name}  platform=IOS")
    res = A.mutate(H, "POST", f"{BASE}/bundleIds", body)
    if res:
        print(f"✅ 登録しました (id={res['data']['id']})")
    A.require_yes(execute, "登録")


if __name__ == "__main__":
    main()
