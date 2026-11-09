# 生活系统 LifeOS

一个跑在浏览器里的个人生活系统：**每天打勾、按周回顾、出事有急救卡**。
它背后有一套完整的健康知识库 —— 清单上每一条都能点开看清「依据是什么、不做会怎样、原文在哪」。

| 入口 | 是什么 |
|---|---|
| **https://endlesswxk.github.io/lifeOS/** | 生活系统 app：今天 / 任务 / 清单 / 统计 |
| **https://endlesswxk.github.io/lifeOS/kb/site/** | 个人健康知识库：66 张卡，可搜、可离线 |

装到手机上：用手机浏览器打开上面第一个地址 → 菜单「添加到主屏幕」→ 之后像原生 app 一样打开，**断网也能用**。

---

## 这里有什么

```
lifeOS/
├─ index.html              生活系统 app（单文件，含全部逻辑与样式）
├─ manifest.webmanifest    PWA 清单（图标、主题色、独立窗口）
├─ sw.js                   Service Worker：离线缓存（app 和知识库都缓存）
├─ icons/                  主屏图标
├─ .nojekyll               GitHub Pages 别用 Jekyll 处理
└─ kb/                     个人健康知识库
   ├─ site/                检索站（单文件，双击就能开）
   ├─ 知识库/               66 张卡，每张一个 markdown
   ├─ 数据与脚本/           卡片源数据 + 生成/自检/发布脚本
   ├─ 一页纸清单/           A4 一页，实测能打印
   ├─ 导入-Hindsight/       74 条记忆载荷（给 AI 记忆库用）
   ├─ 02-引用与来源.md      逐卡溯源到原文条目与论文 DOI
   ├─ 03-使用说明.md        怎么用、证据等级怎么读
   ├─ 04-自部署说明.md      自己搭一份
   └─ 05-持续更新.md        改一次成本 = 一条命令
```

## app 和知识库怎么连起来

**清单**（app 里 58 条）是操作界面，**知识库**（66 张卡）是查阅界面，两边靠卡片 id 相连：

- 首屏右上角「知识库」→ 知识库检索站（旁边是「设置」：备份、深色模式）
- 清单每条右侧「依据 ↗」→ 直接跳到对应的那张卡（自动展开、高亮）
- 知识库页面左上「← 生活系统」→ 回到 app

app 里的清单**由 `kb/数据与脚本/checklist.json` 生成**（`build_app.py`），所以两边永远一致：
改完清单跑一条命令，app、知识库、离线缓存一起更新。

## 数据在哪

全部在**你自己的浏览器**里（`localStorage`，键名 `lifeos.v1`）。没有账号、没有服务器、不上传任何东西。
换浏览器 = 换一份数据，导出/导入见 app 的「统计」页。

## 本地跑

```bash
git clone https://github.com/endlesswxk/lifeOS.git
cd lifeOS
python -m http.server 8080
# 打开 http://localhost:8080
```

（直接双击 `index.html` 也能用，只是 Service Worker 和安装到主屏需要 http(s)。）

## 内容怎么维护

```bash
cd kb
python 数据与脚本/自检.py                 # 16 项一致性校验
python 数据与脚本/deploy.py --sync-lifeos --push   # 重建 → 自检 → 同步 → 推送
```

## 说明

- 这是**个人整理**，不是医疗建议；有症状请就医。
- 证据等级用 `A/B/C/D/-` 标注（`A` 随机对照或大样本，`-` 属常识不适用分级），每条都写了出处。
- 许可证：代码 [MIT](kb/LICENSE)；文本内容 [CC BY 4.0](kb/LICENSE-内容-CC-BY-4.0.md)，上游署名要求见该文件。
- 知识库内容整理自这四个仓库的原文：
  [HowToLiveLonger](https://github.com/geekan/HowToLiveLonger)（Unlicense）、
  [HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)（CC BY 4.0，已署名）、
  [HowToCook](https://github.com/Anduin2017/HowToCook)（Unlicense）、
  [HumanSystemOptimization](https://github.com/zijie0/HumanSystemOptimization)（无许可证，仅作事实引用与改写），
  以及 NHS / CDC / WHO 等公开指南。各卡片的出处与 DOI 见 [kb/02-引用与来源.md](kb/02-引用与来源.md)。
- 上游 `原始资料/`（书籍正文与台账）**不随本仓库分发**（版权与时效），需要时用
  `kb/数据与脚本/fetch_sources.py` 现取。
