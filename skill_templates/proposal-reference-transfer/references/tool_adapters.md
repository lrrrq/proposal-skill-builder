# 工具适配说明

工具只影响执行深度，不影响核心流程。**OpenClaw 是默认推荐路径**（如有）。

## 无工具环境（默认 fallback）

agent 不能读取文件、找图、生图、生成 PPT：

- 交付完整 `content` + `slides` + 视觉规划
- 标注哪些素材需要用户后续补充

## 有工具环境

按可用工具按需触发：

### 文件读取

- 优先读取原始参考资料（PDF / PPT / docx / 图片 / 网页）
- 保留来源摘要

### 图片搜索

- 用于 `reference_image` 来源标注
- 搜索结果只做 moodboard / 风格参考
- 商用授权必须用户明确提供

### AI 生图

- 仅在用户明确需要成品或任务需要视觉落地时生成
- `ai_prompt` 必含 brand-style-pack 中的 `visual_motifs` + colors
- 不生成真实品牌 logo / 可读文字 / 未授权人物肖像

### PPT 生成

- 必须同时传 `content` 和 `slides`
- 不要只传 `slides` 或 image prompts（容易得 content-poor deck）

### OpenClaw 链路（推荐默认）

如有 OpenClaw 风格的 proposal/PPT generator：

- 走 OpenClaw 路径（首选）
- 生成 dict 同时含 `content` + `slides`
- 视觉图像可来自品牌素材 / 参考图 / AI 生图，**必须标注 source**
- 生成结果只有图片提示词或页面标题 → 判定失败，回到正文生成
