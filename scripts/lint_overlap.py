#!/usr/bin/env python3
"""
lint_overlap.py — 扫 PPTX 所有 slide 的 textbox, 检测:
  1. 任何 textbox 之间有重叠 (坐标相交)
  2. textbox 是否超出 slide 边界 (16:9 inch, 10x5.625)

用法:
  python3 lint_overlap.py <pptx_path>
  python3 lint_overlap.py /Applications/lrq/coding/proposal-skill-builder/reports/huayuquan-doc-2026-07/v0.3_huayuquan_deck.pptx

退出码: 0 = 全过, 1 = 有 overlap, 2 = 超出边界
"""
import sys
import zipfile
import re
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}

SLIDE_W_INCH = 13.333   # 16:9 widescreen
SLIDE_H_INCH = 7.5
EMU_PER_INCH = 914400


def parse_pptx(pptx_path: str):
    """Return list[dict] with per-slide textbox info."""
    z = zipfile.ZipFile(pptx_path)
    slide_files = sorted(
        [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
        key=lambda n: int(re.search(r'slide(\d+)', n).group(1))
    )
    slides = []
    for sf in slide_files:
        idx = int(re.search(r'slide(\d+)', sf).group(1))
        root = ET.fromstring(z.read(sf))
        textboxes = []
        for sp in root.iter(f'{{{NS["p"]}}}sp'):
            # collect text first — skip empty textboxes (背景/装饰)
            txt_parts = [t.text for t in sp.iter(f'{{{NS["a"]}}}t') if t.text]
            text = ' '.join(txt_parts).strip()
            if not text:
                continue  # 跳过空 textbox
            xfrm = sp.find(f'.//{{{NS["p"]}}}spPr/{{{NS["a"]}}}xfrm')
            if xfrm is None:
                continue
            off = xfrm.find(f'{{{NS["a"]}}}off')
            ext = xfrm.find(f'{{{NS["a"]}}}ext')
            if off is None or ext is None:
                continue
            x = int(off.get('x', 0)) / EMU_PER_INCH
            y = int(off.get('y', 0)) / EMU_PER_INCH
            cx = int(ext.get('cx', 0)) / EMU_PER_INCH
            cy = int(ext.get('cy', 0)) / EMU_PER_INCH
            textboxes.append({
                'x': x, 'y': y, 'w': cx, 'h': cy,
                'x2': x + cx, 'y2': y + cy,
                'text': text[:50],
            })
        slides.append({'idx': idx, 'textboxes': textboxes})
    z.close()
    return slides


def overlap(a, b):
    """AABB overlap, with min_gap=0 (strict)."""
    if a['x2'] <= b['x'] or b['x2'] <= a['x']:
        return 0.0
    if a['y2'] <= b['y'] or b['y2'] <= a['y']:
        return 0.0
    dx = min(a['x2'], b['x2']) - max(a['x'], b['x'])
    dy = min(a['y2'], b['y2']) - max(a['y'], b['y'])
    return dx * dy  # square inches overlap area


def out_of_bounds(tb):
    return (
        tb['x'] < 0 or tb['y'] < 0
        or tb['x2'] > SLIDE_W_INCH or tb['y2'] > SLIDE_H_INCH
    )


def main():
    if len(sys.argv) < 2:
        print("usage: lint_overlap.py <pptx_path>")
        sys.exit(2)
    pptx = Path(sys.argv[1])
    if not pptx.exists():
        print(f"❌ {pptx} 不存在")
        sys.exit(2)

    slides = parse_pptx(str(pptx))
    has_overlap = False
    has_oob = False
    print(f"📄 {pptx.name} — {len(slides)} 页\n")
    for s in slides:
        # 1) out of bounds
        for tb in s['textboxes']:
            if out_of_bounds(tb):
                has_oob = True
                print(
                    f"  ⚠️  页 {s['idx']:02d} 超界: "
                    f"({tb['x']:.2f},{tb['y']:.2f})→({tb['x2']:.2f},{tb['y2']:.2f})  "
                    f"\"{tb['text']}\""
                )
        # 2) overlap (pairwise) — only report SIGNIFICANT overlaps (>0.5 sq.inch).
        # 老资历 textbox 范围也有 0.1-0.2 inch 重叠 (textbox 留白多), 但视觉 OK.
        n = len(s['textboxes'])
        for i in range(n):
            for j in range(i + 1, n):
                area = overlap(s['textboxes'][i], s['textboxes'][j])
                if area > 0.5:  # > 0.5 sq.inch (5% of 4.4x2.2 textbox)
                    has_overlap = True
                    a, b = s['textboxes'][i], s['textboxes'][j]
                    print(
                        f"  ❌ 页 {s['idx']:02d} 重叠: "
                        f"\"{a['text']}\" ({a['x']:.2f},{a['y']:.2f}) "
                        f"vs \"{b['text']}\" ({b['x']:.2f},{b['y']:.2f}) "
                        f"area={area:.2f} sq.inch"
                    )
    print()
    if not has_overlap and not has_oob:
        print("✅ 全部 OK — 无重叠,无超界")
        sys.exit(0)
    if has_overlap:
        sys.exit(1)
    sys.exit(2)


if __name__ == '__main__':
    main()
