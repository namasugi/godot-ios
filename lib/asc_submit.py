#!/usr/bin/env python3
"""App Store Connect: 編集中バージョンを審査に提出する（reviewSubmissions フロー）。
通常は `asc-submit [--yes]`（bin ラッパー）経由で実行する。--yes 無しは dry-run。

⚠ これは Apple の審査に実際に提出する操作。事前に asc-audit で必須項目が全て ✅ なこと、
   ビルドが添付済み（asc-attach 済み）なことを確認すること。
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

    H = A.headers()
    app = A.app_id(H, A.bundle_id())["id"]
    v = A.editable_version(H, app)
    vid = v["id"]
    print(f"審査提出: app={app} version={v['attributes']['versionString']} (state={v['attributes']['appStoreState']})")

    # 1) 進行中の reviewSubmission を再利用、無ければ作成
    subs = requests.get(f"{BASE}/apps/{app}/reviewSubmissions", headers=H,
                        params={"filter[state]": "READY_FOR_REVIEW,WAITING_FOR_REVIEW,IN_REVIEW", "limit": 1}).json().get("data", [])
    if subs:
        sub_id = subs[0]["id"]
        print(f"- 既存の reviewSubmission を使用 (id={sub_id})")
    else:
        res = A.mutate(H, "POST", f"{BASE}/reviewSubmissions",
                       {"data": {"type": "reviewSubmissions",
                                 "attributes": {"platform": "IOS"},
                                 "relationships": {"app": {"data": {"type": "apps", "id": app}}}}})
        sub_id = res["data"]["id"] if res else "<new>"
        print(f"- reviewSubmission 作成 (id={sub_id})")

    # 2) このバージョンを提出アイテムとして追加
    A.mutate(H, "POST", f"{BASE}/reviewSubmissionItems",
             {"data": {"type": "reviewSubmissionItems",
                       "relationships": {
                           "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": sub_id}},
                           "appStoreVersion": {"data": {"type": "appStoreVersions", "id": vid}}}}})
    print("- reviewSubmissionItem 追加")

    # 3) 提出を確定
    A.mutate(H, "PATCH", f"{BASE}/reviewSubmissions/{sub_id}",
             {"data": {"type": "reviewSubmissions", "id": sub_id, "attributes": {"submitted": True}}})
    if execute:
        print("✅ 審査に提出しました。")
    A.require_yes(execute, "審査提出")


if __name__ == "__main__":
    main()
