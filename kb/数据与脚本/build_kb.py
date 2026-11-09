# -*- coding: utf-8 -*-
"""Build the local health knowledge base from cards.json.

Outputs (relative to 个人健康知识库成果/):
  kb/cards/<id>.md          one self-contained card per item  -> feed to hindsight_ingest_document one by one
  kb/<level>-<name>.md      one bundle per level              -> feed as a single document per topic
  知识库/00-索引.md           human入口
  知识库/index.json          machine index for search.py
  导入-Hindsight/hindsight_payload.jsonl   {"title","content"} lines for an importer elsewhere

Nothing here talks to Hindsight. It only writes files.
"""
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KB = ROOT.parent / "知识库"
PAYLOAD_DIR = ROOT.parent / "导入-Hindsight"
DATA = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
META = DATA["meta"]
CARDS = DATA["cards"]

LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "DONT"]
LEVEL_FILE = {
    "L0": "L0-一票否决",
    "L1": "L1-每天",
    "L2": "L2-每周",
    "L3": "L3-每年或按年龄",
    "L4": "L4-出事那一刻",
    "L5": "L5-一次性办完",
    "L6": "L6-情绪与心理",
    "DONT": "L9-省钱的别做",
}
GRADE_DESC = {
    "A": "随机对照或多队列强证据",
    "B": "大型队列 / 系统综述，观察性关联",
    "C": "弱关联或口径需修正",
    "D": "无直接证据，别当结论",
    "-": "常识性安全措施或实操建议，未做分级",
}


def card_md(c: dict) -> str:
    L = []
    L.append(f"# {c['title']}")
    L.append("")
    L.append(f"- 层级：{c['level']} · {c['section']}")
    L.append(f"- 证据等级：{c['grade']}（{GRADE_DESC[c['grade']]}）")
    L.append(f"- 出处：{c['source']}")
    L.append(f"- 检索词：{'、'.join(c['keywords'])}")
    L.append("")
    L.append("## 怎么做")
    for i, s in enumerate(c["do"], 1):
        L.append(f"{i}. {s}")
    L.append("")
    L.append("## 不做的后果")
    L.append(c["harm"])
    L.append("")
    L.append("## 证据")
    L.append(c["evidence"])
    L.append("")
    if c.get("pitfalls"):
        L.append("## 常见误区")
        for p in c["pitfalls"]:
            L.append(f"- {p}")
        L.append("")
    if c.get("notFor"):
        L.append("## 不适用 / 先问医生")
        L.append(c["notFor"])
        L.append("")
    if c.get("related"):
        L.append("## 关联")
        L.append("、".join(f"`{r}`" for r in c["related"]))
        L.append("")
    return "\n".join(L)


def bundle_md(level: str, cards: list) -> str:
    L = []
    L.append(f"# 个人健康知识库 · {LEVEL_FILE[level].split('-', 1)[1]}")
    L.append("")
    L.append(
        f"本文件包含 {len(cards)} 条，层级 {level}。"
        f"证据分级 A/B/C/D 沿用 HowToLiveLonger 的实用分级，不是 GRADE；"
        f"HR/RR/OR 是人群关联，不能相乘，也不能换算成个人寿命。"
    )
    L.append("")
    L.append("---")
    L.append("")
    for c in cards:
        L.append(card_md(c))
        L.append("---")
        L.append("")
    return "\n".join(L)


