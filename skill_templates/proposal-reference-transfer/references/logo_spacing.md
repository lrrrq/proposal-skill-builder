# Logo / 装饰文字字符间距规范（v0.2）

> **来源**：`reports/huayuquan-doc-2026-07/skill-v0.2-changelog-confirmed.md §2.M-1`
> **适用**：所有 PPT logo / 装饰文字（封面、收尾、页脚、章节切换）

---

## 1. 问题背景

WPS 默认字符间距写法（依赖默认 spc，文本内手动加空格）在 LibreOffice 渲染时**会显示为字符间空格**，导致跨端不一致：

```
WPS 看到的:    M + FILMS
LibreOffice:   M   +   FILMS    ← 字符间被塞了空格
PowerPoint:    M + FILMS
```

**根因**：WPS 把每个字符当独立 run 写入 XML，但 spc 属性没设；LibreOffice 渲染时把 run 边界当作可见空格。

---

## 2. 正确写法（OOXML）

```xml
<a:r>
  <a:rPr lang="zh-CN" sz="1600" spc="300">
    <a:solidFill><a:srgbClr val="44FF05"/></a:solidFill>
  </a:rPr>
  <a:t>M + FILMS</a:t>
</a:r>
```

**spc 属性说明**：
- 单位：千分之 em（`spc="300"` = +30% tracking）
- 取值范围：-1000 ~ +1000
- 常用值：
  - `spc="300"`：M 与 + 之间 / FILMS 与前之间（视觉呼吸感）
  - `spc="0"`：默认（无字符间距调整）
  - `spc="-50"`：紧密排版（如 "M+FILMS"）

---

## 3. python-pptx 代码示例

```python
from pptx.util import Pt
from pptx.oxml.ns import qn

def add_logo_with_spc(run, text, spc_value=300, font_size=16, color_hex='44FF05'):
    """添加带字符间距的 logo 文字。"""
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor.from_string(color_hex)
    # 设置 spc 属性
    rPr = run._r.get_or_add_rPr()
    rPr.set('spc', str(spc_value))

# 用法
run = paragraph.add_run()
add_logo_with_spc(run, 'M + FILMS', spc_value=300, font_size=16, color_hex='44FF05')
```

---

## 4. 错误写法（禁止）

```xml
<!-- 错误 1：默认 spc + 文本内手动加空格 -->
<a:r>
  <a:rPr lang="zh-CN" sz="1600"/>
  <a:t>M   +   FILMS</a:t>
</a:r>

<!-- 错误 2：依赖默认 spc 不设置 -->
<a:r>
  <a:rPr lang="zh-CN" sz="1600"/>
  <a:t>M+FILMS</a:t>
</a:r>
```

---

## 5. 验证标准

```
grep '<a:rPr spc=' skill_templates/proposal-reference-transfer/SKILL.md ≥1
grep '<a:rPr spc=' skill_templates/proposal-reference-transfer/references/ ≥2
```

通过 = v0.2 字符间距规范生效。