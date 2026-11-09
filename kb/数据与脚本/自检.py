# -*- coding: utf-8 -*-
"""成果包自检：一条命令跑完所有一致性校验。

    python 数据与脚本/自检.py

检查项：
  1. 目录与关键文件是否齐全
  2. cards.json 结构（数量 / 唯一 id / 必填字段 / 层级）
  3. related 交叉引用是否都指向真实卡片
  4. 知识库/cards/*.md 与 cards.json 是否一一对应，卡片是否含必需小节
  5. 8 个整包是否存在
  6. 00-索引.md 里的链接是否都能打开
  7. index.json 是否与 cards.json 同步
  8. checklist.json 条数与 harm 字段
  9. search.py 能否正常跑一次检索
 10. 检索站 site/index.html 内嵌卡数是否同步、是否完全自包含
 11. 02-引用与来源.md 是否逐卡溯源、是否含 DOI 与上游仓库
 12. 文档互链（README ↔ 使用说明 / 自部署说明 / 引用 / 变更记录）
 13. 上游原文是否齐（不随包分发；有则校验，无则提示补取）
 14. app 清单同步（app 里的 58 条 == checklist.json 生成结果）

全部通过退出码 0；有失败退出码 1，并列出失败项。
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent

RESULTS = []


def check(name, fn):
    try:
        detail = fn()
        RESULTS.append((True, name, detail or ""))
    except AssertionError as e:
        RESULTS.append((False, name, str(e)))
    except Exception as e:  # 未预期的错误也算失败
        RESULTS.append((False, name, f"{type(e).__name__}: {e}"))


# ---------------------------------------------------------------- 1 结构
REQUIRED_DIRS = ["知识库", "知识库/cards", "数据与脚本",
                 "site", ".github/workflows"]
REQUIRED_FILES = [
    "02-引用与来源.md",
    "01-使用说明.md",
    "03-持续更新.md",
    "CHANGELOG.md",
    "LICENSE",
    "LICENSE-内容-CC-BY-4.0.md",
    ".gitignore",
    ".github/workflows/selfcheck.yml",
    "知识库/00-索引.md",
    "知识库/index.json",
    "site/index.html",
    "数据与脚本/cards.json",
    "数据与脚本/checklist.json",
    "数据与脚本/render.py",
    "数据与脚本/build_kb.py",
    "数据与脚本/build_site.py",
    "数据与脚本/build_refs.py",
    "数据与脚本/fetch_sources.py",
    "数据与脚本/deploy.py",
    "数据与脚本/search.py",
]


def t_structure():
    missing = [d for d in REQUIRED_DIRS if not (PKG / d).is_dir()]
    missing += [f for f in REQUIRED_FILES if not (PKG / f).is_file()]
    # 嵌在别的仓库里（如 lifeOS 的 kb/）时，workflow 必须放在那个仓库的根 .github/
    # —— GitHub 只认仓库根，所以这里不要求 kb/.github/ 存在
    if missing and any(m.startswith(".github/") for m in missing):
        for base in (PKG.parent, PKG.parent.parent):
            wf = base / ".github" / "workflows"
            if wf.is_dir() and any(wf.glob("*.y*ml")):
                missing = [m for m in missing if not m.startswith(".github/")]
                break
    assert not missing, f"缺 {len(missing)} 项：{missing}"
    return f"{len(REQUIRED_DIRS)} 目录 / {len(REQUIRED_FILES)} 文件"


# ---------------------------------------------------------------- 2 cards.json
CARD_FIELDS = ["id", "level", "section", "title", "do", "harm", "evidence", "grade", "source", "keywords"]
LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5", "L6", "DONT"}
GRADES = {"A", "B", "C", "D", "-"}


def load_cards():
    return json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))["cards"]


def t_cards_json():
    cards = load_cards()
    assert len(cards) == 66, f"卡片数 {len(cards)}，期望 66"
    ids = [c["id"] for c in cards]
    assert len(set(ids)) == len(ids), "存在重复 id"
    problems = []
    for c in cards:
        miss = [f for f in CARD_FIELDS if not c.get(f)]
        if miss:
            problems.append(f"{c.get('id', '?')} 缺 {miss}")
        if c.get("level") not in LEVELS:
            problems.append(f"{c.get('id')} 层级非法 {c.get('level')}")
        if c.get("grade") not in GRADES:
            problems.append(f"{c.get('id')} 分级非法 {c.get('grade')}")
        if not isinstance(c.get("do"), list) or len(c["do"]) < 2:
            problems.append(f"{c.get('id')} 的 do 少于 2 步")
    assert not problems, "; ".join(problems[:5])
    return f"{len(cards)} 张，{len(set(ids))} 唯一 id"


def t_related():
    cards = load_cards()
    ids = {c["id"] for c in cards}
    bad = sorted({r for c in cards for r in c.get("related", []) if r not in ids})
    assert not bad, f"related 指向不存在的卡：{bad}"
    return "全部 related 有效"


# ---------------------------------------------------------------- 3 卡片文件
def t_card_files():
    cards = load_cards()
    files = {p.stem for p in (PKG / "知识库" / "cards").glob("*.md")}
    ids = {c["id"] for c in cards}
    assert files == ids, f"多 {sorted(files - ids)} / 少 {sorted(ids - files)}"
    need = ["## 怎么做", "## 不做的后果", "## 证据"]
    bad = []
    for p in (PKG / "知识库" / "cards").glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        miss = [h for h in need if h not in txt]
        if miss:
            bad.append(f"{p.name} 缺 {miss}")
    assert not bad, "; ".join(bad[:5])
    return f"{len(files)} 个文件，均含三个必需小节"


# ---------------------------------------------------------------- 4 整包
BUNDLES = [
    "L0-一票否决", "L1-每天", "L2-每周", "L3-每年或按年龄",
    "L4-出事那一刻", "L5-一次性办完", "L6-情绪与心理", "L9-省钱的别做",
]


def t_bundles():
    missing = [b for b in BUNDLES if not (PKG / "知识库" / f"{b}.md").is_file()]
    assert not missing, f"缺整包：{missing}"
    return f"{len(BUNDLES)} 个整包齐全"


# ---------------------------------------------------------------- 5 索引链接
def t_index_links():
    kb = PKG / "知识库"
    idx = (kb / "00-索引.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+\.md)\)", idx)
    missing = [l for l in links if not (kb / l).exists()]
    assert not missing, f"{len(missing)} 个链接打不开：{missing[:5]}"
    return f"{len(links)} 条链接全部可打开"


# ---------------------------------------------------------------- 6 index.json
def t_index_json():
    kb = PKG / "知识库"
    data = json.loads((kb / "index.json").read_text(encoding="utf-8"))
    cards = load_cards()
    assert data.get("count") == len(cards), f"index.count={data.get('count')}，cards={len(cards)}"
    ids_idx = {c["id"] for c in data["cards"]}
    ids_card = {c["id"] for c in cards}
    assert ids_idx == ids_card, "index.json 与 cards.json 的 id 集合不一致"
    bad = [c["path"] for c in data["cards"] if not (PKG / c["path"]).is_file()]
    assert not bad, f"{len(bad)} 个 path 不存在：{bad[:3]}"
    return f"{data['count']} 条，path 全部存在"


# ---------------------------------------------------------------- 7 checklist
def t_checklist():
    data = json.loads((ROOT / "checklist.json").read_text(encoding="utf-8"))
    items = [i for s in data["sections"] for i in s["items"]] + data["donts"]["items"]
    assert len(items) == 58, f"清单共 {len(items)} 条，期望 58"
    bad = [i["t"][:12] for i in items if not i.get("harm")]
    assert not bad, f"{len(bad)} 条没写危害：{bad[:3]}"
    return f"{len(items)} 条，均含危害"


# ---------------------------------------------------------------- 8 search
def t_search():
    py = sys.executable
    env_line = subprocess.run(
        [py, str(ROOT / "search.py"), "打鼾", "-n", "3"],
        capture_output=True, encoding="utf-8", errors="replace",
        env={"PYTHONIOENCODING": "utf-8", "PATH": ""},
        timeout=60,
    )
    assert env_line.returncode == 0, f"退出码 {env_line.returncode}：{env_line.stderr[:200]}"
    assert "打鼾" in env_line.stdout, "检索「打鼾」没有返回结果"
    assert "snoring-osa" in env_line.stdout, "检索「打鼾」没有命中 snoring-osa"
    return "检索「打鼾」命中 snoring-osa"


# ---------------------------------------------------------------- 11 检索站
def t_site():
    html = PKG / "site" / "index.html"
    s = html.read_text(encoding="utf-8")
    m = re.search(r'<script id="data"[^>]*>(.*?)</script>', s, re.S)
    assert m, "site/index.html 里找不到内嵌数据块"
    page = json.loads(m.group(1))
    cards = load_cards()
    ids_page = {c["id"] for c in page["cards"]}
    ids_card = {c["id"] for c in cards}
    assert ids_page == ids_card, \
        f"站点与 cards.json 不同步：多 {sorted(ids_page - ids_card)[:3]} / 少 {sorted(ids_card - ids_page)[:3]}"
    ext = re.findall(r'<(?:script[^>]*src|link[^>]*href|img[^>]*src)\s*=\s*["\'](?:https?:)?//', s)
    assert not ext, f"站点引用了外部资源（应完全自包含）：{ext[:3]}"
    return f"{len(page['cards'])} 张卡内嵌，无外部引用，{html.stat().st_size:,} B"


# ---------------------------------------------------------------- 12 引用文档
def t_refs():
    txt = (PKG / "02-引用与来源.md").read_text(encoding="utf-8")
    cards = load_cards()
    miss = [c["id"] for c in cards if f"### `{c['id']}`" not in txt]
    assert not miss, f"{len(miss)} 张卡没有溯源小节：{miss[:3]}"
    assert "卡片未标注来源" not in txt, "有卡片没有溯源（检查 build_refs 的分支是否漏 return）"
    assert "台账中未定位" not in txt, "有 HTL 卡片没匹配到台账记录"
    assert "卡片未标注来源" not in txt, "有卡片没有溯源（检查 build_refs 的分支是否漏 return）"
    assert "台账中未定位" not in txt, "有 HTL 卡片没匹配到台账记录"
    dois = re.findall(r"doi\.org/", txt)
    assert len(dois) >= 100, f"DOI 链接只有 {len(dois)} 个，期望 ≥100"
    for repo in ("geekan/HowToLiveLonger", "eternity4719/HowToLiveBetter",
                 "Anduin2017/HowToCook", "zijie0/HumanSystemOptimization"):
        assert repo in txt, f"引用文档缺上游仓库：{repo}"
    assert "无许可证" in txt, "引用文档没写 HumanSystemOptimization 的许可证问题"
    return f"{len(cards)} 张卡全部溯源，DOI 链接 {len(dois)} 个"


# ---------------------------------------------------------------- 13 文档互链
def t_docs_links():
    # 仓库根 README（lifeOS 的首页）由 部署-lifeOS/README-仓库首页.md 生成
    home = PKG.parent / "README.md"
    need = ["02-引用与来源.md", "01-使用说明.md",
            "03-持续更新.md", "CHANGELOG.md", "site/index.html"]
    if home.is_file():
        readme = home.read_text(encoding="utf-8")
        miss = [n for n in need if n not in readme]
        assert not miss, f"仓库首页 README 没有指向：{miss}"
    else:
        miss = [n for n in need if not (PKG / n).exists()]
        assert not miss, f"缺文档：{miss}"
    use = (PKG / "01-使用说明.md").read_text(encoding="utf-8")
    assert "02-引用与来源.md" in use, "使用说明没有指向引用文档（署名要求）"
    assert "03-持续更新.md" in use, "使用说明没有指向持续更新文档"
    return "README（仓库首页）→ 使用说明/引用/更新/变更，互链完整"


# ---------------------------------------------------------------- 14 上游原文
def t_sources():
    """原始资料/ 不随包分发（版权原因），有则校验，无则给出补取命令。"""
    src = PKG / "原始资料"
    book = src / "HLB_book"
    if not src.is_dir():
        return "未取原文（可跑 fetch_sources.py 补；不影响使用，只影响重新生成引用）"
    needed = ["HowToLiveLonger_evidence.json", "HowToLiveBetter_README.md",
              "HumanSystemOptimization_README.md", "HowToCook_README.md"]
    missing = [f for f in needed if not (src / f).is_file()]
    assert not missing, f"原始资料缺：{missing}"
    chapters = sorted(p.name for p in book.glob("*.md")) if book.is_dir() else []
    assert len(chapters) >= 10, f"HLB 正文只有 {len(chapters)} 章，期望 ≥10"
    return f"HLB 正文 {len(chapters)} 章 + 4 份上游台账齐全"


def t_app_sync():
    """app（lifeOS）的清单必须由 checklist.json 生成，且每条深链指向真实卡片。"""
    app = PKG.parent / "index.html"
    if not app.is_file():
        return "无同仓库 app，跳过"

    src = app.read_text(encoding="utf-8")
    if "<<KB-CHECK-START>>" not in src:
        return "app 未接入知识库，跳过"
    assert ('id="hKb"' in src) or ('data-href="kb/site/"' in src), \
        "app 里没有知识库入口（首屏右上角应是 id=\"hKb\"）"

    # 用 build_app.py 的同一套逻辑重算，逐字节比对
    spec = importlib.util.spec_from_file_location("build_app", ROOT / "build_app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cl, cards = m.load()
    secs, problems = m.build_sections(cl, cards)
    assert not problems, f"清单数据有问题：{problems[:3]}"

    want = m.render_block(secs)
    pat = re.compile(re.escape(m.START) + r".*?" + re.escape(m.END), re.S)
    cur = pat.search(src)
    assert cur, "app 里的生成标记不完整"
    assert cur.group(0) == want, "app 清单与 checklist.json 不同步（跑 build_app.py）"

    total = sum(len(x["items"]) for x in secs)
    linked = sum(1 for x in secs for i in x["items"] if i.get("card"))
    return f"{len(secs)} 组 / {total} 条，{linked} 条深链全部有效"


def main():
    ci = "--ci" in sys.argv        # CI 里没有 原始资料/（版权原因不分发）
    print(f"成果包：{PKG}" + ("（CI 模式）" if ci else "") + "\n")
    checks = [
        ("结构完整性", t_structure),
        ("cards.json 结构", t_cards_json),
        ("related 指向", t_related),
        ("卡片文件对照", t_card_files),
        ("整包齐全", t_bundles),
        ("索引链接", t_index_links),
        ("index.json 同步", t_index_json),
        ("清单条目", t_checklist),
        ("检索脚本", t_search),
        ("检索站", t_site),
        ("引用溯源", t_refs),
        ("文档互链", t_docs_links),
        ("上游原文", t_sources),
        ("app 清单同步", t_app_sync),
    ]
    if ci:
        # 上游原文只在本地有：CI 里跳过，不当作失败
        checks = [(n, f) for n, f in checks if n != "上游原文"]
    for name, fn in checks:
        check(name, fn)

    width = max(len(n) for n, _ in checks) + 2
    for ok, name, detail in RESULTS:
        mark = "✔" if ok else "✘"
        print(f"{mark} {name:<{width}} {detail}")

    failed = [r for r in RESULTS if not r[0]]
    print()
    if failed:
        print(f"❌ {len(failed)} 项失败 / 共 {len(RESULTS)} 项")
        return 1
    print(f"✅ 全部 {len(RESULTS)} 项通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