def index_md() -> str:
    L = []
    L.append(f"# {META['title']}")
    L.append("")
    L.append(f"版本 {META['version']} · 构建于 {META['built_at']} · 共 {len(CARDS)} 张卡片")
    L.append("")
    L.append("## 这个库是什么")
    L.append("")
    L.append(
        "从 4 份 GitHub 知识仓库（HowToLiveLonger / HumanSystemOptimization / "
        "HowToLiveBetter / HowToCook）提炼出的健康知识卡。每张卡回答三件事：**怎么做**、"
        "**不做的后果**、**证据是什么**，并附常见误区与不适用人群。"
    )
    L.append("")
    L.append("## 怎么查")
    L.append("")
    L.append("```powershell")
    L.append("python 数据与脚本/search.py 打鼾")
    L.append("python 数据与脚本/search.py 烫伤 起火      # 多个词=或")
    L.append("python 数据与脚本/search.py --tag L4 --list   # 只看某一层")
    L.append("python 数据与脚本/search.py --list           # 全部标题")
    L.append("python 数据与脚本/search.py 打鼾 --full      # 打印整张卡")
    L.append("```")
    L.append("")
    L.append("## 目录")
    L.append("")
    for lv in LEVEL_ORDER:
        cs = [c for c in CARDS if c["level"] == lv]
        if not cs:
            continue
        L.append(f"### {lv} · {LEVEL_FILE[lv].split('-', 1)[1]}（{len(cs)} 条）")
        L.append("")
        L.append(f"整包文件：[{LEVEL_FILE[lv]}.md]({LEVEL_FILE[lv]}.md)")
        L.append("")
        for c in cs:
            L.append(f"- [{c['title']}](cards/{c['id']}.md) — {c['harm']}")
        L.append("")
    L.append("## 证据分级")
    L.append("")
    for k in ["A", "B", "C", "D", "-"]:
        L.append(f"- `{k}` {GRADE_DESC[k]}")
    L.append("")
    L.append("## 来源")
    L.append("")
    for s in META["sources"]:
        L.append(f"- {s}")
    L.append("")
    L.append(f"> {META['note']}")
    L.append("")
    return "\n".join(L)


def build():
    (KB / "cards").mkdir(parents=True, exist_ok=True)

    # validate related ids
    ids = {c["id"] for c in CARDS}
    missing = sorted({r for c in CARDS for r in c.get("related", []) if r not in ids})
    if missing:
        raise SystemExit(f"related 指向不存在的卡：{missing}")
    dup = [i for i in ids if [c["id"] for c in CARDS].count(i) > 1]
    if dup:
        raise SystemExit(f"重复 id：{dup}")

    for c in CARDS:
        (KB / "cards" / f"{c['id']}.md").write_text(card_md(c), encoding="utf-8")

    bundles = OrderedDict()
    for lv in LEVEL_ORDER:
        cs = [c for c in CARDS if c["level"] == lv]
        if not cs:
            continue
        name = LEVEL_FILE[lv]
        (KB / f"{name}.md").write_text(bundle_md(lv, cs), encoding="utf-8")
        bundles[lv] = cs

    (KB / "00-索引.md").write_text(index_md(), encoding="utf-8")

    idx = {
        "meta": META,
        "count": len(CARDS),
        "cards": [
            {
                "id": c["id"],
                "title": c["title"],
                "level": c["level"],
                "section": c["section"],
                "grade": c["grade"],
                "keywords": c["keywords"],
                "harm": c["harm"],
                "path": f"知识库/cards/{c['id']}.md",
            }
            for c in CARDS
        ],
        "bundles": [
            {"level": lv, "file": f"知识库/{LEVEL_FILE[lv]}.md", "count": len(cs)}
            for lv, cs in bundles.items()
        ],
    }
    (KB / "index.json").write_text(
        json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # payload for an importer on ANOTHER machine: one JSON object per line
    with (PAYLOAD_DIR / "hindsight_payload.jsonl").open("w", encoding="utf-8") as f:
        for lv, cs in bundles.items():
            title = f"个人健康知识库 · {LEVEL_FILE[lv].split('-', 1)[1]}"
            f.write(
                json.dumps({"title": title, "content": bundle_md(lv, cs)}, ensure_ascii=False)
                + "\n"
            )
        for c in CARDS:
            f.write(
                json.dumps({"title": f"健康卡：{c['title']}", "content": card_md(c)}, ensure_ascii=False)
                + "\n"
            )

    print(f"cards={len(CARDS)}  bundles={len(bundles)}")
    print("知识库/ ->", KB)


if __name__ == "__main__":
    build()
