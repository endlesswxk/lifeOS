# 个人健康知识库 · 成果包

一句话：把 4 个 GitHub 知识仓库（HowToLiveLonger / HumanSystemOptimization / HowToLiveBetter /
HowToCook）里的健康知识，压成**一张能打的 A4 清单**＋**一个能搜的网页版**＋**一个可检索、可溯源的知识库**。

- 版本 **v1.4** · 建成 2026-11-09
- 规模：一页纸 **58 条**（6 层 + 「别做」）；知识库 **66 张卡 + 8 个整包**（多出的一层是
  `L6 情绪与心理` 8 张，源为 HLB §1、§29 正文原文）
- 事实核对：HowToLiveLonger 的 **64 条**研究台账（含 HR/RR、样本、分级）逐条解析；
  HowToLiveBetter **10 章正文、308 条条目**（每条带 95%CI、证据等级与 DOI，存在 `原始资料/HLB_book/`）；
  HowToCook 的食品安全与厨房准备原文核对。**逐卡溯源见 `02-引用与来源.md`（131 个 DOI 链接）。**

---

## 包里有什么

```
个人健康知识库成果/
├─ README.md                    ← 你正在读的这份（总入口）
├─ 03-使用说明.md                ← 给拿到包的人：三种用法、证据等级怎么读、FAQ
├─ 04-自部署说明.md              ← 放到网上给别人用：本地 / 局域网 / GitHub Pages
├─ 05-持续更新.md                ← 改一次成本 = 一条命令；上游更新怎么跟；token 怎么存一次
├─ 02-引用与来源.md              ← 逐卡溯源到原文条目与论文 DOI（自动生成）
├─ CHANGELOG.md                  ← 版本变更
│
└─ （内部工作笔记：源分析、缺口清单。只在本地维护，不随公开版发布）
├─ LICENSE                       ← 代码 MIT
├─ LICENSE-内容-CC-BY-4.0.md      ← 文本 CC BY 4.0 + 上游署名要求
│
├─ 一页纸清单/                    ← 打印用，A4 实测 1 页
│   ├─ 个人健康检查清单.pdf
│   ├─ 个人健康检查清单.html      ← 可勾选、自动计数、状态存本地
│   └─ 个人健康检查清单.md
├─ site/                         ← 网页版，双击即开，不需要装任何东西
│   ├─ index.html                ← 66 张卡内嵌：搜索、层级筛选、证据筛选、离线可用
│   └─ .nojekyll                 ← 部署到 GitHub Pages 必需
├─ 知识库/                       ← 查询用
│   ├─ 00-索引.md                ← 从这里开始
│   ├─ L0-一票否决.md … L6-情绪与心理.md … L9-省钱的别做.md   （8 个整包）
│   ├─ cards/                    ← 66 张单卡，各自自包含
│   └─ index.json                ← 机器索引（给检索脚本）
├─ 导入-Hindsight/               ← 搬到别的机器用
│   ├─ IMPORT-to-hindsight.md    ← 步骤（本机未执行）
│   └─ hindsight_payload.jsonl   ← 74 行 {title, content}
├─ 数据与脚本/                    ← 想改内容就动这里（全部只用标准库）
│   ├─ checklist.json            ← 一页纸的唯一来源
│   ├─ cards.json                ← 知识卡的唯一来源
│   ├─ render.py                 ← 重建一页纸（md / html）
│   ├─ build_kb.py               ← 重建知识库 + payload + index
│   ├─ build_site.py             ← 重建 site/index.html
│   ├─ build_refs.py             ← 重建 02-引用与来源.md
│   ├─ fetch_sources.py          ← 现取上游原文（原文不进仓库）
│   ├─ build_app.py              ← 从 checklist.json 生成 lifeOS 里的清单（含跳知识库的链接）
│   ├─ deploy.py                 ← 一条命令：重建 → 自检 → 提交 → 推送 → 线上校验
│   ├─ search.py                 ← 本地检索，无网络、无外部调用
│   └─ 自检.py                    ← 一条命令校验全包一致性（16 项）
├─ .github/workflows/selfcheck.yml ← 推送即重建并校验（别人 fork 后也能跑）
└─ 原始资料/                      ← 上游原文快照，**不进公开仓库**（版权 + 时效）
                                    └─ 需要时 `python 数据与脚本/fetch_sources.py` 现取 15 份
```

## 三步上手

**1. 想今天就改几条** → 打开 `一页纸清单/个人健康检查清单.pdf`，
跑一遍打勾，从「没做到」里挑 2–3 条。（不想用纸就开同目录的 `.html`。）

**2. 想查某件事到底怎么回事** → **双击 `site/index.html`**，用你平时说话的词搜
（`打呼噜`、`胸口疼`、`睡不着`、`烫伤`）。不用装 Python，不用联网，手机上也能开。

想在命令行里查：

```powershell
python 数据与脚本/search.py 打鼾                    # 检索
python 数据与脚本/search.py 烫伤 起火 -n 5           # 多个词=或
python 数据与脚本/search.py --tag L4 --list         # 全部急救条目
python 数据与脚本/search.py 睡不着 --full            # 打印整张卡
```

