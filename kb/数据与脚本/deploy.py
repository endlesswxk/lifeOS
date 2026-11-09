# -*- coding: utf-8 -*-
"""一条命令走完「重建 → 自检 → 提交 → 推送 → 线上校验」。

用法：
    python 数据与脚本/deploy.py                  # 重建 + 自检 + 提交（不推送）
    python 数据与脚本/deploy.py --push           # 再加推送（含 tag）
    python 数据与脚本/deploy.py --push --verify https://endlesswxk.github.io/health-kb/
    python 数据与脚本/deploy.py --version 1.3 --push   # 先升版本号再跑
    python 数据与脚本/deploy.py --upstream       # 只检查上游原文有没有更新

设计约定：
  * 只用标准库；token 不进本脚本，靠 git 自己的凭据助手（见 05-持续更新.md）
  * 自检不过就中止，绝不把没校验的内容推上去
  * 没有内容变化就干净退出，不产生空提交
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
PY = sys.executable


def run(cmd, cwd=PKG, check=True, capture=True):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=capture,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        out = (r.stdout or "") + (r.stderr or "")
        raise SystemExit(f"✘ 失败：{' '.join(str(c) for c in cmd)}\n{out.strip()[:1500]}")
    return r


def step(msg):
    print(f"\n── {msg} " + "─" * max(0, 46 - len(msg)))


def cards_meta():
    d = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
    return d["meta"]["version"], len(d["cards"])


def bump_version(new):
    p = ROOT / "cards.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    old = d["meta"]["version"]
    d["meta"]["version"] = new
    d["meta"]["built_at"] = date.today().isoformat()
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  版本 {old} → {new}（built_at → {d['meta']['built_at']}）")


def rebuild():
    step("重建派生物")
    for s in ("build_kb.py", "build_site.py", "build_refs.py"):
        run([PY, str(ROOT / s)])
        print(f"  ✔ {s}")


def selfcheck():
    step("一致性自检")
    r = run([PY, str(ROOT / "自检.py")], check=False)
    tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-3:]
    for l in tail:
        print("  " + l)
    if r.returncode != 0:
        raise SystemExit("✘ 自检未通过，已中止（没有提交、没有推送）")


def git(*args, check=True):
    return run(["git", *args], check=check)


def has_changes():
    return bool(git("status", "--porcelain", check=False).stdout.strip())


def commit(version, n_cards, message=None):
    step("提交")
    git("add", "-A")
    staged = git("diff", "--cached", "--name-only").stdout.strip().splitlines()
    if not staged:
        print("  没有内容变化，跳过提交")
        return False
    msg = message or f"update: v{version} · {n_cards} 张卡 · {date.today().isoformat()}"
    ident = ["-c", "user.name=endlesswxk", "-c", "user.email=endlesswxk@users.noreply.github.com"]
    r = run(["git", *ident, "commit", "-m", msg], check=False)
    if r.returncode != 0:  # 本地已配好身份时用不着 -c，再试一次裸提交
        git("commit", "-m", msg)
    print(f"  ✔ {msg}")
    print(f"  改动 {len(staged)} 个文件")
    return True


def push(tag):
    step("推送")
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    remote = git("remote", check=False).stdout.strip()
    if not remote:
        raise SystemExit(
            "✘ 还没设置 remote。先执行：\n"
            "  git remote add origin https://github.com/<用户名>/<仓库名>.git\n"
            "  （然后把 token 存进凭据助手，见 05-持续更新.md）"
        )
    args = ["push", "origin", branch]
    if tag:
        git("tag", "-f", tag)
        args += ["--tags"]
    r = run(["git", *args], check=False)
    if r.returncode != 0:
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        if "Authentication" in out or "could not read Username" in out or "403" in out:
            raise SystemExit(
                "✘ 推送需要凭据。两种做法：\n"
                "  1) 一次性：git config --global credential.helper manager  然后手动 push 一次\n"
                "  2) 或用 GitHub CLI：gh auth login\n"
                "  token 权限至少要 Contents: Read and write + Workflows: Read and write"
            )
        raise SystemExit(f"✘ 推送失败：\n{out[:1200]}")
    print("  ✔ 已推送")


def verify(url, version):
    step(f"线上校验 {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "health-kb-deploy/1.3",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read().decode("utf-8", "replace")
            print(f"  HTTP {r.status} · {len(body):,} 字符")
    except Exception as e:
        raise SystemExit(f"✘ 打不开：{type(e).__name__}: {e}（Pages 可能还在构建，等 1–3 分钟再试）")
    if f"版本 {version}" in body:
        print(f"  ✔ 页面上已是 v{version}")
    else:
        print(f"  ⚠ 页面里没找到「版本 {version}」——可能是缓存，让对方 Ctrl+F5，或等 Pages 生效")
    if "<script id=\"data\"" not in body:
        raise SystemExit("✘ 页面里没有内嵌数据块，站点可能不完整")


def _norm_bytes(b):
    """去掉 UTF-8 BOM 并统一换行，用于判断「上游内容真的变了吗」。"""
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    return b.replace(b"\r\n", b"\n")


def check_upstream():
    """重新抓上游原文，报告哪些章/台账变了。"""
    step("上游变更检测")
    spec = importlib.util.spec_from_file_location("fetch_sources", ROOT / "fetch_sources.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    changed, failed = [], []
    for rel, url in m.TARGETS:
        p = m.target_path(rel)
        old = p.read_bytes() if p.is_file() else b""
        try:
            m.fetch(rel, url, force=True)
        except Exception as e:
            failed.append(f"{rel}（{type(e).__name__}）")
            continue
        new = p.read_bytes()
        # 只比「内容」：去 BOM、统一换行，避免工具差异被误报成上游更新
        if _norm_bytes(old) != _norm_bytes(new):
            changed.append((rel, "新增" if not old else f"{len(old):,} → {len(new):,} B"))

    if failed:
        print("  ⚠ 抓取失败：" + "、".join(failed))
    if not changed:
        print("  ✔ 上游没有变化")
        return
    print(f"  发现 {len(changed)} 个文件有变化：")
    for rel, how in changed:
        print(f"    · {rel}  （{how}）")
    print("\n  下一步：跑 `python 数据与脚本/deploy.py` 重建引用，再看 diff 决定要不要改卡。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="先升到指定版本号，如 1.3")
    ap.add_argument("--message", "-m", help="自定义提交信息")
    ap.add_argument("--push", action="store_true", help="提交后推送（自动打 tag v<版本>）")
    ap.add_argument("--verify", metavar="URL", help="推送后校验线上地址")
    ap.add_argument("--upstream", action="store_true", help="只检查上游原文是否更新")
    ap.add_argument("--skip-rebuild", action="store_true", help="跳过重建（只提交已有改动）")
    args = ap.parse_args()

    if args.upstream:
        check_upstream()
        return 0

    print(f"成果包：{PKG}")
    if args.version:
        bump_version(args.version)

    if not args.skip_rebuild:
        rebuild()
    selfcheck()

    version, n_cards = cards_meta()
    if has_changes() or args.message:
        commit(version, n_cards, args.message)
    if args.push:
        push(f"v{version}")
    if args.verify:
        verify(args.verify, version)

    print(f"\n完成（v{version} · {n_cards} 张卡）")
    if not args.push:
        print("提示：加 --push 才会推送到 GitHub。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
