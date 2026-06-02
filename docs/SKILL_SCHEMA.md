# Skill Schema

> 状态: Skill Metadata 协议
> 更新时间: 2026-06-02

## 1. 目标

Skill 必须从“可读文档”升级为“可调度资产”。Router 不能靠猜测使用 Skill，必须依赖 metadata 判断适用、排除、兼容和优先级。

## 2. Skill 类型

`brand_persona`: 定义品牌人格、语气、价值判断、表达边界和禁忌。

`strategy_method`: 定义可迁移策略方法，通常由多个 pattern 支撑。

`output_structure`: 定义提案结构、PPT 页序、章节密度、视觉参考位和版式规则。

`language_style`: 定义公司语言质感、标题方式、乙方提案表达和脚本文体。

`execution_output`: 组装前三类结果，形成 OpenClaw 可执行的成品上下文。

## 3. Metadata 必填字段

```yaml
skill_id:
display_name:
skill_type:
brand:
project_type:
tone:
goal_type:
applicable_when:
not_applicable_when:
compatible_with:
conflict_with:
priority:
required_context:
output_role:
source_cases:
source_patterns:
quality_level:
callable:
status:
version:
```

## 4. 字段说明

`skill_id`: 稳定唯一标识，不随显示名变化。

`skill_type`: 必须从五类 Skill 类型中选择。

`brand`: 可为具体品牌、行业品牌族或 `generic`。

`project_type`: 触发该 Skill 的项目类型。

`tone`: 品牌或提案调性，例如 `稳中有网感`、`高端留白`、`年轻生活方式`。

`goal_type`: 商业目标，例如预约直播、节日转化、品牌升级、招商、内部传播。

`applicable_when`: 适用条件，必须能被 Router 读取。

`not_applicable_when`: 禁用条件，优先级高于适用条件。

`compatible_with`: 推荐搭配的 Skill 类型或 skill_id。

`conflict_with`: 明确冲突的 Skill 类型、行业、调性或 skill_id。

`priority`: 路由优先级，建议 1 到 5，5 最高。

`required_context`: 使用该 Skill 前必须具备的信息。

`output_role`: Skill 在最终上下文中的职责，例如 `brand_constraints`、`strategy_patterns`、`page_structure`、`writer_prompt_pack`。

## 5. 四层职责边界

品牌人格 Skill 不输出完整方案，不设计 PPT 页序，不重写策略。它只定义品牌像谁、怎么说、不能怎么说。

策略方法 Skill 不做排版，不写最终脚本长文。它只输出可迁移判断逻辑、触发条件、适用边界和禁忌。

输出结构 Skill 不重新判断品牌和策略。它只定义页序、章节、信息密度、图文关系和交付形态。

语言风格 Skill 不定义品牌人格，不设计策略方法，不规定页序。它只定义公司在标题、正文、脚本和乙方提案中的语言质感，包括句长、语气、禁止用词和表达密度。

执行输出 Skill 不允许成为超级 Skill。它只组装前四层结果，形成 Writer 可用上下文。

## 6. 最小示例

```yaml
skill_id: leader-live-talk-preheat
display_name: 领导人访谈直播预热矩阵
skill_type: strategy_method
brand: generic
project_type:
  - 访谈直播
  - 领导人短视频
tone:
  - 稳中有网感
goal_type:
  - 直播预约
  - 评论区互动
applicable_when:
  - brief 包含领导人或高管访谈
  - brief 目标包含直播预热或预约
not_applicable_when:
  - 纯产品硬广
  - 不允许领导人出镜
compatible_with:
  - brand_persona
  - output_structure
conflict_with:
  - 纯综艺恶搞调性
priority: 4
required_context:
  - brand
  - leader_name
  - live_topic
output_role: strategy_patterns
quality_level: draft
callable: true
status: draft
version: "1.0"
```

