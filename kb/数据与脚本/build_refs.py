# -*- coding: utf-8 -*-
"""生成 02-引用与来源.md：把每张卡追溯到它引用的原文条目与论文（含 DOI）。

数据来源（全部在仓库内，可复核）：
  原始资料/HLB_book/*.md            HowToLiveBetter 章节正文（### 条目 / 证据等级 / 来源）
  原始资料/HowToLiveLonger_evidence.json   HTL 研究台账（64 records + citations）
  数据与脚本/cards.json             本包的 65 张卡

    python 数据与脚本/build_refs.py
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
SRC = PKG / "原始资料"
CARDS = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
META = CARDS["meta"]
CARD_LIST = CARDS["cards"]

# ---------------------------------------------------------------- 上游仓库
REPOS = [
    ("HowToCook", "https://github.com/Anduin2017/HowToCook", "103.7k", "Unlicense（公共领域）",
     "食品安全温度表、油的烟点与轮换、食物中毒清单", "HowToCook_README.md / HowToCook_食品安全.md / HowToCook_厨房准备.md"),
    ("HowToLiveBetter", "https://github.com/eternity4719/HowToLiveBetter", "74.4k", "CC BY 4.0（需署名）",
     "L0–L5 骨架、急救与筛查、情绪与心理的效应量", "HowToLiveBetter_README.md / HowToLiveBetter_selfcheck.html / HLB_book/ 5 章"),
    ("HowToLiveLonger", "https://github.com/geekan/HowToLiveLonger", "36.0k", "Unlicense（公共领域）",
     "A/B/C/D 分级体系、64 条研究台账（HR/RR/CI）", "HowToLiveLonger_README.md / HowToLiveLonger_evidence.json / HTLL_compact.txt"),
    ("HumanSystemOptimization", "https://github.com/zijie0/HumanSystemOptimization", "21.9k", "**无许可证文件**",
     "机制层：晨光、进食窗口、多巴胺、菌群（仅做事实引用与改写）", "HumanSystemOptimization_README.md"),
]

NOT_USED = [
    ("remote-working", "11.8k", "资料合集，不含健康证据"),
    ("openGym", "20.4k", "训练记录工具，不产生知识"),
    ("workout-cool", "8.7k", "训练计划工具"),
    ("Trail-Sense", "3.0k", "户外生存工具，场景在野外"),
    ("wego(wegoweather)", "8.6k", "终端天气"),
    ("briefsky", "259", "天气前端"),
    ("OpenFarm", "1.7k", "种植数据库，2025-04 后未更新"),
    ("fate", "2.4k", "起名工具，五行属文化趣味"),
]

GRADE_DESC = {
    "A": "随机对照或多队列强证据", "B": "大型队列/系统综述（观察性关联）",
    "C": "弱关联或口径需修正", "D": "无直接证据", "-": "常识性安全措施/实操，未分级",
}


# ---------------------------------------------------------------- 解析 HLB 正文
def parse_hlb():
    """{(chapter:int, entry:int): {title, grade, sources:[raw], dois:[], urls:[]}}"""
    out = {}
    for f in sorted((SRC / "HLB_book").glob("*.md")):
        if f.name == "_index.json":
            continue
        m = re.match(r"(\d+)-", f.name)
        if not m:
            continue
        ch = int(m.group(1))
        text = f.read_text(encoding="utf-8")
        parts = re.split(r"^### (\d+)\.\s*(.+)$", text, flags=re.M)
        # parts: [preamble, num, title, body, num, title, body, ...]
        for i in range(1, len(parts) - 2, 3):
            num, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
            g = re.search(r"- 证据等级：([ABCD\-])", body)
            s = re.search(r"- 来源：(.*)", body)
            src = s.group(1).strip() if s else ""
            dois = re.findall(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", src)
            urls = re.findall(r"https?://[^\s<>）)]+", src)
            out[(ch, num)] = {
                "title": title, "grade": g.group(1) if g else "", "sources": src,
                "dois": list(dict.fromkeys(dois)), "urls": list(dict.fromkeys(urls)),
                "file": f.name,
            }
    return out


HLB = parse_hlb()

# ---------------------------------------------------------------- 解析 HTL 台账
HTL = json.loads((SRC / "HowToLiveLonger_evidence.json").read_text(encoding="utf-8-sig"))
HTL_RECORDS = HTL["records"]


def _norm(t):
    """去掉空白与标点，用于宽松比较。"""
    return re.sub(r"[\s（）()【】\[\]、，,。·—\-／/]", "", t or "").lower()


def htl_lookup(name):
    """按 factor 名匹配台账记录：主名归一化后比对，括号内限定词加权。"""
    raw = (name or "").strip()
    base = re.sub(r"[（(].*?[）)]", "", raw).strip()
    kb = _norm(base)
    quals = [_norm(q) for q in re.findall(r"[（(]([^）)]*)[）)]", raw)]
    scored = []
    for r in HTL_RECORDS:
        f = r.get("factor") or ""
        if not f:
            continue
        nf = _norm(f)
        fb = _norm(re.sub(r"[（(].*?[）)]", "", f))
        score = 0
        if kb and kb == fb:
            score += 10
        elif kb and (kb in nf or fb in kb):
            score += 5
        for q in quals:
            if q and q[:6] and q[:6] in nf:
                score += 3
        if score:
            scored.append((score, len(f), r))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [r for _, _, r in scored[:3]]


def refs_for_card(card):
    """返回 [(kind, label, detail, links[])]"""
    src = card["source"]
    out = []

    # HLB 条目级：HLB §29 第1、5、12条
    for m in re.finditer(r"HLB\s*§(\d+)(?:[–-](\d+))?\s*第([\d、,，]+)条", src):
        ch = int(m.group(1))
        for num in re.findall(r"\d+", m.group(3)):
            e = HLB.get((ch, int(num)))
            if e:
                links = [f"https://doi.org/{d}" for d in e["dois"]] + \
                        [u for u in e["urls"] if "doi.org" not in u]
                out.append(("HLB", f"§{ch} 第{num}条 {e['title']}", f"证据等级 {e['grade']}", links))
            else:
                out.append(("HLB", f"§{ch} 第{num}条", "该章正文未收录", []))
    if out:
        return out

    # HLB 章节级（没有条号）
    chs = re.findall(r"§(\d+)", src.split("；HSO")[0].split("；HTC")[0])
    if "HLB" in src and chs:
        for ch in dict.fromkeys(int(c) for c in chs):
            have = sorted(n for (c, n) in HLB if c == ch)
            if not have:
                out.append(("HLB 章", f"§{ch} 全章", "正文未收录（引用为章节级）", []))
                continue
            # 在这一章里按关键词找候选条目（标注为候选，不冒充条号）
            kws = [k for k in card.get("keywords", []) if len(k) >= 2]
            scored = []
            for n in have:
                title = HLB[(ch, n)]["title"]
                hits = [k for k in kws if k in title]
                if hits:
                    scored.append((len(hits), n, title, hits))
            scored.sort(key=lambda x: (-x[0], x[1]))
            out.append(("HLB 章", f"§{ch} 全章", f"本地已收录 {len(have)} 条", []))
            for cnt, n, title, hits in scored[:2]:
                e = HLB[(ch, n)]
                links = [f"https://doi.org/{d}" for d in e["dois"]][:4]
                out.append((
                    "候选条目",
                    f"§{ch} 第{n}条 {title}",
                    f"关键词命中 {'、'.join(hits[:4])} · 证据等级 {e['grade']}（候选，未人工确认）",
                    links,
                ))
    # HTL 台账
    for m in re.finditer(r"HTL\s*([^；;]+?)(?=[；;]|$)", src):
        name = m.group(1).strip()
        recs = htl_lookup(name)
        if not recs:
            out.append(("HTL", f"HTL {name}", "台账中未定位到同名 factor", []))
            continue
        for r in recs:
            links = []
            for s in (r.get("sources") or []):
                u = s if isinstance(s, str) else (s.get("url") or "")
                if u.startswith("http") and "github.com/geekan/MetaGPT" not in u:
                    links.append(u)
            out.append((
                "HTL",
                f"HTL {r.get('factor')}",
                f"分级 {r.get('grade')} · {r.get('verdict')} · {r.get('effect') or ''}",
                links[:4],
            ))

    # HSO
    if "HSO" in src:
        out.append(("HSO", "HumanSystemOptimization", "机制层来源；该项目无许可证，本包仅作事实引用与改写", []))
    if "HTC" in src:
        out.append(("HTC", "HowToCook 食品安全 / 厨房准备", "常识性安全措施（Unlicense）", []))
    return out


def build():
    L = []
    CN = "一二三四五六七八九十"
    secno = [0]

    def sec(title):
        secno[0] += 1
        L.append(f"## {CN[secno[0] - 1]}、{title}")
        L.append("")

    L.append("# 引用与来源")
    L.append("")
    L.append("> 这份文件回答一个问题：**包里每一条结论，能追到哪一段原文、哪一篇论文。**")
    L.append("> 全部由 `数据与脚本/build_refs.py` 从仓库内的原始资料自动生成，可重跑复核。")
    L.append("")
    L.append(f"版本 {META['version']} · 构建于 {META['built_at']} · 卡片 {len(CARD_LIST)} 张")
    L.append("")

    # ---- 一、上游仓库
    sec("引用到的上游仓库")
    L.append("")
    L.append("来自星标清单 `github.com/stars/endlesswxk/lists/生活与健康` 的 12 个仓库，其中 4 个构成本包的知识来源：")
    L.append("")
    L.append("| 仓库 | ★ | 许可证 | 本包用了什么 | 本地文件 |")
    L.append("|---|---|---|---|---|")
    for name, url, stars, lic, what, files in REPOS:
        L.append(f"| [{name}]({url}) | {stars} | {lic} | {what} | `{files}` |")
    L.append("")
    L.append("快照时间：2026-11-09（GitHub 页面与 raw 文件）。star 数为当日值，会变。")
    L.append("")
    L.append("### 许可证这件事要说清楚")
    L.append("")
    L.append("| 仓库 | 许可证 | 对本包意味着什么 |")
    L.append("|---|---|---|")
    L.append("| HowToCook | Unlicense（公共领域） | 可自由使用，无需署名（本包仍署名） |")
    L.append("| HowToLiveLonger | Unlicense（公共领域） | 同上；A/B/C/D 分级沿用其定义 |")
    L.append("| HowToLiveBetter | CC BY 4.0 | **必须署名**；本包已在 README、页面 footer、本节署名，衍生物同样 CC BY 4.0 |")
    hso_ids = [c["id"] for c in CARD_LIST if "HSO" in c["source"]]
    hso_list = "、".join("`" + i + "`" for i in hso_ids)
    L.append(
        "| HumanSystemOptimization | **没有 LICENSE 文件** | 默认保留所有权利。"
        "本包**不整段复制**其文字，只做事实引用与改写；若权利人提出要求，"
        f"删除 `source` 里带 `HSO` 的 {len(hso_ids)} 张卡（{hso_list}）即可 |"
    )
    L.append("")
    L.append("> 结论：别人的代码/文本不能因为「放在 GitHub 上」就当成免费。`HumanSystemOptimization` 这一条是最容易被忽略的。")
    L.append("")
    L.append("### 没有采用另外 8 个")
    L.append("")
    L.append("| 仓库 | ★ | 为什么没进知识库 |")
    L.append("|---|---|---|")
    for name, stars, why in NOT_USED:
        L.append(f"| {name} | {stars} | {why} |")
    L.append("")

    # ---- 二、逐卡溯源
    sec("逐卡溯源")
    L.append("")
    L.append("每张卡 → 它引用的原文条目 → 该条目下的论文（DOI 可点）。")
    L.append("")
    missing_chapters = OrderedDict()
    for c in CARD_LIST:
        refs = refs_for_card(c)
        L.append(f"### `{c['id']}` {c['title']}")
        L.append("")
        L.append(f"- 卡片标注：`{c['source']}` · 证据等级 **{c['grade']}**（{GRADE_DESC[c['grade']]}）")
        if not refs:
            L.append("- 溯源：卡片未标注来源（需补）")
            L.append("")
            continue
        for kind, label, detail, links in refs:
            line = f"- **{kind}** · {label} — {detail}"
            L.append(line)
            if links:
                L.append("  - " + " · ".join(f"<{u}>" for u in links[:6]))
            if kind == "HLB 章" and "未收录" in detail:
                missing_chapters.setdefault(label, []).append(c["id"])
        L.append("")

    # ---- 三、未收录正文的章节
    if missing_chapters:
        sec("还缺正文的章节（引用只有章节级）")
        L.append("这些卡引用的 HLB 章节正文还没取到本地，所以只能标到「第几节」，给不出条目号与 DOI。")
        L.append("补法见 `01-待办-未覆盖缺口.md`：从 `raw.githubusercontent.com/eternity4719/HowToLiveBetter/main/book/` 取对应 `NN-*.md`。")
        L.append("")
        L.append("| 章节 | 受影响卡片 |")
        L.append("|---|---|")
        for ch, ids in missing_chapters.items():
            L.append(f"| {ch} | {', '.join('`'+i+'`' for i in ids)} |")
        L.append("")

    # ---- 四、政策与指南
    sec("政策与指南类来源")
    L.append("")
    L.append("本包有几条结论靠的是国内政策文件或国际指南，不是论文。它们同样是可复核的：")
    L.append("")
    seen = set()
    rows = []
    for (ch, num), e in sorted(HLB.items()):
        for u in e["urls"]:
            if any(k in u for k in ("gov.cn", "nhc.gov.cn", "nice.org.uk", "nia.nih.gov", "flk.npc.gov.cn", "who.int")):
                if u in seen:
                    continue
                seen.add(u)
                rows.append((f"§{ch} 第{num}条", u))
    for label, u in rows[:40]:
        L.append(f"- {label} · <{u}>")
    L.append("")
    L.append(f"（从已收录的 {len(HLB)} 条 HLB 正文里抽到 {len(seen)} 个政策/指南链接，上面列出前 40 个。）")
    L.append("")

    # ---- 五、复核方法
    sec("自己复核这三步")
    L.append("")
    L.append("```powershell")
    L.append("# 1. 重取某一章原文（把 29 换成章节号）")
    L.append("#    https://raw.githubusercontent.com/eternity4719/HowToLiveBetter/main/book/29-遭遇重大打击之后.md")
    L.append("# 2. 重取 HTL 台账")
    L.append("#    https://raw.githubusercontent.com/geekan/HowToLiveLonger/main/data/evidence.json")
    L.append("# 3. 重跑本文件，看溯源有没有变")
    L.append("python 数据与脚本/build_refs.py")
    L.append("```")
    L.append("")
    L.append("> 注意：论文的 DOI 指向出版方页面，摘要可读、全文多数需要机构订阅。本包只引用原文已经写明")
    L.append("> 的效应量，不自行换算、不做二次统计。")
    L.append("")

    out = PKG / "02-引用与来源.md"
    out.write_text("\n".join(L), encoding="utf-8")
    n_doi = len(re.findall(r"doi\.org/", "\n".join(L)))
    print(f"refs -> {out}  ({out.stat().st_size:,} B)  HLB 条目 {len(HLB)} 条 · DOI 链接 {n_doi} 个")


if __name__ == "__main__":
    build()
