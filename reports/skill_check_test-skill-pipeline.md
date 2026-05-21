# Skill Check Report: test-skill-pipeline

**检查时间**: 2026-05-21T13:19:17.167682
**Skill 目录**: /Applications/lrq/coding/proposal-skill-builder/skills/draft/test-skill-pipeline

---

## 基本信息

- **skill_id**: test-skill-pipeline
- **dataset**: prod
- **当前 quality_level**: bronze
- **检查后建议 quality_level**: **silver**
- **评分**: 75.6/100

**建议**: 分数 75.6 在 75-89 之间

---

## 检查结果汇总

- **结构检查**: 4 通过 / 0 失败
- **状态检查**: 6 通过 / 0 失败
- **章节检查**: 11 通过 / 1 失败
- **压缩检查**: 3 通过 / 0 失败

## 分数明细

- **structure**: 15/? - 文件存在(3/3) + 字段完整(12/12)
- **traceability**: 8.6/? - 案例(2.5/5) + Patterns(2.0/5) + Fragments(4.1000000000000005/5)
- **abstract**: 8/? - 可复用策略 4 条 (8/20)
- **process**: 15/? - 处理流程 5 步 (15/15)
- **output**: 8/? - 输出格式 4 条 (8/10)
- **visual**: 6/? - 视觉策略 (6/10) [有警告]
- **examples**: 10/? - Brief(2个) + 输出方向(2个) = 10/10
- **limits**: 5/? - 限制条件 5 条 (5/5)

**总分**: 75.6/100

## ✅ 通过项

- skill.json 存在
- SKILL.md 存在
- examples.md 存在
- skill.json 字段完整
- status = draft
- callable = false
- dataset = prod
- source_cases 有 1 个案例
- source_patterns 有 4 个
- source_strategies 有 5 个
- 章节『适用场景』存在
- 章节『输入要求』存在
- 章节『核心判断逻辑』存在
- 章节『处理流程』存在
- 章节『输出格式』存在
- 章节『可复用策略』存在
- 章节『视觉策略』存在
- 章节『内容结构策略』存在
- 章节『受众洞察』存在
- 章节『限制条件』存在
- 章节『来源案例』存在
- compressed_fragments.json 存在（41 个压缩后 fragments）
- 低质量 fragments 占比 22.0%（可接受）
- too_short fragments 比例正常（0/41）

## ❌ 失败项

- 缺少章节『执行方法』

- 视觉片段仅 0 个，视觉策略可信度受限
- 当前等级 (bronze) 与建议等级 (silver) 不一致

## Compression Quality

- **Total Compressed**: 41
- **Low Quality Ratio**: 22.0%

**Quality Distribution**:
- low_information (低信息密度): 9

## 📋 发布建议

✅ **可以发布**（建议等级: silver，评分: 75.6）

---

*由 Proposal Skill Builder 自动生成*