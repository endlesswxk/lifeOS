# 把这份知识库放进 Hindsight（在别的机器上执行）

> **本次没有在这台电脑写入 Hindsight。** 这里只生成了文件和导入说明，
> 一次 `hindsight_ingest_document` 都没调用过。下面所有步骤都需要你在**另一台机器**上运行。

---

## 0. 先决定三件事

| 决定 | 选项 | 建议 |
|---|---|---|
| 导到哪里 | 独立 bank / 现有 bank | **独立 bank**，例如 `personal::health`。健康是个人的长期事实，混进 `coding-agent::<repo>` 会和代码记忆互相污染 |
| 导多细 | 8 个大包 / 66 张卡 / 两者都要 | **先导 8 个大包**（一次 8 条，快），检索命中粗粒度问题时够用；不够再补 66 张卡做细粒度 |
| 谁执行 | 目标机上的 agent 逐条调用 | 让 agent 读 `hindsight_payload.jsonl` 逐行调用，比手抄可靠 |

独立 bank 的配置方式（目标机 `~/.hindsight/coding-agent.json`）：

```jsonc
{
  "mapPathToBank": {
    "E:/SLACK-AI": "personal::health"   // 换成目标机上的实际目录
  }
}
```

改完要**重启 agent**（持久插件只在工作区加载时读配置）。

## 1. 把整个 `个人健康知识库成果` 文件夹拷到目标机

需要的最小集合：

```
个人健康知识库成果/
  导入-Hindsight/hindsight_payload.jsonl   ← 导入用的 74 行 JSONL（8 个大包 + 66 张卡）
  知识库/                                  ← 人读的 Markdown（可选，但建议一起带）
  数据与脚本/cards.json                     ← 结构化数据（可选，以后要重建/改写时用）
```

## 2. 校验文件，别急着导

```powershell
# 每行必须是合法 JSON，且有 title / content
python -c "import json;[json.loads(l) for l in open('导入-Hindsight/hindsight_payload.jsonl',encoding='utf-8')];print('ok')"
```

## 3. 让目标机的 agent 执行导入

把下面这段原样发给目标机上的会话（Claude Code / Codex / DSH 都行，只要有 `hindsight_ingest_document`）：

```text
读 导入-Hindsight/hindsight_payload.jsonl，逐行解析，对每一行调用
hindsight_ingest_document(title=该行的 title, content=该行的 content)。

要求：
- 一次一条，不要合并、不要改写 content，原样传入。
- 只导前 8 行（8 个大包）时，导完就停，报告成功条数。
- 全部导完之后，用 hindsight_search_knowledge_pages 查询
  「打鼾 睡眠呼吸暂停」，确认能召回「个人健康知识库 · 每年或按年龄」；
  再用「烫伤」查询，确认能召回「个人健康知识库 · 出事那一刻」。
- 把两次校验的结果贴出来。任何一条失败就停下来报告，不要跳过。
```

> 为什么分两批：8 个大包是「按层」的整合文档（每包 5–17 条），适合回答
> 「我该注意什么」；58 张卡是单点文档，适合回答「打鼾要不要查」这种具体问题。
> 先导大包能让检索马上可用，细粒度可以之后慢慢补。

## 4. 导入后怎么用

- 提问式检索：`hindsight_search_knowledge_pages("血压 多久量一次")`
- 深问因果：`hindsight_reflect("我睡眠不好，清单里哪几条和我有关")`
- 注意：Hindsight 的 `reflect` 会把文档拆成 facts，**卡里写的「证据等级 / 出处 / HR」是文本，
  会作为事实被记住，不会被算成新的结论**——所以卡里每一处数字都保留了原始出处。

## 5. 想改内容怎么办

内容唯一来源是 `cards.json`：

```powershell
# 改完重新生成所有 Markdown、索引和 payload
python 数据与脚本/build_kb.py
```

再回到第 3 步重导（同名文档会以新版本覆盖旧记忆；如果改了结论，建议把 title 带上版本号，
例如「个人健康知识库 v1.1 · 每天」，避免和旧事实打架）。

---

## 导入前的三条提醒

1. **这是个人健康数据。** 独立 bank + 只在你自己的账号下，别导进公司共享 bank。
2. **别把它当诊断。** 内容来自公开知识库的整理，证据是人群关联；急性症状按 `L4` 的处置走，
   需要诊断时找医生。
3. **导入不等于生效。** Hindsight 的检索要等 ingestion + consolidation 跑完，
   导完立刻查可能查不到，等几分钟再试一次。
