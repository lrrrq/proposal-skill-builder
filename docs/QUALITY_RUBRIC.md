# Quality Rubric - Skill 质量标准

> **状态**: 占位文档 - 待完善

## 概述

本文档定义 Skill 质量评估标准。

**核心原则**：Skill 是能力抽象层，不是案例罗列。

## 质量分数计算

评分维度（满分 100）：

| 维度 | 满分 | 说明 |
|------|------|------|
| structure | 15 | 文件存在 + 字段完整 |
| traceability | 15 | 案例来源 + Patterns + Fragments |
| abstract | 20 | 可复用策略抽象程度 |
| process | 15 | 处理流程可执行性 |
| output | 10 | 输出格式明确度 |
| visual | 10 | 视觉策略可信度 |
| examples | 10 | 示例质量 |
| limits | 5 | 限制条件清晰度 |

## 质量等级

### Gold
- patterns ≥ 5
- 视觉片段 ≥ 20
- 策略单元 ≥ 3
- 总分 ≥ 90

### Silver
- patterns ≥ 5
- 视觉片段 ≥ 1
- 或总分 ≥ 75

### Bronze
- patterns ≥ 3
- 或总分 ≥ 60

### Failed
- source_cases 为空
- source_patterns < 3
- 总分 < 60

## 硬规则

1. **视觉片段 < 3 时，最高只能 Silver**
2. **source_cases 为空，直接 Failed**
3. **source_patterns 少于 3，直接 Failed**
4. **examples.md 为空，最高只能是 Bronze**
5. **SKILL.md 缺少限制条件，最高只能是 Bronze**

## Compression 质量标志

| 标志 | 说明 | 影响 |
|------|------|------|
| normal | 正常质量 | 无 |
| too_short | 文本过短（<20字符） | 降低 abstract 分数 |
| duplicate | 重复内容 | 降低 traceability 分数 |
| low_information | 低信息密度 | 降低 abstract 分数 |
| merged | 多个 fragment 合并 | 提升抽象层级 |
| vision_only | 纯视觉来源 | 标记来源 |
| text_only | 纯文本来源 | 标记来源 |

## 低质量阈值

| 指标 | 阈值 | 处理建议 |
|------|------|----------|
| 低质量 fragments 占比 | > 50% | 检查提取质量 |
| too_short 占比 | > 30% | 合并或补充内容 |
| duplicate 占比 | > 30% | 去重处理 |

## Skill 组装质量检查

### 1. 结构检查
- skill.json 存在且字段完整
- SKILL.md 存在
- examples.md 存在

### 2. 状态检查
- status = "draft"
- callable = false
- dataset in ("test", "prod")

### 3. 章节检查
SKILL.md 必须包含：
- 适用场景
- 输入要求
- 核心判断逻辑
- 处理流程
- 输出格式
- 可复用策略
- 视觉策略
- 内容结构策略
- 受众洞察
- 执行方法
- 限制条件
- 来源案例

## 提升质量的方法

1. **增加视觉片段**：ai_fragments 数量不足会影响视觉策略可信度
2. **丰富 Patterns**：至少 5 个有意义的 Patterns
3. **完善示例**：至少 2 个完整 Brief + 输出方向 示例
4. **明确限制条件**：说明 Skill 的适用边界
5. **执行 Fragment Compression**：减少低质量 fragments

## Phase 任务

### Phase 3.5
- [ ] 完善 compression 质量标志
- [ ] 验证低质量阈值

### Phase 4
- [ ] 强化 Pattern 抽象质量
- [ ] 完善 human review 流程
- [ ] 建立 Skill 组装质量检查清单

## 参见

- `docs/HUMAN_REVIEW_GUIDE.md` - 人工审查指南
- `docs/PUBLISH_CONTRACT.md` - 发布契约