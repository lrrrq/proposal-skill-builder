# Pattern Schema

> 状态: 策略 Pattern 协议
> 更新时间: 2026-06-02

## 1. 目标

Pattern 不能只是旧方案摘要。合格 Pattern 必须能被 Router 选择、被 Assembler 组合、被 Checker 校验。

一个 Pattern 应回答:

- 什么时候用。
- 为什么这样做。
- 如何迁移。
- 不能怎么用。
- 来源证据是什么。
- 置信度如何。

## 2. Pattern 类型

`brand_translation`: 品牌转译方法。

`content_strategy`: 内容策略方法。

`narrative_structure`: 叙事结构方法。

`visual_layout`: 视觉和版式方法。

`language_style`: 语言风格方法。

`execution_method`: 执行落地方法。

## 3. 必填字段

```yaml
pattern_id:
pattern_name:
pattern_type:
trigger_condition:
project_type:
brand_fit:
audience_fit:
goal_fit:
core_logic:
proposal_flow:
visual_direction:
language_direction:
avoid:
applicable_when:
not_applicable_when:
source_case:
source_pages:
evidence_fragments:
confidence:
```

## 4. 字段说明

`trigger_condition`: 命中该 Pattern 的 brief 特征。

`brand_fit`: 适合的品牌气质或行业，不是品牌名堆砌。

`audience_fit`: 适合的目标人群。

`goal_fit`: 适合的商业目标。

`core_logic`: 这个 Pattern 的策划判断核心。

`proposal_flow`: 迁移到新方案时的内容展开顺序。

`visual_direction`: 视觉、版式、参考图和页面调性的迁移方向。

`language_direction`: 标题、正文、脚本、乙方提案语言的表达方向。

`avoid`: 使用该 Pattern 时必须避免的误用。

`applicable_when`: 正向适用条件。

`not_applicable_when`: 禁用条件，优先级高于正向条件。

`source_case`: 来源案例 id 或文件名。

`evidence_fragments`: 支撑该 Pattern 的证据片段 id。

`confidence`: `low`、`medium`、`high`。

## 5. 示例

```yaml
pattern_id: festival-light-vacation-translation
pattern_name: 节日轻度假转译
pattern_type: content_strategy
trigger_condition:
  - 酒店品牌
  - 节日营销
  - 年轻家庭
  - 礼盒推广
project_type:
  - TVC
  - 短视频
brand_fit:
  - 生活方式酒店
  - 都市度假酒店
audience_fit:
  - 城市年轻家庭
goal_fit:
  - 节日礼盒推广
  - 小红书种草
core_logic:
  - 降低传统节日符号的仪式感
  - 用酒店空间承载短暂逃离感
  - 让礼盒作为关系和场景的一部分自然出现
proposal_flow:
  - 先定义节日情绪
  - 再定义品牌空间角色
  - 再将产品放入人物关系
visual_direction:
  - 夏日自然光
  - 酒店空间细节
  - 轻松家庭状态
language_direction:
  - 克制
  - 松弛
  - 避免硬广口吻
avoid:
  - 龙舟主体化
  - 传统红金堆砌
  - 电商广告式硬广
applicable_when:
  - brief 要求节日传播但品牌不适合传统符号
not_applicable_when:
  - brief 明确要求传统民俗主视觉
source_case: W酒店中秋创意概要M Films0705V1(2).pdf
source_pages:
  - 3
  - 4
  - 5
evidence_fragments: []
confidence: high
```

## 6. 质量标准

高质量 Pattern:

- 有明确触发条件。
- 有明确禁用条件。
- 能迁移到新 brief。
- 不依赖旧案例专有名词才能成立。
- 能指出误用风险。
- 有来源证据。

低质量 Pattern:

- 只是复述旧方案内容。
- 只有形容词，没有判断逻辑。
- 没有适用和不适用边界。
- 不能被 Router 自动筛选。
- 无法被 Checker 验证。

