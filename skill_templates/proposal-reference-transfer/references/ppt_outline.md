# PPT 页面结构模板

用于把新策划正文转换成 slide-ready 的 PPT 结构。页面结构必须服务讲述，不只是目录。

## M Films 提案硬 DNA（每页必含）

调研 49 个 M Films 真实策划案总结的页眉/页脚结构，**每页都需保留**：

### 页眉（右上角，自上而下）

```
{page}              ← 页码
|                   ← 1px 宽垂直品牌绿短线
M + FILMS           ← 绿色 M + 灰字
PR VIDEOS           ← 业务范畴三件套
TVC BRANDING VIDEOS
DOCUMENTARY
```

### 页脚（右下角，自上而下）

```
[大 Logo]           ← M+FILMS Logo（M 字母品牌绿 #41FF00）
Copyright @ M+FILMS. All Right Reserved
```

### 对角 Logo 关系（封面必含）

- **客户 Logo 永远在右上角**
- **M+FILMS Logo 永远在右下角**
- 二者形成视觉对角——M Films 提案的"硬规矩"

### 章节切换（每个 4 段的开篇页）

- 章节大标题用品牌绿 #41FF00
- 标题下方必有一条**粗壮品牌绿水平色块**作为视觉引导

## 每页字段

```yaml
slides:
  - page: 1
    title: "页面标题"
    purpose: "这一页要说服客户什么"
    core_copy: "页面主文案，适合直接上 PPT"
    points:
      - "内容要点 1"
      - "内容要点 2"
      - "内容要点 3"
    visual_suggestion: "画面、图表、空间、案例或影像建议"
    speaker_note: "讲述备注"
    # 4 段式对应 page_template.yaml 的 6 段进度条：
    #   0 = 封面/项目理解
    #   1 = 创意背景
    #   2 = 创意概要
    #   3 = 创意脚本-模块一/二
    #   4 = 创意脚本-模块三/参考片
    #   5 = 视觉调性/收束
    # 在 4 段式提案中只点亮 4 个高亮段（0/2/3/5），2/4 灰显
    progress_segment: 0   # 0-5
    chapter: "cover"     # cover | background | summary | script | reference
```

## 4 段式 → 6 段进度条映射

按 `brand-style-pack/<company>/page_template.yaml` 的 `progress_bar.segments=6` 渲染时：

| 4 段式章节 | `chapter` 字段 | `progress_segment` | 进度条状态 |
|-----------|----------------|-------------------|-----------|
| 封面 | `cover` | 0 | active |
| 创意背景 | `background` | 1 | inactive |
| 创意概要 | `summary` | 2 | active |
| 创意脚本-模块一/二 | `script` | 3 | active |
| 创意脚本-模块三/参考片 | `script` / `reference` | 4 | inactive |
| 视觉调性/收束 | `reference` | 5 | active |

**渲染要求**：每页 PPT 必须输出 `progress_segment` 字段，否则进度条会缺位（这是 v0.2 实测暴露的"进度条字段未在 slides 中"问题，已修复）。

## M Films 4 段式页序（默认）

```markdown
# 封面
1. 封面: 客户 Logo 右上 + 主视觉（电影感）+ M+FILMS 右下

# 段 1 - 创意背景
2. 章节切换页: "创意背景"（绿色水平色块）
3. 背景洞察 1: 市场/品牌/受众
4. 背景洞察 2: 延展

# 段 2 - 创意概要
5. 章节切换页: "创意概要"（绿色水平色块）
6. 核心命题
7. 创意概念
8. 策略路径

# 段 3 - 创意脚本
9. 章节切换页: "创意脚本"（绿色水平色块）
10. 模块一
11. 模块二
12. 模块三

# 段 4 - 参考片 + 调性
13. 章节切换页: "参考片 + 调性"（绿色水平色块）
14. 参考片
15. 视觉调性
16. 收束页
```

**总页数估算：12-16 页**（M Films 真实案例 60%+ 在 12-15 页范围）。

brief 明确要求其他页序时按 brief；brief 限定页数（如"5 页版"）时保留"核心命题 + 策略路径 + 内容模块"。

## 要求

- 每页必须有可上 PPT 的核心文案
- **不要只输出图片 prompt**
- 不要让页面标题代替正文
- 每页**必须包含 M Films 页眉/页脚硬 DNA**（页码 + 业务范畴三件套 + 落款）
- 章节切换页必用品牌绿水平色块
- 客户 Logo 必在右上角，M+FILMS 必在右下角
