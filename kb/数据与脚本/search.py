# -*- coding: utf-8 -*-
"""Local search over the health knowledge base. No network, no Hindsight calls.

  python search.py 打鼾
  python search.py 烫伤 起火          多个词按「或」匹配，命中权重相加
  python search.py 咳嗽 --and         多个词必须同时命中
  python search.py --tag L4            只看某一层（L0..L5 / DONT）
  python search.py --list              列出全部卡片
  python search.py 打鼾 --full         打印整张卡
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
CARDS = DATA["cards"]
CARD_DIR = ROOT.parent / "知识库" / "cards"

LEVEL_NAME = {
    "L0": "一票否决", "L1": "每天", "L2": "每周", "L3": "每年/按年龄",
    "L4": "出事那一刻", "L5": "一次性办完", "L6": "情绪与心理", "DONT": "别做",
}


def haystack(c):
    return " ".join(
        [
            c["title"], c["section"], c["harm"], c["evidence"],
            " ".join(c["do"]), " ".join(c.get("pitfalls", [])),
            c.get("notFor", ""), c["source"],
        ]
    ).lower()


def score(c, terms, require_all):
    kw = [k.lower() for k in c["keywords"]]
    title = c["title"].lower()
    body = haystack(c)
    total = 0
    hit_terms = 0
    for t in terms:
        s = 0
        if any(t == k or t in k for k in kw):
            s += 5
        if t in title:
            s += 3
        if t in body:
            s += 1
        if s:
            hit_terms += 1
        total += s
    if require_all and hit_terms < len(terms):
        return 0
    return total


def short(c, n=70):
    h = c["harm"]
    return h if len(h) <= n else h[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("terms", nargs="*", help="检索词")
    ap.add_argument("--tag", default="", help="只看某一层：L0 L1 L2 L3 L4 L5 DONT")
    ap.add_argument("--list", action="store_true", help="列出全部卡片")
    ap.add_argument("--full", action="store_true", help="打印完整卡片")
    ap.add_argument("--and", action="store_true", dest="require_all", help="所有词必须命中")
    ap.add_argument("-n", type=int, default=5, help="返回条数，默认 5")
    a = ap.parse_args()

    pool = CARDS
    if a.tag:
        tag = a.tag.upper()
        pool = [c for c in pool if c["level"] == tag]
        if not pool:
            sys.exit(f"没有 {a.tag} 这一层，可选：{', '.join(LEVEL_NAME)}")

    if a.list or not a.terms:
        for c in pool:
            print(f"{c['level']:<5} {c['grade']:<2} {c['title']}")
            print(f"      {short(c, 60)}")
        print(f"\n共 {len(pool)} 张卡")
        return

    terms = [t.lower() for t in a.terms]
    ranked = sorted(
        ((score(c, terms, a.require_all), c) for c in pool),
        key=lambda x: -x[0],
    )
    ranked = [(s, c) for s, c in ranked if s > 0][: a.n]
    if not ranked:
        print(f"没找到「{' '.join(a.terms)}」。试试 --list 看全部标题。")
        return

    for s, c in ranked:
        print(f"[{c['level']} {LEVEL_NAME.get(c['level'], '')}] {c['title']}   (相关度 {s})")
        print(f"  证据 {c['grade']} · {c['source']}")
        print(f"  不做的后果：{c['harm']}")
        print(f"  卡片：知识库/cards/{c['id']}.md")
        if a.full:
            body = (CARD_DIR / f"{c['id']}.md").read_text(encoding="utf-8")
            print("\n" + body)
        print()


if __name__ == "__main__":
    main()
