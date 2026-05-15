# Phase Board - Proposal Skill Builder

## 阶段状态

| Phase | 内容 | 状态 | 禁止项 |
|-------|------|------|--------|
| Phase 1 | Foundation CLI（intake + compile-case）| ✅ 完成 | 无 |
| Phase 2 | Vision Layer（describe-assets + ai_fragments）| ✅ 完成 | 无 |
| Phase 3 | Strategy Layer（build-strategies + StrategyUnit）| ✅ 完成 | 无 |
| Phase 3.5 | Knowledge Quality Consolidation（Fragment Compression）| 🔄 当前 | 无 |
| Phase 4 | Skill Asset Hardening | ⏳ 待开始 | 无 |
| Phase 5 | Publish + Registry | ❌ 禁止当前实现 | publish-skill, route |
| Phase 6 | OpenClaw Integration Support | ❌ 禁止当前实现 | 在线接入 |

## 当前阶段

**Phase 3.5: Knowledge Quality Consolidation**

### 目标
Fragment Compression - 压缩短文本/重复/低信息 fragments，提升 Pattern 质量

### 已完成任务
1. ✅ compression.py 实现
2. ✅ compress-fragments CLI 命令
3. ✅ composer.py 支持 compressed_fragments.json
4. ✅ skill_checker.py 压缩质量检查章节
5. ✅ 验证命令运行通过

### 数据流

```
源文件摄入
  ↓
intake → create-case → compile-case
                              ↓
                    extract-patterns
                              ↓
                    build-ai-fragments
                              ↓
                    build-strategies
                              ↓
                    compress-fragments（Phase 3.5）
                              ↓
                    compose-skill → check-skill
                              ↓
                    skills/draft/<skill_id>/
                              ↓
                    (Phase 5: publish-skill → skills/published/)
```

## Phase 路线图

```
Phase 1: Foundation CLI
  └── intake, compile-case, create-case, list-files/cases

Phase 2: Vision Layer
  └── describe-assets, build-ai-fragments

Phase 3: Strategy Layer
  └── build-strategies, strategy_dna.md

Phase 3.5: Knowledge Quality Consolidation
  └── compress-fragments, quality flags, compression report

Phase 4: Skill Asset Hardening
  └── Pattern 抽象强化, Skill 质量提升, Human Review

Phase 5: Publish + Registry
  └── publish-skill, skill_registry.json 更新（禁止当前实现）

Phase 6: OpenClaw Integration Support
  └── Registry 只读协议, Skill 文档, 调用协议（禁止当前实现）
```

## 质量标准

| 质量级别 | patterns 数 | 视觉片段 | 策略单元 |
|---------|------------|---------|---------|
| Bronze | ≥3 | - | - |
| Silver | ≥5 | ≥1 | - |
| Gold | ≥5 | ≥20 | ≥3 |

**视觉片段 < 3 时，最高只能 Silver**

## CLI 命令清单（Phase 1-4）

```
init, status, intake, create-case, list-files, list-cases,
compile-case, extract-patterns, describe-assets,
build-ai-fragments, build-strategies,
compress-fragments,
compose-skill, check-skill,
batch-compile, mark-case-dataset, mark-file-dataset,
check-ai-provider
```

## 项目非目标（绝对禁止）

1. ❌ 不做前端
2. ❌ 不做智能问答
3. ❌ 不做最终提案输出器
4. ❌ 不做完整 SaaS
5. ❌ 不做数据库（SQLite 以外）
6. ❌ 不做 Web 服务

## 禁止项（当前生效）

| 禁止项 | 所属 Phase |
|--------|-----------|
| publish-skill | Phase 5 |
| route | Phase 5 |
| 钉钉接入 | Phase 6 |
| OpenClaw 在线接入 | Phase 6 |
| 前端 | 永不 |
| 智能问答 | 永不 |
| 方案输出器 | 永不 |