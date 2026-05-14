# Stage F.2 Failure Log

## case_0003 - W酒店中秋创意方案

**状态**: FAILED (NOT_READY for Skill extraction)

**失败原因**:
- 源文件格式: PPTX
- fragments: 22个，但全部是 short 型，无实质内容（版权声明/格式文本）
- ai_fragments: 0 (LibreOffice 未安装，无法提取视觉层)
- patterns: 1 (版权声明类垃圾文本，pattern_type=visual_direction)
- strategies: 2 (模板填充，无实质内容)

**核心问题**:
case_0003 的创意价值在视觉图像中，但 LibreOffice 未安装导致无法提取。文本层只有版权声明。重复处理不会改善结果。

**结论**: 不值得修复。已冻结为失败样本。

---

## w-hotel-mid-autumn (draft Skill)

**状态**: FAILED_DRAFT

**来源**: case_0003
**check-skill 结果**:
- score: 65.2/100
- suggested_level: failed
- passed: 20
- failed: 3

**失败原因**:
- 缺少章节『核心判断逻辑』
- 缺少章节『内容结构策略』
- 缺少章节『执行方法』
- 视觉片段仅 0 个
- source_patterns 只有 1 个

**结论**: 不允许发布。仅作为失败 draft 保留供参考。

---

## 已确认不适合的 case

| case_id | verdict | 原因 |
|---------|---------|------|
| case_0001 | NOT_READY | fragments=1，无实质内容 |
| case_0002 | NOT_READY | fragments=1，无实质内容 |
| case_0003 | WEAK (→FAIL) | PPTX 视觉内容无法提取，patterns=1, strategies=2 |

---

*记录时间: 2026-05-14*