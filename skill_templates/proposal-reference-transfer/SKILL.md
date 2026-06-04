---
name: proposal-reference-transfer
description: Use this skill whenever the user wants to create a new Chinese proposal, campaign plan, event plan, brand activation plan, or PPT deck by referencing an existing proposal, case, campaign, planning document, or deck. This skill guides the agent to extract transferable strategy from source materials, adapt it to a new brief and brand context, produce complete Chinese proposal content, create slide-ready structure, plan visual assets through brand assets, reference images, or AI-generated images, and verify that the output is not a shallow rewrite, brand mismatch, or prompt-only deck.
---

# 参考策划迁移生成

## 使用目标

当用户希望参考已有策划、案例、方案、PPT 或活动文档来生成新策划时，使用本 skill。

目标不是复刻参考策划，而是先提炼参考资料中的可迁移方法，再基于新 brief 和新品牌语义，输出完整中文策划正文、PPT 页面结构、视觉资产规划和最终质量校验。

## 核心原则

1. 先提炼，再生成。不要一看到参考策划就直接仿写。
2. 优先读取原始参考资料。不要把旧摘要、旧 case、旧生成结果当成权威来源。
3. 迁移方法，不迁移表皮。策略逻辑、叙事结构、创意方法可以迁移；品牌词、客户名称、不可复用场景不能照搬。
4. 品牌适配优先。行业相同不代表品牌语义相同。
5. 正文必须完整。不能只输出标题、页面结构、图片 prompt 或视觉描述。
6. PPT 链路必须同时保留 `content` 和 `slides`。`content` 承载正文和页面文案，`slides` 承载页面结构和视觉规划。
7. 图片服务策划表达，不替代策划内容。参考图用于方向判断，AI 图用于概念呈现，品牌素材用于准确表达。

## 输入识别

先判断用户是否提供或要求以下内容：

- 参考策划资料：PDF、PPT、docx、图片、案例文本、网页、历史方案。
- 新 brief：客户、品牌、目标、受众、场景、预算、时间、交付物。
- 品牌资料：品牌调性、品牌词汇、视觉规范、禁忌、过往素材。
- 输出要求：只要正文、需要 PPT 结构、还是需要 PPT 成品链路。
- 图片需求：是否需要找参考图、生成 AI 图、使用品牌素材或输出 moodboard。

如果关键信息不足，优先提出最少数量的问题。不要为了完整性追问所有细节；能基于合理假设推进时，先声明假设再执行。

## 工作流

### 1. 读取参考策划

优先从原始文件或用户提供的原始内容中提炼。若只能拿到摘要或二手材料，要在输出中标明证据等级较低。

需要详细模板时，读取 `references/reference_extraction.md`。

### 2. 提炼可迁移方法

提炼以下内容：

- 原策划目标和受众
- 核心策略逻辑
- 创意概念和叙事结构
- 内容模块和执行节奏
- 视觉语言和体验方法
- 可迁移方法
- 不可迁移内容

提炼结果要短，但要有判断。不要把原文改写成长摘要。

### 3. 解析新 brief

明确新项目的客户、品牌、目标、受众、场景、约束和成功标准。若用户没有提供完整 brief，用当前信息建立简短假设。

### 4. 做品牌适配判断

比较参考策划和新品牌之间的语义差异：

- 哪些策略方法可以沿用
- 哪些表达会造成错品牌
- 哪些视觉或语言需要重写
- 是否存在行业相同但品牌气质相反的问题

如果发现明显品牌错配，必须先指出，再生成适配后的新方案。

### 5. 生成完整中文策划正文

输出 `content`。正文要完整，但保持短文本提案风格，适合后续转 PPT。

需要正文结构时，读取 `references/proposal_content.md`。

禁止 prompt-only 输出。如果用户要策划或 PPT，最终内容里必须有可直接阅读的中文方案正文。

### 6. 生成 PPT 页面结构

输出 `slides`。每页至少包含：

- 页码
- 页面标题
- 页面目的
- 页面核心文案
- 内容要点
- 视觉建议
- 讲述备注

需要页面模板时，读取 `references/ppt_outline.md`。

### 7. 规划 PPT 视觉资产

为每页判断是否需要图片，以及图片来源：

- `brand_asset`：用户或品牌已有素材
- `reference_image`：参考图、moodboard、案例图
- `ai_generated`：AI 生成概念图、空间图、主视觉草图
- `no_image`：不需要图片

默认只输出参考图搜索词和 AI 生图 prompt，不默认真的找图或生图。只有用户明确要求生成 PPT 成品，或当前 agent 有对应工具且任务需要时，才进入实际找图或生图。

每张图都要标注用途状态：品牌授权素材、参考图、AI 概念图、待用户确认素材。不要把参考图当成可直接商用素材，除非用户明确提供授权。

需要图片流程模板时，读取 `references/visual_assets.md`。

### 8. 执行质量校验

输出 `quality_check`。至少检查：

- 是否基于原始参考资料提炼
- 是否明确可迁移和不可迁移内容
- 是否完成新品牌适配
- 是否有完整 `content`
- 是否有 slide-ready 的 `slides`
- 是否规划图片来源
- 是否避免只输出 image prompt
- 是否避免旧品牌、旧客户、旧 case 污染
- 如需 PPT 成品，是否同时传递 `content` 和 `slides`

需要完整清单时，读取 `references/quality_checklist.md`。

### 9. 可选工具适配

本 skill 是通用 agent skill，不绑定任何单一运行环境。

如果当前环境有 PPT 工具、图片搜索工具、图片生成工具或 OpenClaw 风格链路，按 `references/tool_adapters.md` 执行适配。没有这些工具时，输出完整正文、PPT 页面结构和视觉资产规划即可。

## 默认输出结构

默认使用以下结构，除非用户指定其他格式：

```markdown
# 提炼与适配摘要

# 新策划正文

# PPT 页面结构

# PPT 视觉资产规划

# 最终校验
```

## 输出风格

- 默认中文输出。
- 使用短文本提案风格：逻辑清楚、段落短、概念感强、适合落页。
- 不写成长篇报告，除非用户明确要求。
- 不把内部推理过程完整暴露给用户，但要给出必要的提炼和适配依据。
- 对不确定的品牌、素材、版权或 brief 条件，明确标注假设。
