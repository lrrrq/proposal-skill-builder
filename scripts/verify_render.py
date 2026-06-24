"""
verify_render.py — 重跑 deck.pptx + 渲染全部页为 PNG, 一键视觉验证

用法:
  python3 scripts/verify_render.py

前置:
  - LibreOffice 装在 /Volumes/LibreOffice/LibreOffice.app (dmg 已挂)
  - PyMuPDF 装好 (pip install pymupdf)

输出:
  - /tmp/deck_pXX.png (18 张渲染图)
  - /tmp/deck_render_report.md (页面大小汇总)

为什么这个脚本很重要:
  之前我只看 OOXML 文字一致就报完美, 但视觉层完全没验证.
  这个脚本能让我用 Read image 自己看每一页.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

import fitz  # PyMuPDF


SOFFICE = "/Volumes/LibreOffice/LibreOffice.app/Contents/MacOS/soffice"
DECK_PPTX = "/Applications/lrq/coding/proposal-skill-builder/reports/huayuquan-doc-2026-07/deck.pptx"
OUT_DIR = "/tmp"


def step(msg):
    print(f"▶ {msg}", flush=True)


def gen_deck():
    step("重跑 gen_deck.py")
    os.chdir("/Applications/lrq/coding/proposal-skill-builder/reports/huayuquan-doc-2026-07")
    result = subprocess.run(["python3", "gen_deck.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ gen_deck.py 失败:\n{result.stderr}")
        sys.exit(1)
    for line in result.stdout.split('\n')[-3:]:
        print(f"   {line}")


def to_pdf():
    step("PPT → PDF (LibreOffice)")
    if not Path(SOFFICE).exists():
        print(f"❌ LibreOffice 没装: {SOFFICE}")
        print(f"   重新挂载: hdiutil attach -noverify -nobrowse /tmp/libreoffice.dmg")
        sys.exit(1)
    pdf_out = "/tmp/deck.pdf"
    if Path(pdf_out).exists():
        Path(pdf_out).unlink()
    result = subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", "/tmp", DECK_PPTX],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0 or not Path(pdf_out).exists():
        print(f"❌ PDF 转换失败:\n{result.stderr}")
        sys.exit(1)
    size_kb = Path(pdf_out).stat().st_size / 1024
    print(f"   ✅ /tmp/deck.pdf ({size_kb:.1f} KB)")


def pdf_to_pngs():
    step("PDF → 18 张 PNG (PyMuPDF)")
    doc = fitz.open("/tmp/deck.pdf")
    for f in Path(OUT_DIR).glob("deck_p*.png"):
        f.unlink()
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        pix.save(f"{OUT_DIR}/deck_p{i+1:02d}.png")
    doc.close()
    pngs = sorted(Path(OUT_DIR).glob("deck_p*.png"))
    print(f"   ✅ {len(pngs)} 张 PNG: {pngs[0].name} ... {pngs[-1].name}")


def report():
    step("报告")
    md = ["# Deck 渲染报告\n"]
    md.append(f"- **PPTX**: `{DECK_PPTX}`")
    md.append(f"- **PDF**: /tmp/deck.pdf")
    md.append(f"- **PNG**: /tmp/deck_p01.png - deck_p18.png (18 张)\n")

    md.append("## 18 页文件大小\n")
    md.append("| 页 | 文件大小 (KB) |")
    md.append("|---|---------------|")
    for p in sorted(Path(OUT_DIR).glob("deck_p*.png")):
        size_kb = p.stat().st_size / 1024
        md.append(f"| {p.stem.replace('deck_p', '')} | {size_kb:.1f} |")

    md.append("\n## 视觉验证清单 (你 / 我可以用 Read image 抽查)\n")
    md.append("- [ ] 页 1: 封面不重叠")
    md.append("- [ ] 页 2: 章节大字 'Creative Background' 不换行不裁字")
    md.append("- [ ] 页 3 / 4 / 5: 标题跟正文不重叠")
    md.append("- [ ] 页 9: '策略路径' 标题 (用户上次截图说错版) 修好")
    md.append("- [ ] 页 11 / 12: 带图内容页布局正常")
    md.append("- [ ] 页 18: 封底 Thank you + M+FILMS + Copyright 不重叠")

    out = "/tmp/deck_render_report.md"
    Path(out).write_text('\n'.join(md), encoding='utf-8')
    print(f"   ✅ {out}")


def lint_overlap():
    """第 5 步: 跑 lint_overlap.py 检测 textbox 重叠 (v0.3.1+)"""
    step("textbox 重叠检测 (lint_overlap.py)")
    lint_script = Path("/Applications/lrq/coding/proposal-skill-builder/scripts/lint_overlap.py")
    if not lint_script.exists():
        print(f"   ⚠️ {lint_script} 不存在, 跳过")
        return
    result = subprocess.run(
        ["python3", str(lint_script), DECK_PPTX],
        capture_output=True, text=True, timeout=60
    )
    # 把输出逐行打印
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"   {line}")
    if result.returncode == 0:
        print(f"   ✅ lint 全过")
    else:
        print(f"   ❌ lint 退出码 {result.returncode}, 报告中有 overlap")
        # 不 sys.exit(1), 让 report 还能跑


def main():
    if not Path(DECK_PPTX).exists():
        print(f"❌ PPT 不存在: {DECK_PPTX}")
        sys.exit(1)
    gen_deck()
    to_pdf()
    pdf_to_pngs()
    lint_overlap()  # v0.3.1+ 新增
    report()
    print(f"\n🎯 全部就绪 — 用 Read image 看 /tmp/deck_pXX.png 自己验证")


if __name__ == '__main__':
    main()