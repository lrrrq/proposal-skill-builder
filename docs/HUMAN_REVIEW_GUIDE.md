# Human Review Guide - 人工审查指南

> **状态**: 占位文档 - 待 Phase 4 实现

## 概述

本文档定义人工审查流程，确保 Skill 质量达到发布标准。

**核心原则**：AI 分析 + 人工确认 = 高质量 Skill

## 审查时机

### 1. Fragment 审查（Phase 2-3）
在 AI 分析生成 `.pending.json` 后，人工确认：
- 页面类型（page_type）
- 策略类型（strategy_type）
- 说服目标（persuasion_goal）
- 情绪触发点（emotional_trigger）

### 2. Pattern 审查（Phase 4）
在 extract-patterns 生成 patterns.json 后，人工确认：
- Pattern 抽象名称是否准确
- Pattern 分类是否正确
- 可复用逻辑是否清晰

### 3. Skill 组装审查（Phase 4）
在 compose-skill 生成 draft Skill 后，人工确认：
- SKILL.md 内容是否准确
- 示例是否符合实际场景
- 限制条件是否完整

### 4. 发布前审查（Phase 5）
在 publish-skill 前，最终确认：
- 所有文件完整
- 质量分数达标
- 无敏感信息泄露

## 审查文件格式

### Fragment Pending 格式

```json
{
  "fragment_id": "frag_001",
  "pending_review": true,
  "ai_analysis": {
    "page_type": "emotional_appeal",
    "strategy_type": "narrative_strategy",
    "persuasion_goal": "建立品牌认同",
    "emotional_trigger": "luxury_aspiration"
  },
  "human_notes": "",
  "confirmed": false
}
```

### Pattern Pending 格式

```json
{
  "pattern_id": "pat_001",
  "pending_review": true,
  "ai_analysis": {
    "pattern_type": "narrative",
    "abstract_name": "Luxury Emotional Compression",
    "description": "..."
  },
  "human_notes": "",
  "confirmed": false
}
```

## 审查流程

### Step 1: 列出待审查项

```bash
python -m skill_builder.cli list-pending <case_id>
```

输出：
```
case_0004 待审查项：
- fragments: 3 个待确认
- patterns: 2 个待确认
- strategies: 1 个待确认
```

### Step 2: 逐项审查

```bash
python -m skill_builder.cli review-fragment <fragment_id>
```

交互式界面显示 AI 分析结果，人工确认或修改。

### Step 3: 标记确认

```bash
python -m skill_builder.cli confirm-fragment <fragment_id> --notes "确认无误"
```

### Step 4: 生成审查报告

```bash
python -m skill_builder.cli review-summary <case_id>
```

## 审查标准

### Fragment 审查标准
- [ ] page_type 准确反映页面功能
- [ ] strategy_type 符合实际策略
- [ ] persuasion_goal 明确且可执行
- [ ] emotional_trigger 描述准确
- [ ] 无事实错误

### Pattern 审查标准
- [ ] abstract_name 具有抽象意义，不是具体描述
- [ ] description 清晰说明复用逻辑
- [ ] pattern_type 分类正确
- [ ] strategic_function 明确
- [ ] 可实际复用于新案例

### Skill 组装审查标准
- [ ] SKILL.md 章节完整
- [ ] 处理流程可执行
- [ ] 输出格式明确
- [ ] 示例真实可信
- [ ] 限制条件合理

## 审查输出

审查完成后生成 `review_summary.md`：

```markdown
# Human Review Summary: case_0004

## 审查时间
2026-05-13

## 审查结果

| 类型 | 总数 | 已确认 | 待确认 |
|------|------|--------|--------|
| Fragments | 33 | 30 | 3 |
| Patterns | 5 | 5 | 0 |
| Strategies | 6 | 6 | 0 |

## 待确认项

### Fragments
- frag_015: page_type 不确定
- frag_022: emotional_trigger 需要补充
- frag_031: strategy_type 需要修正

## 审查意见

[人工填写审查意见]

## 下一步

- [ ] 完成 frag_015 确认
- [ ] 完成 frag_022 补充
- [ ] 完成 frag_031 修正
```

## Phase 4 任务

1. [ ] 实现 list-pending 命令
2. [ ] 实现 review-fragment 命令（交互式界面）
3. [ ] 实现 confirm-fragment 命令
4. [ ] 实现 review-summary 命令
5. [ ] 生成 review_summary.md 模板

## 参见

- `docs/QUALITY_RUBRIC.md` - 质量标准
- `docs/PUBLISH_CONTRACT.md` - 发布契约
- `docs/OPENCLAW_INTEGRATION.md` - OpenClaw 集成