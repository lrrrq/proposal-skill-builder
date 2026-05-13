# Skill Check Report: w-hotel-mid-autumn

**检查时间**: 2026-05-13T18:39:08.483127
**Skill 目录**: /Applications/lrq/coding/proposal-skill-builder/skills/draft/w-hotel-mid-autumn

---

## 基本信息

- **skill_id**: w-hotel-mid-autumn
- **dataset**: prod
- **当前 quality_level**: bronze
- **检查后建议 quality_level**: **failed**
- **评分**: 65.2/100

**建议**: source_patterns 只有 1 个，少于 3

---

## 检查结果汇总

- **结构检查**: 4 通过 / 0 失败
- **状态检查**: 6 通过 / 0 失败
- **章节检查**: 9 通过 / 3 失败
- **压缩检查**: 1 通过 / 0 失败

## 分数明细

- **structure**: 15/? - 文件存在(3/3) + 字段完整(12/12)
- **traceability**: 5.2/? - 案例(2.5/5) + Patterns(0.5/5) + Fragments(2.2/5)
- **abstract**: 2/? - 可复用策略 1 条 (2/20)
- **process**: 15/? - 处理流程 5 步 (15/15)
- **output**: 8/? - 输出格式 4 条 (8/10)
- **visual**: 6/? - 视觉策略 (6/10) [有警告]
- **examples**: 10/? - Brief(2个) + 输出方向(2个) = 10/10
- **limits**: 4/? - 限制条件 4 条 (4/5)

**总分**: 65.2/100

## ✅ 通过项

- skill.json 存在
- SKILL.md 存在
- examples.md 存在
- skill.json 字段完整
- status = draft
- callable = false
- dataset = prod
- source_cases 有 1 个案例
- source_patterns 有 1 个
- source_strategies 有 2 个
- 章节『适用场景』存在
- 章节『输入要求』存在
- 章节『处理流程』存在
- 章节『输出格式』存在
- 章节『可复用策略』存在
- 章节『视觉策略』存在
- 章节『受众洞察』存在
- 章节『限制条件』存在
- 章节『来源案例』存在
- ⚠️ 未运行 compress-fragments（compressed_fragments.json 不存在）

## ❌ 失败项

- 缺少章节『核心判断逻辑』
- 缺少章节『内容结构策略』
- 缺少章节『执行方法』

- 视觉片段仅 0 个，视觉策略可信度受限
- 当前等级 (bronze) 与建议等级 (failed) 不一致
- 总分 65.2 < 75，质量有待提升

## 📋 发布建议

❌ **不建议发布**（建议等级: failed，评分: 65.2）

---

*由 Proposal Skill Builder 自动生成*