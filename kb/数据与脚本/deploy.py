# -*- coding: utf-8 -*-
"""一条命令走完「重建 → 自检 → 提交 → 推送 → 线上校验」。

用法：
    python 数据与脚本/deploy.py                  # 重建 + 自检 + 提交（不推送）
    python 数据与脚本/deploy.py --push           # 再加推送（含 tag）
    python 数据与脚本/deploy.py --push --verify https://endlesswxk.github.io/lifeOS/kb/site/
    python 数据与脚本/deploy.py --version 1.3 --push   # 先升版本号再跑
    python 数据与脚本/deploy.py --upstream       # 只检查上游原始有没有更新
    python 数据与脚本/deploy.py --sync-lifeos    # 同步 kb/ + sw.js 到 lifeOS 仓库并推送

设计约定：
  * 只用标准库；token 不进本脚本，靠 git 自己的凭据助手（见 03-持续更新.md）
  * 自检不过就中止，绝不把没校验的内容推上去
  * 没有内容变化就干净退出，不产生空提交
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
PY = sys.executable


# 任何 git 子进程都不许拉登录窗：没凭据就直接失败，而不是弹窗等人点。
NO_PROMPT = {
    "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "SSH_ASKPASS": "",
    "GIT_CONFIG_COUNT": "1",                 # 让子进程不调用系统里的 credential.helper
    "GIT_CONFIG_KEY_0": "credential.helper",
    "GIT_CONFIG_VALUE_0": "",
}


def _env(extra=None):
    e = dict(os.environ)
    e.update(NO_PROMPT)
    e.update(extra or {})
    return e


def run(cmd, cwd=PKG, check=True, capture=True, env=None):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=capture,
                       encoding="utf-8", errors="replace", env=_env(env))
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
            "  （然后把 token 存进凭据助手，见 03-持续更新.md）"
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



PUBLISH_EXCLUDE = ("部署-lifeOS/",)   # 只有本地部署须知不进公开仓库
# 本机配置放在 数据与脚本/.local.json（已在 .gitignore 里，不进仓库）。
# 别人用这份包时不需要它：没配就退回 git 自己的凭据助手。
LOCAL_CFG = ROOT / ".local.json"


def local_cfg():
    try:
        return json.loads(LOCAL_CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}


_CFG = local_cfg()
CRED_NAME = os.environ.get("CRED_NAME") or _CFG.get("cred_name", "")
CREDMAN = os.environ.get("CREDMAN_SCRIPT") or _CFG.get("cred_script", "")


def cred_secret(name):
    """从可选的凭据脚本取 secret；没配置或取不到就返回空串。不打印。"""
    if not CREDMAN or not Path(CREDMAN).is_file():
        return ""
    r = subprocess.run(["pwsh", "-NoProfile", "-Command",
                        f'& "{CREDMAN}" get -Name {name} -Field secret'],
                       capture_output=True, text=True, encoding="utf-8")
    return (r.stdout or "").strip() if r.returncode == 0 else ""


LIFEOS_DEFAULT = (os.environ.get("LIFEOS_REPO") or _CFG.get("lifeos_repo")
                  or str(PKG.parent / "lifeOS"))


def sync_lifeos(repo_path, do_push):
    """把知识库同步进 lifeOS 仓库：kb/ + kb/index.html 跳转页 + sw.js，并重生成 app 清单。"""
    import shutil

    repo = Path(repo_path)
    if not (repo / ".git").is_dir():
        raise SystemExit(f"✘ 不是 git 仓库：{repo}\n  先 git clone https://github.com/endlesswxk/lifeOS.git {repo}")

    step(f"同步到 lifeOS：{repo}")
    url0 = run(["git", "-C", str(repo), "remote", "get-url", "origin"]).stdout.strip()
    tok0 = cred_secret(CRED_NAME)
    if tok0 and url0.startswith("https://"):
        user0 = _CFG.get("git_user", "endlesswxk")
        pull = run(["git", "-C", str(repo), "pull", "--ff-only",
                    re.sub(r"^https://", f"https://{user0}:{tok0}@", url0)], check=False)
        pull_msg = (((pull.stdout or "") + (pull.stderr or "")).replace(tok0, "***")).strip()
    else:
        pull = run(["git", "-C", str(repo), "pull", "--ff-only"], check=False)
        pull_msg = ((pull.stdout or "") + (pull.stderr or "")).strip()
    print("  " + pull_msg[:200])

    # 1) kb/ = 本包的全部跟踪文件（跳过 .github，workflow 只认仓库根）
    out = run(["git", "-C", str(PKG), "-c", "core.quotepath=false", "ls-files", "-z"]).stdout
    allf = [f for f in out.split("\0") if f.strip()]
    files = [f for f in allf if not f.startswith(".github/")
             and not any(f.startswith(x) for x in PUBLISH_EXCLUDE)]
    internal = [f for f in allf if any(f.startswith(x) for x in PUBLISH_EXCLUDE)]
    kb = repo / "kb"
    copied = 0
    for rel in files:
        src, dst = PKG / rel, kb / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f"  kb/ 写入 {copied} 个文件")
    if internal:
        names = ", ".join(sorted({x.split("/")[0] for x in internal}))
        print(f"  跳过 {len(internal)} 个内部文件（不公开）：{names}")

    # 根目录 CI 只对维护者有用，不进公开仓库
    ci = repo / ".github" / "workflows" / "kb-selfcheck.yml"
    if ci.is_file():
        ci.unlink()
        print("  移除根目录 CI（kb-selfcheck.yml）")
        for d in (ci.parent, ci.parent.parent):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()

    # 2) 清理 kb/ 里已从本包删除的旧文件
    tracked_kb = run(["git", "-C", str(repo), "-c", "core.quotepath=false", "ls-files", "-z", "kb"]).stdout
    removed = 0
    for f in [x for x in tracked_kb.split("\0") if x.strip()]:
        rel = f[3:] if f.startswith("kb/") else None
        if rel and rel not in files and (kb / rel).exists():
            (kb / rel).unlink()
            removed += 1
    if removed:
        print(f"  kb/ 删除 {removed} 个已不存在的旧文件")
    # 顺手清空目录残渣
    for d in sorted([x for x in kb.rglob("*") if x.is_dir()], key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()

    # 3) kb/index.html 跳转页（静态，永不与 site/ 不同步）
    (kb / "index.html").write_text(REDIRECT_PAGE, encoding="utf-8")

    # 4) sw.js（从本包 部署-lifeOS/sw.js 拷过去）
    sw = PKG / "部署-lifeOS" / "sw.js"
    if sw.is_file():
        shutil.copy2(sw, repo / "sw.js")
        ver = re.search(r"const CACHE = '([^']+)'", sw.read_text(encoding="utf-8"))
        print(f"  sw.js → {ver.group(1) if ver else '?'}")

    # 5) 仓库首页 README（GitHub 上没有它会显示「Add a README」）
    # 根 .gitignore 兜底（防本机私有文件被误提交）
    gi = PKG / "部署-lifeOS" / "gitignore-仓库根"
    if gi.is_file():
        shutil.copy2(gi, repo / ".gitignore")

    # 校验型 CI（只做检查，不生成内容）
    wfdir = repo / ".github" / "workflows"
    src_wf = PKG / "部署-lifeOS" / "github-workflows"
    if src_wf.is_dir():
        wfdir.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_wf.glob("*.yml")):
            shutil.copy2(f, wfdir / f.name)
        for stale in wfdir.glob("*.yml"):
            if not (src_wf / stale.name).is_file():
                stale.unlink()
        print(f"  .github/workflows → {len(list(src_wf.glob('*.yml')))} 个（校验型 CI）")

    home = PKG / "部署-lifeOS" / "README-仓库首页.md"
    if home.is_file():
        shutil.copy2(home, repo / "README.md")
        print("  README.md → 仓库首页")
    if gi.is_file():
        print("  .gitignore → 仓库根（兜底）")

    # 6) 重新生成 app 里的清单（含跳知识库的链接）
    app = repo / "index.html"
    if app.is_file():
        r = run([PY, str(ROOT / "build_app.py"), "--app", str(app)], check=False)
        print("  " + (r.stdout or "").strip().replace("\n", "\n  "))

    # 7) 提交
    st = run(["git", "-C", str(repo), "status", "--porcelain"]).stdout.strip()
    if not st:
        print("  没有变化，跳过提交")
    else:
        n = len(st.splitlines())
        ident = ["-c", "user.name=endlesswxk", "-c", "user.email=endlesswxk@users.noreply.github.com"]
        version, _ = cards_meta()
        run(["git", "-C", str(repo), "add", "-A"], check=True)   # 别忘了 add
        run(["git", "-C", str(repo), *ident, "commit", "-q", "-m",
             f"kb: 同步知识库 v{version}（{n} 个文件）"], check=True)
        left = run(["git", "-C", str(repo), "status", "--porcelain"]).stdout.strip()
        assert not left, f"提交后仍有未提交改动：{left[:200]}"
        print(f"  已提交 {n} 个文件")

    if do_push:
        url = run(["git", "-C", str(repo), "remote", "get-url", "origin"]).stdout.strip()
        tok = cred_secret(CRED_NAME)
        if tok and url.startswith("https://"):
            user = _CFG.get("git_user", "endlesswxk")
            auth = re.sub(r"^https://", f"https://{user}:{tok}@", url)   # 直接带 token，不弹窗
            r = run(["git", "-C", str(repo), "push", auth, "HEAD:main"], check=False)
            out2 = (((r.stdout or "") + (r.stderr or "")).replace(tok, "***")).strip()
        else:
            r = run(["git", "-C", str(repo), "push", "origin", "HEAD:main"], check=False)
            out2 = ((r.stdout or "") + (r.stderr or "")).strip()
        if r.returncode != 0:
            raise SystemExit(
                "✘ 推送失败（没有可用凭据）：\n" + out2[:600] +
                "\n  在 数据与脚本/.local.json 里配 cred_name + cred_script，"
                "或先配一次 git 凭据助手（见 03-持续更新.md）")
        print("  已推送 → https://github.com/endlesswxk/lifeOS")
    else:
        print("  提示：加 --push 才会推送")


REDIRECT_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>个人健康知识库</title>
<meta http-equiv="refresh" content="0; url=site/">
<link rel="canonical" href="site/">
<style>
  body{margin:0;min-height:100vh;display:grid;place-items:center;
       font:16px/1.6 -apple-system,"Segoe UI","Noto Sans SC","Microsoft YaHei",sans-serif;
       background:#f7f7f5;color:#1c1c1e;text-align:center;padding:2rem}
  a{color:#2e7d8f}
  @media (prefers-color-scheme:dark){body{background:#131416;color:#e9e9ea}a{color:#63b7c8}}
</style>
</head>
<body>
<div>
  <p>正在打开个人健康知识库…</p>
  <p><a href="site/">如果没有自动跳转，点这里</a></p>
</div>
<script>location.replace("site/");</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="先升到指定版本号，如 1.3")
    ap.add_argument("--message", "-m", help="自定义提交信息")
    ap.add_argument("--push", action="store_true", help="提交后推送（自动打 tag v<版本>）")
    ap.add_argument("--verify", metavar="URL", help="推送后校验线上地址")
    ap.add_argument("--upstream", action="store_true", help="只检查上游原文是否更新")
    ap.add_argument("--skip-rebuild", action="store_true", help="跳过重建（只提交已有改动）")
    ap.add_argument("--sync-lifeos", nargs="?", const=LIFEOS_DEFAULT, metavar="REPO",
                    help=f"同步 kb/ + sw.js 到 lifeOS 仓库（默认 {LIFEOS_DEFAULT}）")
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
    if args.push and not args.sync_lifeos:
        push(f"v{version}")   # 独立仓库推送；同步 lifeOS 时由 sync_lifeos 负责
    if args.verify:
        verify(args.verify, version)

    if args.sync_lifeos:
        sync_lifeos(args.sync_lifeos, args.push)

    print(f"\n完成（v{version} · {n_cards} 张卡）")
    if not args.push:
        print("提示：加 --push 才会推送到 GitHub。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
