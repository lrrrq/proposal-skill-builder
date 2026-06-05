# PPT 视觉资产规划模板

用于为 PPT 每页规划图片、参考图或 AI 生图。图片是策划表达的辅助，不替代方案正文。

## 图片来源优先级

按 brand-style-pack 优先（**不凭空搜图**）：

1. `brand_asset`：`brand-style-pack/<company>/assets/` 已有素材（logo、产品图、KV、门店/场地、过往活动照片）
2. `reference_image`：`brand-style-pack/<company>/reference_images/` 风格参考图
3. `ai_generated`：AI 生成概念图，prompt 含 pack 中的 visual_motifs
4. `no_image`：策略页、流程页、表格页，可用文字、图表或留白

**默认不从公网搜图**——除非 pack 中确实没有对应素材，且 brief 明确要求新参考。

## 每页 visual 字段

```yaml
visual:
  role: "主视觉 / 氛围图 / 案例参考 / 空间示意 / 流程图 / 信息图"
  source_type: "brand_asset | reference_image | ai_generated | no_image"
  source_path: "brand-style-pack/m-films/reference_images/03_cinematic.png"  # source_type 非 no_image 时必填
  reference_query: "如需在 pack 外找参考图，写搜索关键词"
  ai_prompt: "如需 AI 生图，写完整提示词（必含 pack 中的 visual_motifs）"
  composition: "主体、前景、中景、背景、视角、构图关系"
  style_constraints: "品牌色、材质、光线、人物、空间、摄影或插画风格（从 pack 引用）"
  avoid: "不要出现的元素、错误品牌语义、错误 logo、错误文字"
  aspect_ratio: "16:9"  # 海报 9:16, 微信 1:1, KV 16:9
  usage_note: "品牌授权素材 / 参考图 / AI 概念图 / 待用户确认素材"
```

## 选择规则

- pack 中有明确品牌素材 → 优先 `brand_asset`
- pack 中有对应风格参考图 → `reference_image`
- 需要不存在的概念画面、空间想象或主视觉草图 → `ai_generated`（**prompt 必含 pack 的 visual_motifs**）
- 策略页、流程页、表格页不强行配图 → `no_image`

## M Films visual_motifs（AI 生图必含）

> 来自 M Films 49 策划案 + 5 年设计资产生成的视觉语料。

```yaml
m-films:
  cinematography:
    - long_exposure_light_painting      # 长曝光光绘
    - low_saturation_dramatic_lighting  # 低饱和度戏剧光
    - motion_blur_dynamic                # 动态模糊
    - high_contrast_chiaroscuro          # 高对比度明暗对照
  typography:
    - ultra_extended_bold                # 极宽扩展粗体
    - calligraphy_meets_sans_serif      # 书法 × 无衬线混搭
  geometric_motifs:
    - circle_seal                        # 圆形印章
    - x_cross_marker                     # X 形准星
    - hex_grid_pattern                   # 六边形蜂巢
    - horizontal_division_block          # 水平分隔色块
  forbidden_in_ai_prompt:
    - 奢华金
    - 大面积暖色调
    - 渐变色滥用
    - 传统中国风符号堆砌
```

## AI 生图 prompt 要求

- 必含主体、场景、构图、光线、色彩、材质、情绪、用途
- 必含 brand-style-pack 中的 visual_motifs
- 必含 pack 中的 colors（hex 优先）
- 避免要求生成真实品牌 logo / 可读文字 / 未授权人物肖像
- 默认 `16:9`（海报 9:16 / 微信 1:1 / KV 16:9 可调）

## 参考图要求

- 参考图只用于 moodboard、方向判断和客户沟通
- **不要把参考图当最终商用图**，除非用户明确提供授权
- pack 中有 → 直接引用；pack 中无 → 询问用户（见 SKILL.md 询问机制）
- 搜索词要具体到场景、风格、材质、空间或镜头语言

## reference_images 缺失时的降级机制（v0.2 修复）

> v0.2 实测发现：`brand-style-pack/m-films/reference_images/` 目录尚未填充真实素材。
> skill 必须明确"pack 中无 reference_images 时怎么走"，否则下游 agent 会卡住。

按以下优先级降级：

1. **检查 pack 路径**：`brand-style-pack/<company>/reference_images/`
   - 存在且有图片 → 直接引用（`source_type: reference_image`）
   - 不存在 / 为空 → 走第 2 步
2. **降级到 brand_asset**：检查 `brand-style-pack/<company>/assets/` 是否有可作参考的素材
   - 有 → `source_type: brand_asset`（用 KV / 案例图 / 门店照作风格参考）
   - 没有 → 走第 3 步
3. **降级到 ai_generated**：用 pack 中的 `visual_motifs` + `colors` 生成概念图
   - prompt 必含 `m-films.visual_motifs` 中的 2-3 个 motifs
   - prompt 必含 `m-films.colors` 中的主色 hex
   - `usage_note: "AI 概念图 - 需客户确认，非最终商用素材"`
4. **询问用户**（见 SKILL.md 询问机制）：让用户选择
   - (a) 跳过该页图片（`no_image`）
   - (b) 用 M Films 历史 49 策划案 PDF 中找相似场景（`source_path: source_proposals/accepted/<case>.pdf`）
   - (c) 等用户后续补素材

**强制要求**：当 source_type = `reference_image` 但 pack 中无对应文件时，**agent 必须在输出中标注 `reference_images_missing: true`** 并触发降级流程。禁止假装引用了一个不存在的文件。

## 跨公司复用

换公司时**只换 brand-style-pack**，visual 字段的 source_path 自动指向新 pack：

- `brand-style-pack/m-films/reference_images/...`
- `brand-style-pack/eth-corp/reference_images/...`（举例）
- 同一 skill 模板，不同公司视觉
