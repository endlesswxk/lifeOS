# -*- coding: utf-8 -*-
"""按需重新抓取上游原文到 原始资料/。

为什么需要它：上游原文**不随本包分发**。两个原因——
  1. 有些项目没有许可证（HumanSystemOptimization），再分发原文有版权风险；
  2. 原文本会随上游更新而变，链一份快照容易过期。

所以 `02-引用与来源.md` 里的每条 DOI 都能靠这个脚本重新核对。

    python 数据与脚本/fetch_sources.py            # 缺什么抓什么
    python 数据与脚本/fetch_sources.py --force    # 全部重抓
    python 数据与脚本/fetch_sources.py --check    # 只检查本地是否齐全，不联网

只用标准库（urllib），不装 requests。
"""
import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com"
OUT = Path(__file__).resolve().parent.parent / "原始资料"

# HLB 正文章节：卡片引用了 §1 §2 §3 §6 §8 §13 §16 §22 §29 §34
HLB_CHAPTERS = [
    "01-不要早死", "02-不要慢慢死", "03-不要浪费精力", "06-反面清单",
    "08-别把自己搭进去", "13-紧急情况", "16-得了慢性病之后怎么活",
    "22-怎么放松", "29-遭遇重大打击之后", "34-家里的常备药别吃出事",
]

# (本地路径, URL)
TARGETS = [
    ("HowToLiveBetter_README.md",
     f"{RAW}/eternity4719/HowToLiveBetter/main/README.md"),
    ("HowToLiveLonger_README.md",
     f"{RAW}/geekan/HowToLiveLonger/main/README.md"),
    ("HowToLiveLonger_evidence.json",
     f"{RAW}/geekan/HowToLiveLonger/main/data/evidence.json"),
    ("HumanSystemOptimization_README.md",
     f"{RAW}/zijie0/HumanSystemOptimization/main/README.md"),
    ("HowToCook_README.md",
     f"{RAW}/Anduin2017/HowToCook/master/README.md"),
] + [
    (f"HLB_book/{ch}.md",
     f"{RAW}/eternity4719/HowToLiveBetter/main/book/{urllib.parse.quote(ch)}.md")
    for ch in HLB_CHAPTERS
]


def target_path(rel):
    return OUT / rel


def is_present(rel):
    p = target_path(rel)
    return p.is_file() and p.stat().st_size > 1000


def fetch(rel, url, force=False, timeout=60):
    p = target_path(rel)
    if is_present(rel) and not force:
        return "skip", p.stat().st_size
    p.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "health-kb-fetch/1.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if len(data) < 500:
        raise RuntimeError(f"取回内容过短（{len(data)} B），可能 URL 已变")
    p.write_bytes(data)
    return "ok", len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="已存在也重抓")
    ap.add_argument("--check", action="store_true", help="只检查，不联网")
    args = ap.parse_args()

    ok = skip = fail = 0
    for rel, url in TARGETS:
        if args.check:
            state = "ok" if is_present(rel) else "缺"
            size = target_path(rel).stat().st_size if is_present(rel) else 0
            print(f"[{state:>2}] {rel:<42} {size:>9,} B")
            if is_present(rel):
                ok += 1
            else:
                fail += 1
            continue
        try:
            state, size = fetch(rel, url, force=args.force)
            print(f"[{state:>4}] {rel:<42} {size:>9,} B")
            ok += state == "ok"
            skip += state == "skip"
        except Exception as e:
            print(f"[FAIL] {rel:<42} {type(e).__name__}: {e}")
            fail += 1

    print()
    print(f"完成：抓取 {ok} · 跳过 {skip} · 失败 {fail}")
    if fail:
        print("缺文件时 build_refs.py 会退化：只能标到「第几节」，给不出条目号与 DOI。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
