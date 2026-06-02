# Proposal Skill Builder Project Handoff

> 状态: 项目交接入口
> 更新时间: 2026-06-02
> 适用对象: OpenClaw、Claude、ChatGPT、Codex、人工协作者

## 1. 项目目标

本项目要把公司历史策划案转化为可复用、可检索、可调用的策划能力资产。旧策划案不是普通参考资料，而是要被提炼为品牌人格、策略 pattern、语言风格、输出结构、禁忌边界和可复用 Skill。

最终运行链路是:

```text
旧策划案
-> 离线编译为 fragments / patterns / strategies / skills
-> registry 管理可调用资产
-> Runtime Router 根据新 brief 选择上下文
-> Context Assembler 组装 OpenClaw 可消费输入
-> OpenClaw 作为 Writer 输出方案
-> Runtime Checker 校验是否符合 brief、品牌和公司风格
```

项目长期目标是形成策划公司的数字创意操作系统。任何执行平台都只是工作节点，项目规则、状态、资产和决策依据必须独立保存在仓库中。

## 2. 当前定位

当前项目不是纯 prompt 工程，也不是通用 RAG。它是离线 Skill 资产编译器 + registry 资产准备器，并正在进入 runtime validation 阶段。

当前重点:

- 冻结旧 pipeline 的盲目扩展。
- 补齐 Skill Metadata 与 Pattern Schema。
- 强化 Runtime Router 的 Skill Selection。
- 新增 Context Assembler 的上下文组装协议。
- 新增 Runtime Checker 与 gold sample 校准规则。
- 将规则文档升级为跨平台交接手册。

## 3. 系统边界

允许做:

- 离线摄入旧策划案。
- 提炼 fragments、patterns、strategies、skills。
- 维护 registry 与只读发布资产。
- 用 Runtime Router 做 brief 画像和 Skill Selection。
- 将选中资产组装为 OpenClaw Writer 输入。
- 用 Checker 校验输出质量。

暂时不做:

- Web 服务或 SaaS。
- 前端界面。
- 复杂多 Agent 编排。
- 在线问答系统。
- 让 OpenClaw 自由承担 Router、Assembler、Checker。
- 大规模 PPT 自动化，除非 runtime 闭环稳定后再扩展。

## 4. 核心术语

`Fragment`: 从源策划案中提取的文本或视觉证据片段。

`Pattern`: 从多个 fragment 中抽象出的可迁移策划方法，必须包含触发条件、适用边界、禁忌和来源证据。

`Strategy`: 更高层的策略单元，聚合多个 pattern，用于表达判断逻辑和策划主线。

`Skill`: 可调用策划能力资产，包含 Skill Metadata、SKILL.md、来源案例、适用边界和输出角色。

`Runtime Router`: 接收 brief 后决定调用哪些 Skill 和 Pattern 的运行时选择器。

`Context Assembler`: 将 Router 结果压缩为 OpenClaw 可消费上下文的组装器。

`Writer`: 负责最终文字生成的执行者，OpenClaw 默认承担这个角色。

`Runtime Checker`: 校验输出是否符合 brief、品牌人格、策略目标、结构要求和禁忌边界。

## 5. 模块职责

`intake / case_manager / compiler`: 负责源文件摄入、案例绑定和基础编译。

`asset_describer / source_knowledge_extractor`: 负责视觉描述和源知识抽取。

`pattern_engine / strategy_engine`: 负责从证据中抽取 patterns 和 strategies。

`composer`: 负责将案例资产组合为 Skill 文档和 skill.json。

`registry`: 负责发布资产登记和 OpenClaw 只读访问边界。

`router_v2`: 当前应收敛为 Runtime Router 的最小验证入口，优先验证 Skill Selection，不应直接扩成完整输出器。

`skill_checker / quality_checker`: 可作为 Runtime Checker 的基础，但需要 gold sample 校准。

## 6. 当前阶段

当前阶段应命名为:

```text
Runtime Validation Preparation
```

本阶段目标不是继续扩案例处理能力，而是让已有资产能被稳定调度、组装和校验。

## 7. 下一步任务

1. 对照 `docs/SKILL_SCHEMA.md` 补齐现有 Skill Metadata。
2. 对照 `docs/PATTERN_SCHEMA.md` 强化 pattern 字段。
3. 将 `router_v2` 收敛为只输出 Skill Selection 结果的验证器。
4. 新增 Context Assembler，输入 Router 结果，输出 OpenClaw prompt 包。
5. 挑选 10 个旧案例建立 gold sample。
6. 用 `docs/VALIDATION_PROTOCOL.md` 校准 Checker。

## 8. 接手检查清单

新执行者开始工作前必须检查:

- `CLAUDE.md`: 工程规则与禁止事项。
- `docs/PROJECT_HANDOFF.md`: 当前项目总目标与交接说明。
- `docs/CURRENT_STATE.md`: 当前阶段、冻结范围、下一步任务。
- `docs/RUNTIME_PROTOCOL.md`: 在线运行链路。
- `docs/SKILL_SCHEMA.md`: Skill Metadata 规则。
- `docs/PATTERN_SCHEMA.md`: Pattern Schema 规则。
- `docs/VALIDATION_PROTOCOL.md`: 输出校验与 gold sample 规则。

如果这些文档与某个对话上下文冲突，以仓库文档为准。

