# Runtime Validation Protocol

> 状态: Runtime 校验协议
> 更新时间: 2026-06-02

## 1. 目标

Runtime Checker 用来判断 Writer 输出是否符合 brief、品牌人格、策略方法、输出结构和公司提案风格。Checker 不替代人工审美判断，但必须能稳定指出跑偏位置。

## 2. Checker 输入

```yaml
brief:
route_result:
assembled_context:
writer_output:
source_skill_metadata:
source_patterns:
```

## 3. Checker 输出

```yaml
brief_fit_score:
brand_persona_score:
strategy_match_score:
structure_score:
language_style_score:
forbidden_violation:
ppt_readiness_score:
overall_verdict:
revision_instructions:
```

## 4. 评分维度

`brief_fit_score`: 是否回应用户 brief 的品牌、项目类型、商业目标、输出形态和限制条件。

`brand_persona_score`: 是否符合品牌人格、调性和表达边界。

`strategy_match_score`: 是否使用了 Router 选中的策略 pattern，是否出现策略错配。

`structure_score`: 是否符合输出结构 Skill 的页序、章节节奏和信息密度。

`language_style_score`: 是否符合公司提案语言、标题方式、脚本颗粒度和乙方表达质感。

`forbidden_violation`: 是否违反禁忌边界。该项为硬规则，不应被总分抵消。

`ppt_readiness_score`: 是否自然可转为 PPT，包括页标题、页内信息量、参考图位、视觉方向和收尾。

## 5. Verdict 规则

`pass`: 可进入人工微调或交付。

`revise`: 有明确可修复问题，需 Writer 按 revision instructions 重写局部。

`block`: 命中禁忌、品牌严重错配、策略严重错配或结构不可转 PPT。

## 6. Gold Sample 校准

先选 10 个公司旧案例作为 gold sample。每个样本人工标注:

- 品牌调性。
- 项目类型。
- 商业目标。
- 目标人群。
- 策略逻辑。
- 语言风格。
- 输出结构。
- 禁忌边界。
- 可复用 pattern。
- 不可迁移内容。

校准流程:

1. 人工完成 gold sample 标注。
2. Checker 对同一批样本评分。
3. 对比人工判断和自动评分。
4. 记录分歧最大的维度。
5. 优先修正分歧最大的评估项。
6. 重新跑同一批样本，直到关键维度稳定。

## 7. 最小通过标准

进入 Writer 输出后的成品必须满足:

- `brief_fit_score` 不低于 80。
- `brand_persona_score` 不低于 75。
- `strategy_match_score` 不低于 75。
- `structure_score` 不低于 80。
- `forbidden_violation` 必须为空。
- `overall_verdict` 不能为 `block`。

如果用于客户提案，还必须满足:

- `language_style_score` 不低于 80。
- `ppt_readiness_score` 不低于 80。

## 8. 修订指令格式

Checker 不输出泛泛建议，必须输出可执行修订指令。

示例:

```yaml
overall_verdict: revise
revision_instructions:
  - 将第 3 页从泛泛品牌介绍改为用户场景切入，匹配品牌人格 Skill 的生活方式调性。
  - 删除第 5 页关于竞品领先的未经证实判断，命中 forbidden boundary。
  - 将短视频脚本从完整对白压缩为可拍摄概要，匹配 10 页 PPT 信息密度。
```

