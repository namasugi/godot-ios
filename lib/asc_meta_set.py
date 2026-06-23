#!/usr/bin/env python3
"""App Store Connect: メタデータを JSON から一括投入する（asc-audit の ❌ を埋める用途）。
通常は `asc-meta-set <json> [--yes]`（bin ラッパー）経由で実行する。--yes 無しは dry-run。

JSON 例（与えたキーだけ反映。localizations は locale 単位で upsert）:
{
  "copyright": "2026 ikesugi-web",
  "primaryCategory": "GAMES",
  "secondaryCategory": "GAMES_PUZZLE",
  "localizations": {
    "ja":    {"name": "くまサバ", "subtitle": "...", "privacyPolicyUrl": "https://...",
              "description": "...", "keywords": "a,b,c", "promotionalText": "...",
              "supportUrl": "https://...", "marketingUrl": "https://...", "whatsNew": "..."},
    "en-US": {"description": "...", "keywords": "...", "supportUrl": "https://..."}
  }
}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asc_common as A
from asc_common import BASE

APPINFO_FIELDS = {"name", "subtitle", "privacyPolicyUrl"}
VERSION_FIELDS = {"description", "keywords", "promotionalText", "supportUrl", "marketingUrl", "whatsNew"}


def _upsert(H, list_url, child_type, parent_rel, parent_type, parent_id, locale, attrs):
    import requests
    if not attrs:
        return
    items = requests.get(list_url, headers=H, params={"limit": 50}).json().get("data", [])
    found = next((x for x in items if x["attributes"].get("locale") == locale), None)
    if found:
        print(f"  [{locale}] 更新 {child_type}: {', '.join(attrs)}")
        A.mutate(H, "PATCH", f"{BASE}/{child_type}/{found['id']}",
                 {"data": {"type": child_type, "id": found["id"], "attributes": attrs}})
    else:
        print(f"  [{locale}] 新規 {child_type}: {', '.join(attrs)}")
        A.mutate(H, "POST", f"{BASE}/{child_type}",
                 {"data": {"type": child_type, "attributes": {**attrs, "locale": locale},
                           "relationships": {parent_rel: {"data": {"type": parent_type, "id": parent_id}}}}})


def main():
    import requests
    argv = sys.argv[1:]
    execute = "--yes" in argv
    os.environ["ASC_DRY_RUN"] = "0" if execute else "1"
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        sys.exit(__doc__)
    data = json.load(open(paths[0]))

    H = A.headers()
    app = A.app_id(H, A.bundle_id())["id"]
    v = A.editable_version(H, app)
    vid = v["id"]
    info = requests.get(f"{BASE}/apps/{app}/appInfos", headers=H).json()["data"][0]
    info_id = info["id"]
    print(f"メタデータ投入: app={app} version={v['attributes']['versionString']} appInfo={info_id}")

    # バージョン属性
    if "copyright" in data:
        print(f"- copyright = {data['copyright']}")
        A.mutate(H, "PATCH", f"{BASE}/appStoreVersions/{vid}",
                 {"data": {"type": "appStoreVersions", "id": vid, "attributes": {"copyright": data["copyright"]}}})

    # カテゴリ（appInfo relationships）
    rels = {}
    for key in ("primaryCategory", "secondaryCategory"):
        if data.get(key):
            rels[key] = {"data": {"type": "appCategories", "id": data[key]}}
    if rels:
        cats = ", ".join(f"{k}={rels[k]['data']['id']}" for k in rels)
        print(f"- categories = {cats}")
        A.mutate(H, "PATCH", f"{BASE}/appInfos/{info_id}",
                 {"data": {"type": "appInfos", "id": info_id, "relationships": rels}})

    # ローカライズ（locale 単位で appInfo / version の両系統へ振り分け）
    for locale, fields in (data.get("localizations") or {}).items():
        info_attrs = {k: v for k, v in fields.items() if k in APPINFO_FIELDS}
        ver_attrs = {k: v for k, v in fields.items() if k in VERSION_FIELDS}
        _upsert(H, f"{BASE}/appInfos/{info_id}/appInfoLocalizations",
                "appInfoLocalizations", "appInfo", "appInfos", info_id, locale, info_attrs)
        _upsert(H, f"{BASE}/appStoreVersions/{vid}/appStoreVersionLocalizations",
                "appStoreVersionLocalizations", "appStoreVersion", "appStoreVersions", vid, locale, ver_attrs)

    A.require_yes(execute, "メタデータ更新")


if __name__ == "__main__":
    main()
