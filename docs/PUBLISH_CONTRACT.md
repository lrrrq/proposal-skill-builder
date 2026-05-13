# Publish Contract - Skill 发布契约

> **状态**: 占位文档 - 待 Phase 5 实现

## 概述

本文档定义 Skill 从 draft 到 published 的发布契约。

**核心原则**：
- Draft Skill 存储在 `skills/draft/<skill_id>/`
- 正式 Skill 存储在 `skills/published/<skill_id>/`
- `skill_registry.json` 只登记 `skills/published/` 中的 Skills

## 发布流程

```
compose-skill → skills/draft/<skill_id>/
                         │
                         ▼
                    check-skill
                         │
                         ▼
                   (人工确认)
                         │
                         ▼
               publish-skill → skills/published/
                                        │
                                        ▼
                              skill_registry.json 更新
```

## Draft Skill 要求

Draft Skill 必须满足以下条件才能发布：

### 1. 文件完整性
```
skills/draft/<skill_id>/
├── SKILL.md          # 必须存在
├── skill.json        # 必须存在
└── examples.md        # 必须存在
```

### 2. 质量门槛

| 检查项 | 要求 |
|--------|------|
| score | ≥ 60/100 |
| quality_level | ≠ failed |
| patterns | ≥ 3 |
| source_cases | ≥ 1 |

### 3. 数据契约

`special_skills.json` 字段要求：
- `skill_id`: 字符串，字母数字和连字符
- `display_name`: 字符串
- `description`: 字符串，非空
- `status`: 必须是 "draft"
- `dataset`: "test" 或 "prod"
- `quality_level`: "bronze", "silver", 或 "gold"
- `callable`: false（draft 阶段）
- `source_cases`: 非空数组
- `source_patterns`: 非空数组
- 其他必需字段见 CLAUDE.md

## 发布命令（Phase 5 实现）

```bash
python -m skill_builder.cli publish-skill <skill_id>
```

### 验证步骤

1. 检查文件完整性
2. 检查质量门槛
3. 执行 human review（如果配置）
4. 移动到 published 目录
5. 更新 registry

## Registry 更新

发布后，`registry/skill_registry.json` 必须包含：

```json
{
  "skills": [
    {
      "skill_id": "luxury-hotel-festival",
      "display_name": "Luxury Hotel Festival",
      "status": "published",
      "dataset": "prod",
      "quality_level": "silver",
      "published_at": "2026-05-13T12:00:00Z",
      ...
    }
  ],
  "updated_at": "2026-05-13T12:00:00Z"
}
```

## 回滚机制

如果发布后发现问题：

1. 从 `skills/published/` 移回 `skills/draft/`
2. 从 `skill_registry.json` 移除记录
3. 记录回滚原因

## Phase 5 任务

1. [ ] 实现 publish-skill 命令
2. [ ] 实现质量门槛检查
3. [ ] 实现 registry 更新逻辑
4. [ ] 实现回滚机制
5. [ ] 定义 human review 流程

## 参见

- `docs/OPENCLAW_INTEGRATION.md` - OpenClaw 集成
- `docs/QUALITY_RUBRIC.md` - 质量标准
- `docs/HUMAN_REVIEW_GUIDE.md` - 人工审查指南