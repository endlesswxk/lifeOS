# -*- coding: utf-8 -*-
"""把 checklist.json 生成 lifeOS app 里的 CHECK_SECTIONS（清单数据）。

app 与知识库同仓库时，app 在仓库根、知识库在 kb/，所以默认路径是 ../index.html。

    python 数据与脚本/build_app.py                    # 就地更新 ../index.html
    python 数据与脚本/build_app.py --app D:/x/index.html
    python 数据与脚本/build_app.py --check            # 只校验是否同步，不写盘

为什么要有这个脚本：
  以前 app 里的清单是手写死的一份副本，改了 checklist.json 它不会动。
  现在两边同一个来源，每条还带一个 card 字段指向知识库的卡，
  app 里点「依据 ↗」就能跳到 kb/site/#c-<卡 id>。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent

START = "/* <<KB-CHECK-START>>"
END = "/* <<KB-CHECK-END>> */"

LEVEL_LABEL = {"L0": "一票否决", "L1": "每天", "L2": "每周", "L3": "每年/按年龄",
               "L4": "出事那一刻", "L5": "一次性办完", "DONT": "禁"}


def load():
    cl = json.loads((ROOT / "checklist.json").read_text(encoding="utf-8"))
    cards = {c["id"]: c for c in json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))["cards"]}
    return cl, cards


def build_sections(cl, cards):
    """checklist.json -> app 的 CHECK_SECTIONS 结构，并校验每条都指向真实卡片。"""
    secs = []
    problems = []
    for sec in cl["sections"]:
        items = []
        for it in sec["items"]:
            cid = it.get("card")
            if not cid:
                problems.append(f"{it.get('id', '?')} 缺 card 字段")
            elif cid not in cards:
                problems.append(f"{it.get('id', '?')} 指向不存在的卡 {cid}")
            items.append({
                "id": it["id"],
                "text": it["t"],
                "grade": it.get("g", ""),
                "std": it.get("std", ""),
                "harm": it.get("harm", ""),
                "src": it.get("s", ""),
                "card": cid or "",
            })
        secs.append({"lv": sec["level"], "title": sec["title"],
                     "note": sec.get("note", ""), "items": items})

    d = cl["donts"]
    items = []
    for it in d["items"]:
        cid = it.get("card")
        if not cid:
            problems.append(f"{it.get('id', '?')} 缺 card 字段")
        elif cid not in cards:
            problems.append(f"{it.get('id', '?')} 指向不存在的卡 {cid}")
        items.append({
            "id": it["id"], "text": it["t"], "grade": it.get("g", ""),
            "std": it.get("std", ""), "harm": it.get("harm", ""),
            "src": it.get("s", ""), "card": cid or "",
        })
    secs.append({"lv": "DONT", "title": d["title"], "note": d.get("note", ""), "items": items})
    return secs, problems


def render_block(secs):
    payload = json.dumps(secs, ensure_ascii=False, separators=(",", ":"))
    return (f"{START} 由 kb/数据与脚本/build_app.py 从 checklist.json 生成，勿手改 */\n"
            f"const CHECK_SECTIONS = {payload};\n{END}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default=str(PKG.parent / "index.html"))
    ap.add_argument("--check", action="store_true", help="只校验，不写盘")
    args = ap.parse_args()

    cl, cards = load()
    secs, problems = build_sections(cl, cards)
    if problems:
        print("✘ 数据问题：")
        for p in problems:
            print("   " + p)
        return 1

    total = sum(len(s["items"]) for s in secs)
    block = render_block(secs)

    app = Path(args.app)
    if not app.is_file():
        print(f"✘ 找不到 app：{app}")
        return 1
    src = app.read_text(encoding="utf-8")

    if START not in src or END not in src:
        print(f"✘ app 里没有生成标记（{START} … {END}），先确认这是打过补丁的 index.html")
        return 1

    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    cur = pat.search(src).group(0)
    same = cur == block

    if args.check:
        if same:
            print(f"✔ app 清单与 checklist.json 同步（{len(secs)} 组 / {total} 条）")
            return 0
        print(f"✘ app 清单已过期（{len(secs)} 组 / {total} 条）——跑 python 数据与脚本/build_app.py")
        return 1

    if same:
        print(f"✔ 无需更新（{len(secs)} 组 / {total} 条，{len(block):,} 字符）")
        return 0

    out = pat.sub(lambda _: block, src, count=1)
    app.write_text(out, encoding="utf-8")
    linked = sum(1 for s in secs for i in s["items"] if i["card"])
    print(f"app -> {app}  ({len(out.encode('utf-8')):,} B)")
    print(f"  清单 {len(secs)} 组 / {total} 条 · 其中 {linked} 条带知识库深链")
    print(f"  数据块 {len(cur):,} → {len(block):,} 字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
