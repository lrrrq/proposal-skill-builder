# OpenClaw Integration Guide

> **状态**: 占位文档 - 待 Phase 6 实现

## 概述

本文档描述 Proposal Skill Builder 与 OpenClaw 的集成方式。

**核心定位**：本项目是离线 Skill 资产编译器 + Registry 资产准备器，OpenClaw 负责最终的 Brief 理解和方案输出。

## 集成架构

```
Proposal Skill Builder (CLI)
       │
       │ 离线编译
       ▼
skills/published/     ← OpenClaw 只读访问
registry/
       │
       ▼
   OpenClaw
   (Brief 理解 + 方案输出)
```

## OpenClaw 只读访问协议

### 访问路径

```
Base: /Applications/lrq/coding/proposal-skill-builder

Registry:
  - registry/skill_registry.json  (Skill 注册表)
  - skills/published/              (已发布 Skills)

Case 数据（只读）:
  - compiled/cases/<case_id>/
    ├── source_meta.json
    ├── fragments.json
    ├── ai_fragments.json
    ├── patterns.json
    ├── strategies.json
    └── strategy_dna.md
```

### Skill 目录结构

```
skills/published/<skill_id>/
├── SKILL.md          # Skill 定义文档
├── skill.json        # Skill 元数据
└── examples.md       # 调用示例
```

## 调用协议

### 获取所有 Skills

```python
import json

registry_path = "registry/skill_registry.json"
with open(registry_path, "r") as f:
    registry = json.load(f)

skills = registry.get("skills", [])
for skill in skills:
    print(skill["skill_id"], skill["display_name"])
```

### 读取单个 Skill

```python
skill_id = "luxury-hotel-festival"
skill_dir = f"skills/published/{skill_id}/"

with open(f"{skill_dir}/skill.json", "r") as f:
    skill_meta = json.load(f)

with open(f"{skill_dir}/SKILL.md", "r") as f:
    skill_content = f.read()
```

### 获取 Case 数据

```python
case_id = "case_0004"
case_dir = f"compiled/cases/{case_id}/"

# 读取 Strategy DNA
with open(f"{case_dir}/strategy_dna.md", "r") as f:
    strategy_dna = f.read()

# 读取 Patterns
with open(f"{case_dir}/patterns.json", "r") as f:
    patterns = json.load(f)
```

## 调用示例

### 示例 Brief：奢侈品牌春节活动

```
客户：国际奢侈酒店品牌
活动：春节期间高端定制活动
目标客群：高净值家庭（企业主、金融从业者）
预算：约 200 万元
需求：完整的活动方案
```

### OpenClaw 调用流程

1. 读取 `registry/skill_registry.json` 获取可用 Skills
2. 根据 Brief 类型选择合适 Skill
3. 读取 `skills/published/<skill_id>/SKILL.md` 获取调用指南
4. 结合客户需求生成定制方案

## 限制说明

- 本项目**不提供**在线 API
- 本项目**不提供**方案生成服务
- OpenClaw 必须有本地文件系统访问权限
- 所有数据为只读，不支持写入操作

## Phase 6 任务

1. [ ] 验证 OpenClaw 只读访问协议
2. [ ] 完善调用示例
3. [ ] 测试 Registry 读取
4. [ ] 文档完善

## 参见

- `docs/PUBLISH_CONTRACT.md` - Skill 发布契约
- `docs/QUALITY_RUBRIC.md` - 质量标准
- `docs/HUMAN_REVIEW_GUIDE.md` - 人工审查指南