**3. 想搬进 Hindsight** → 只读 `导入-Hindsight/IMPORT-to-hindsight.md`，
在**另一台机器**上按步骤执行。

> 要给别人的话：把整个文件夹发过去 + 附一句「打开 `site/index.html`」。要放网上，看 `04-自部署说明.md`。

## 内容长什么样

每条知识都是一张自包含的卡：

| 字段 | 说明 |
|---|---|
| 层级 | L0 一票否决 / L1 每天 / L2 每周 / L3 每年 / L4 出事那一刻 / L5 一次性办完 / L6 情绪与心理 / L9 别做 |
| 怎么做 | 2–3 步可执行动作，不是口号 |
| 不做的后果 | 具体后果，能量化就给数字 |
| 证据 | 研究类型 + 效应量 + 出处（`HTL`/`HSO`/`HLB §n`/`HTC`） |
| 常见误区 | 1–2 条最常被搞反的地方 |
| 不适用 | 谁不该照做、该先问医生 |
| 检索词 | 含口语和症状词（打呼噜、胸口疼、睡不着…） |

证据等级 A/B/C/D 是 HowToLiveLonger 的实用分级，不是 GRADE；`-` 表示常识性安全措施、没做分级。
怎么读、有哪些坑，见 `03-使用说明.md` 第四节。

## 改内容

> 只想跑一次更新？`python 数据与脚本/deploy.py --push` 一条命令全做完，见 `05-持续更新.md`。
> 下面是不用脚本时的手工步骤，两者等价。

`cards.json` 和 `checklist.json` 是**唯一来源**，其余都是派生物，别直接改产物：

```powershell
# 改了 cards.json
python 数据与脚本/build_kb.py       # 知识库/ + 导入载荷 + index.json
python 数据与脚本/build_site.py     # 网页版
python 数据与脚本/build_refs.py     # 引用与来源

# 改了 checklist.json → 重建一页纸的 md / html（pdf 用浏览器打印，见下）
python 数据与脚本/render.py
& "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" --headless=new `
  --no-pdf-header-footer --print-to-pdf="一页纸清单\个人健康检查清单.pdf" `
  ([System.Uri]"$PWD\一页纸清单\个人健康检查清单.html").AbsoluteUri
```

改了内容记得把 `cards.json` 里的 `meta.version` 升一号，页脚会跟着变。

## 改完记得自检

```powershell
python 数据与脚本/自检.py
```

它会校验 **16 项**：结构完整性、卡片字段、related 指向、卡片文件对照、整包齐全、索引链接、
index.json 同步、导入载荷、PDF 页数、清单危害字段、检索脚本、**检索站与源是否同步且无外部请求**、
**每条结论是否都有溯源（且没有「未标注来源」）**、**文档之间是否互相指得到**、**上游原文是否齐**、
**app 里的清单是否就是 checklist.json 生成的那份（58 条深链全部指向真实卡片）**。全部通过才说明包是自洽的。

## 三条边界（别跳过）

1. **没有在这台机器写入 Hindsight。** 本包只生成文件与导入说明，
   一次 `hindsight_ingest_document` 都没调用。要导入请到目标机按文档操作，
   并建议导进**独立 bank**（如 `personal::health`），不要混进代码记忆。
2. **证据是人群关联，不是个人结论。** A/B/C/D 沿用 HowToLiveLonger 的实用分级（不是 GRADE）；
   HR/RR/OR 不能相乘，也不能换算成「少活几年」。
   危害一栏里有一部分是通用医学常识（急救时间窗、中毒机制），出处栏标的是「行动」本身的来源。
3. **不能替代医生。** L4 是现场处置，不是诊断；急症按卡上写的打 120 / 去急诊。

## 许可证与署名

- 代码（`数据与脚本/*.py`、`site/index.html`）：**MIT**
- 文本（卡片、清单、文档）：**CC BY 4.0**，需署名
- 上游：HowToLiveLonger（Unlicense）、HowToCook（Unlicense）、HowToLiveBetter（**CC BY 4.0，必须署名**）、
  HumanSystemOptimization（**无许可证**，仅作事实引用与改写，可按要求删除相关卡）

细节与逐条溯源见 `02-引用与来源.md` 与 `LICENSE-内容-CC-BY-4.0.md`。

## 没纳入的东西

- `remote-working`（远程工作资料合集）：属于工作方式与机会信息，不是健康证据。
- `HowToLiveBetter` 的「钱」「账号与防骗」两个模块：与健康无关，另行处理。
- **家庭药箱、急救实操演练、睡眠进阶、人群分层、体检报告解读、环境职业暴露**：
  正文与优先级记在本地的工作笔记里（不随公开版发布），其中急救与药箱两节的正文已经取到本地，随时能补卡。
- 心理健康原来是最大缺口，v1.2 已补 `L6 情绪与心理` 8 张（自杀手段限制、说出口、直接询问、丧亲、重病诊断、哀伤卡住、创伤后）。
