#!/usr/bin/env python3
"""App Store Connect: 提出に必要な項目の入力状況を監査して未入力を洗い出す。
bundle id は実行中の Godot プロジェクトの export_presets.cfg から自動導出する。
通常は `asc-audit`（bin ラッパー）経由で実行する。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asc_common as A
from asc_common import BASE


def mark(ok):
    return "✅" if ok else "❌ 未入力"


def get(H, url, **kw):
    import requests
    return requests.get(url, headers=H, **kw).json()


def main():
    import requests
    H = A.headers()
    bundle = A.bundle_id()
    app = A.app_id(H, bundle)
    app_id = app["id"]
    print(f"# {bundle} 提出項目 監査 (app {app_id})\n")

    # ---- App情報（appInfo: カテゴリ/コンテンツ権利/年齢） ----
    infos = get(H, f"{BASE}/apps/{app_id}/appInfos")["data"]
    info = infos[0]
    ia = info["attributes"]
    inc = get(H, f"{BASE}/apps/{app_id}/appInfos",
              params={"include": "primaryCategory,secondaryCategory,ageRatingDeclaration"}).get("included", [])
    age = next((x for x in inc if x["type"] == "ageRatingDeclarations"), None)
    print("## App情報（全言語共通・一度だけ）")
    print(f"- プライマリカテゴリ: {mark(info['relationships'].get('primaryCategory',{}).get('data'))}")
    print(f"- コンテンツ配信権(Content Rights): {mark(ia.get('contentRightsDeclaration'))}  値={ia.get('contentRightsDeclaration')}")
    print(f"- 年齢制限(Age Rating): {mark(age is not None)}")

    # appInfoLocalizations: name/subtitle/privacyPolicyUrl
    ail = get(H, f"{BASE}/appInfos/{info['id']}/appInfoLocalizations")["data"]
    for l in ail:
        a = l["attributes"]
        loc = a["locale"]
        print(f"- [{loc}] 名前:{mark(a.get('name'))} / サブタイトル:{mark(a.get('subtitle'))} / プライバシーURL:{mark(a.get('privacyPolicyUrl'))}")

    # ---- バージョン ----
    vers = get(H, f"{BASE}/apps/{app_id}/appStoreVersions", params={"limit": 5})["data"]
    v = next((x for x in vers if x["attributes"]["appStoreState"] == "PREPARE_FOR_SUBMISSION"), vers[0])
    va = v["attributes"]
    vid = v["id"]
    print(f"\n## バージョン {va['versionString']} (state={va['appStoreState']})")
    print(f"- 著作権(Copyright): {mark(va.get('copyright'))}  値={va.get('copyright')}")
    b = get(H, f"{BASE}/appStoreVersions/{vid}/build").get("data")
    print(f"- ビルド添付: {mark(b is not None)}")
    print(f"- リリースタイプ: {va.get('releaseType')}")

    # version localizations: description/keywords/promotionalText/supportUrl/marketingUrl/whatsNew
    vl = get(H, f"{BASE}/appStoreVersions/{vid}/appStoreVersionLocalizations", params={"limit": 50})["data"]
    print("\n## バージョン情報（言語別）")
    for l in vl:
        a = l["attributes"]
        loc = a["locale"]
        sets = get(H, f"{BASE}/appStoreVersionLocalizations/{l['id']}/appScreenshotSets")["data"]
        shots = sum(len(get(H, f"{BASE}/appScreenshotSets/{s['id']}/appScreenshots")["data"]) for s in sets)
        print(f"- [{loc}]")
        print(f"    説明:{mark(a.get('description'))} / キーワード:{mark(a.get('keywords'))} / "
              f"プロモ:{mark(a.get('promotionalText'))}")
        print(f"    サポートURL:{mark(a.get('supportUrl'))} / マーケURL:{a.get('marketingUrl') or '—(任意)'} / "
              f"新機能:{a.get('whatsNew') or '—(初回は任意)'}")
        print(f"    スクショ:{mark(shots>0)} ({shots}枚)")

    # ---- 価格 ----
    try:
        sched = get(H, f"{BASE}/apps/{app_id}/appPriceSchedule")
        has_price = bool(sched.get("data"))
    except Exception:
        has_price = False
    print(f"\n## 価格")
    print(f"- 価格スケジュール: {mark(has_price)}")

    # ---- IAP ----
    iaps = get(H, f"{BASE}/apps/{app_id}/inAppPurchasesV2", params={"limit": 20}).get("data", [])
    print(f"\n## アプリ内課金")
    if not iaps:
        print("- ❌ IAP未作成")
    for p in iaps:
        a = p["attributes"]
        print(f"- {a.get('productId')}  state={a.get('state')}  ({a.get('name')})")


if __name__ == "__main__":
    main()
