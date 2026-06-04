# 工具适配说明

本 skill 是通用 agent skill，不绑定 OpenClaw、Codex 或任何单一工具。工具只影响执行深度，不影响核心流程。

## 无工具环境

如果当前 agent 不能读取文件、找图、生成图片或创建 PPT：

- 输出参考提炼。
- 输出完整中文策划正文 `content`。
- 输出 PPT 页面结构 `slides`。
- 输出视觉资产规划。
- 标注哪些素材需要用户后续补充。

## 文件读取工具

如果可以读取 PDF、PPT、docx、图片或网页：

- 优先读取原始参考资料。
- 保留来源摘要。
- 不要只依赖用户转述，除非无法访问原文件。

## 图片搜索工具

如果可以搜索图片：

- 用于 `reference_image`。
- 搜索结果只作为 moodboard 或风格参考。
- 除非用户提供授权来源，不要把搜索图默认写成最终商用素材。

## 图片生成工具

如果可以 AI 生图：

- 仅在用户明确需要成品 PPT、主视觉草图、空间概念图或当前任务需要视觉落地时生成。
- 生成前确认每张图的 `ai_prompt`、用途和比例。
- 不生成真实品牌 logo、可读文字或未授权人物肖像。

## PPT 工具

如果可以生成 PPT：

- 先确认 `content` 和 `slides` 都存在。
- `content` 用于正文、页面文案和讲述逻辑。
- `slides` 用于页序、版式、视觉建议和图片规划。
- 不要只把 `slides` 或 image prompts 传入生成器，否则容易得到 content-poor deck。

## OpenClaw 风格链路

OpenClaw 只是可选环境，不是唯一执行路径。

如果当前链路有 OpenClaw 风格的 proposal/PPT generator：

- 确认生成 dict 同时包含 `content` 和 `slides`。
- PPT 出站装配时同时传正文 sections 和 slides。
- 视觉图像可来自品牌素材、参考图或 AI 生图，但必须标注来源和用途。
- 如果生成结果只有图片提示词或页面标题，判定为失败并回到正文生成步骤。
