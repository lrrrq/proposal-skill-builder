---
name: proposal-reference-transfer
description: Use this skill whenever the user wants to create a new Chinese proposal, campaign plan, event plan, brand activation plan, or PPT deck by referencing an existing proposal, case, campaign, planning document, or deck. This skill guides the agent to load the relevant brand-style-pack, extract transferable strategy from source materials, adapt to a new brief and brand context, produce complete Chinese proposal content following a 4-section structure, create slide-ready structure with mandatory header/footer DNA, plan visual assets through brand packs (not blind search), and verify against hard rules including brand-style consistency, page DNA, and red lines.
---

# 参考策划迁移生成

## 使用目标

当用户希望参考已有策划、案例、方案、PPT 或活动文档来生成新策划时，使用本 skill。

目标不是复刻参考策划，而是先加载公司品牌资产，再从参考资料中提炼可迁移方法，最后基于新 brief 输出完整中文策划正文、PPT 页面结构、视觉资产规划和质量校验。

## 核心原则

1. **先加载品牌资产，再生成**——必须先加载 `brand-style-pack/<company>/`，所有视觉与词汇决策在 pack 范围内做。
2. **优先读取原始参考资料**——不要把旧摘要、旧 case、旧生成结果当成权威来源。
3. **迁移方法，不迁移表皮**——策略逻辑、叙事结构、创意方法可以迁移；品牌词、客户名称、不可复用场景不能照搬。
4. **品牌适配有克制度**——客户品牌强（蔡司 / TEENIE WEENIE 类）→ M Films 让位；客户品牌弱 → M Films 主张。详见「客户品牌强度评估」步骤。
5. **正文必须完整**——不能只输出标题、页面结构、图片 prompt。
6. **PPT 链路同时保留 `content` 和 `slides`**——`content` 承载正文和页面文案，`slides` 承载页面结构和视觉规划。
7. **图片来源优先从 pack 取**——参考图 / 品牌素材从 `brand-style-pack/reference_images/` 取，不凭空搜图。
8. **缺资源就问，不凭空造**——参见「询问机制」。

## 工作流

### 0. 加载品牌资产（前置）

按 brief 关键词加载：

- 默认加载 `brand-style-pack/m-films/`（M+FILMS 恩柏斯影视）。
- brief 含明确客户名 / 行业 → 叠加加载 `brand-style-pack/<client>/` 和 `industry-pack/<industry>/`。
- 加载失败 → 询问机制。

### 1. 读取参考策划

优先从原始文件或用户提供的原始内容中提炼。若只能拿到摘要或二手材料，要在输出中标明证据等级较低。

详细模板见 `references/reference_extraction.md`。

### 2. 提炼可迁移方法

提炼要点：

- 原策划目标和受众
- 核心策略逻辑
- 创意概念和叙事结构
- 内容模块和执行节奏
- 视觉语言和体验方法
- 可迁移方法 / 不可迁移内容（二分法）

### 3. 解析新 brief

明确新项目的客户、品牌、目标、受众、场景、约束和成功标准。信息不足时按 brief 关键词建立简短假设。

### 4. 客户品牌强度评估

判断 M Films 视觉的克制度，输出 `client_brand_strength`：

| 强度 | 典型客户 | M Films 视觉策略 |
|------|----------|------------------|
| `extreme_high` | 蔡司 / TEENIE WEENIE / 国际奢侈 | 极度克制：用 "M Production" 缩写、不显式 Logo |
| `high` | 高端酒店 / 高端服饰 / Snowpeak | 主张强：全 DNA 注入 + 绿色装饰线主导 |
| `medium` | 中国科技（OPPO / 美的）| 中度：抽象 M 元素 + 绿色装饰线 |
| `low` | 地产 / 企业 / 中端客户 | 全开：完整 DNA + 业务范畴 |

### 5. 生成完整中文策划正文

按 **M Films 4 段式**（创意背景 / 创意概要 / 创意脚本 / 参考片+调性）输出 `content`。

详细模板见 `references/proposal_content.md`。

### 6. 生成 PPT 页面结构

输出 `slides`，按 M Films 4 段式页序。**每页必含硬 DNA**：

- 右上角：页码 + 垂直绿短线 + M+FILMS + 业务范畴三件套
- 右下角：M+FILMS Logo + Copyright
- 客户 Logo 右上角，M+FILMS 右下角（对角关系）
- 章节切换页用品牌绿水平色块

详细模板见 `references/ppt_outline.md`。

### 7. 规划 PPT 视觉资产

图片来源优先级（**从 pack 取，不凭空搜**）：

1. `brand_asset`：`brand-style-pack/<company>/assets/` 已有素材
2. `reference_image`：`brand-style-pack/<company>/reference_images/` 风格参考
3. `ai_generated`：AI 生成概念图，prompt 含 pack 中的 visual_motifs
4. `no_image`：策略页 / 流程页 / 表格页

详细模板见 `references/visual_assets.md`。

### 8. 执行质量校验

输出 `quality_check`，按 4 维度校验：

- 通用校验（参考提炼 / 品牌适配 / 策划正文 / PPT 结构 / 视觉资产 / 工具链）
- 品牌风格一致性（在 brand-style-pack 范围内）
- 硬 DNA（页眉页脚 + 业务范畴 + 对角 Logo）
- 红线（不可触犯的禁忌）

详细清单见 `references/quality_checklist.md`。

### 9. 工具适配（条件分支）

只在当前 agent 有工具时触发：

- 有 PPT 工具 → 同时传 `content` 和 `slides`
- 有图片搜索工具 → 从 pack 取，不用公网搜
- 有图片生成工具 → ai_prompt 含 pack 中的 visual_motifs + colors
- 有 OpenClaw 风格链路 → 优先走 OpenClaw

无工具时：交付完整正文 + 页面结构 + 视觉规划即可。详细见 `references/tool_adapters.md`。

## 默认输出结构

```markdown
# 提炼与适配摘要
# 新策划正文（4 段式）
# PPT 页面结构（含 M Films 页眉/页脚硬 DNA）
# PPT 视觉资产规划（含 source 标注）
# 最终校验（4 维度）
# 资源使用清单（用了哪些 pack 文件）
```

## 询问机制

**缺资源时主动停下问用户，不靠 AI 凭空造**。

| 触发时机 | 询问内容 |
|----------|----------|
| 找不到对应 brand-style-pack | "要做哪个公司？M Films / 某客户 / 某新公司？" |
| pack 内 logo 只有 1 版 | "需要反白版吗？贴深色背景用的" |
| 字体未指明文件路径 | "字体文件路径？没有就标记 system-ui 兜底" |
| reference_images 少于 3 张 | "够用吗？要 AI 补还是用户提供？" |
| 客户行业无 industry-pack | "高端酒店？中端？快消？" |
| brief 提到特殊场景 | "节日？年会？招聘？新品发布？" |

**原则**：

- 一次最多问 1-2 个，避免打断流程
- 每个问题给默认选项
- 30 秒不答用默认继续
- 不问能根据 brief 推的

## 输出风格

- 默认中文输出
- 短文本提案风格：逻辑清楚、段落短、概念感强、适合落页
- 不写成长篇报告
- 不暴露内部推理，但给提炼和适配依据
- 不确定项明确标注假设
