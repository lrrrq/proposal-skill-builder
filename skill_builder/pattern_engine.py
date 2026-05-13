"""
pattern_engine - Pattern 提取
"""

import json
import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config
from .db import get_connection
from .utils import now_iso


# Pattern 类型定义
PATTERN_TYPES = {
    "strategy": ["目标", "目的", "策略", "定位", "核心", "价值", "品牌", "差异化", "优势"],
    "content_structure": ["目录", "流程", "章节", "结构", "框架", "模块", "层次", "逻辑"],
    "visual_direction": ["视觉", "风格", "画面", "色彩", "设计", "图形", "排版", "字体", "色调"],
    "audience_insight": ["用户", "客户", "人群", "受众", "会员", "消费者", "目标群体", "画像"],
    "execution_method": ["执行", "落地", "排期", "预算", "物料", "实施", "步骤", "时间节点", "资源"],
}


def generate_pattern_id() -> str:
    """生成短 pattern ID"""
    return uuid.uuid4().hex[:12]


def detect_pattern_types(text: str) -> List[str]:
    """检测文本中包含的 pattern 类型"""
    detected = []
    text_lower = text.lower()

    for pattern_type, keywords in PATTERN_TYPES.items():
        for keyword in keywords:
            if keyword in text_lower:
                if pattern_type not in detected:
                    detected.append(pattern_type)
                break  # 一个匹配就够

    return detected


def build_pattern_name(pattern_type: str, index: int) -> str:
    """构建 pattern 名称"""
    type_names = {
        "strategy": "策略",
        "content_structure": "内容结构",
        "visual_direction": "视觉方向",
        "audience_insight": "受众洞察",
        "execution_method": "执行方法",
    }
    return f"{type_names.get(pattern_type, pattern_type)}_{index:02d}"


def build_pattern_description(pattern_type: str, fragments: List[Dict]) -> str:
    """构建 pattern 描述"""
    if not fragments:
        return ""

    # 取所有片段的 summary 拼接
    summaries = [f.get("summary", "")[:60] for f in fragments if f.get("summary")]
    if summaries:
        return " | ".join(summaries[:3])
    return ""


def extract_patterns(case_id: str, fragments: List[Dict]) -> List[Dict]:
    """
    从 fragments 中提取 patterns（保留旧接口，内部调用 extract_patterns_with_layer）
    """
    return extract_patterns_with_layer(case_id, fragments)


def extract_patterns_with_layer(case_id: str, fragments: List[Dict]) -> List[Dict]:
    """
    从 fragments 中提取 patterns，支持 source_layer 追踪

    规则：
    - 按 pattern_type 分组
    - 每个 fragment 可能属于多个 pattern_type
    - 同类型的 fragment 聚合成一个 pattern
    - patterns.json 中记录每个 pattern 的 source_fragment_ids（含 layer 信息）
    """
    # 按 type 分组
    type_to_fragments = {pt: [] for pt in PATTERN_TYPES.keys()}

    for frag in fragments:
        raw_text = frag.get("raw_text", "")
        if not raw_text.strip():
            continue

        detected_types = detect_pattern_types(raw_text)

        for ptype in detected_types:
            type_to_fragments[ptype].append(frag)

    # 构建 patterns
    patterns = []
    pattern_counter = {pt: 0 for pt in PATTERN_TYPES.keys()}

    for ptype, frags in type_to_fragments.items():
        if not frags:
            continue

        pattern_counter[ptype] += 1
        pattern_id = generate_pattern_id()
        pattern_name = build_pattern_name(ptype, pattern_counter[ptype])

        # source_fragment_ids 带 layer 标记
        source_ids = []
        text_count = 0
        vision_count = 0
        for f in frags:
            fid = f.get("fragment_id", "")
            layer = f.get("source_layer", "text")
            source_ids.append({"fragment_id": fid, "layer": layer})
            if layer == "vision":
                vision_count += 1
            else:
                text_count += 1

        # confidence: 基于 fragment 数量
        confidence = min(0.5 + len(frags) * 0.1, 1.0)

        # quality: 基于 fragment quality_flags
        all_flags = []
        for f in frags:
            all_flags.extend(f.get("quality_flags", []))
        has_empty = "empty" in all_flags
        quality = "low" if has_empty else ("medium" if len(frags) > 1 else "high")

        # 来源统计
        source_summary = []
        if text_count > 0:
            source_summary.append(f"文本×{text_count}")
        if vision_count > 0:
            source_summary.append(f"视觉×{vision_count}")

        pattern = {
            "pattern_id": pattern_id,
            "case_id": case_id,
            "name": pattern_name,
            "pattern_type": ptype,
            "description": build_pattern_description(ptype, frags),
            "source_fragment_ids": source_ids,
            "fragment_count": len(frags),
            "confidence_score": round(confidence, 2),
            "quality_level": quality,
            "source_summary": " | ".join(source_summary) if source_summary else "unknown",
        }

        patterns.append(pattern)

    return patterns


def generate_case_card(case_id: str, patterns: List[Dict], meta: Dict = None,
                      fragments: List[Dict] = None, ai_fragments: List[Dict] = None) -> str:
    """
    生成 case_card.md 内容

    Args:
        case_id: Case ID
        patterns: patterns 列表
        meta: source_meta.json 内容
        fragments: 文本 fragments 列表
        ai_fragments: 视觉 ai_fragments 列表
    """
    lines = [
        f"# Case Card: {case_id}",
        "",
    ]

    if meta:
        lines.extend([
            f"**标题**: {meta.get('title', '未命名')}",
            f"**来源文件**: {meta.get('original_filename', '未知')}",
            f"**数据集**: {meta.get('dataset', 'prod')}",
            f"**创建时间**: {meta.get('created_at', '未知')}",
            "",
            "---",
            "",
        ])

    # Fragment 统计
    text_count = len(fragments) if fragments else 0
    vision_count = len(ai_fragments) if ai_fragments else 0

    lines.extend([
        "## Fragment 统计",
        "",
        f"- **文本 Fragments**: {text_count}",
        f"- **视觉 AI Fragments**: {vision_count}",
        f"- **Patterns 总数**: {len(patterns)}",
        "",
    ])

    # 分层 Patterns
    text_patterns = [p for p in patterns if "文本×" in p.get("source_summary", "")]
    vision_patterns = [p for p in patterns if "视觉×" in p.get("source_summary", "")]

    if text_patterns:
        lines.extend([
            "### 文本 Patterns",
            "",
        ])
        for p in text_patterns:
            lines.append(f"- **{p['name']}** ({p['pattern_type']}): {p.get('description', '')[:60]}...")
        lines.append("")

    if vision_patterns:
        lines.extend([
            "### 视觉 Patterns",
            "",
        ])
        for p in vision_patterns:
            lines.append(f"- **{p['name']}** ({p['pattern_type']}): {p.get('description', '')[:60]}...")
        lines.append("")

    # 摘要
    if patterns:
        summaries = [p.get("description", "")[:80] for p in patterns[:3] if p.get("description")]
        if summaries:
            lines.extend([
                "## 核心摘要",
                "",
                " | ".join(summaries),
                "",
            ])

    # Patterns 详情
    lines.extend([
        "## Patterns 详情",
        "",
    ])

    if patterns:
        for p in patterns:
            lines.append(f"### {p['name']} ({p['pattern_type']})")
            lines.append(f"- **ID**: `{p['pattern_id']}`")
            lines.append(f"- **置信度**: {p['confidence_score']}")
            lines.append(f"- **质量**: {p['quality_level']}")
            lines.append(f"- **片段数**: {p['fragment_count']}")
            if p.get("description"):
                lines.append(f"- **描述**: {p['description'][:100]}")
            lines.append("")
    else:
        lines.append("*暂无提取到 Patterns（源内容太少）*")
        lines.append("")

    # 可复用价值
    lines.extend([
        "## 可复用价值",
        "",
    ])

    if patterns:
        types = [p['pattern_type'] for p in patterns]
        type_labels = {
            "strategy": "策略定位能力",
            "content_structure": "内容结构能力",
            "visual_direction": "视觉呈现能力",
            "audience_insight": "受众洞察能力",
            "execution_method": "执行落地能力",
        }
        values = [type_labels.get(t, t) for t in types if t in type_labels]
        if values:
            lines.extend([f"- {v}" for v in values])
        else:
            lines.append("- 待定")
    else:
        lines.append("- 待定（需补充源案例内容）")

    lines.extend([
        "",
        "## 质量风险",
        "",
    ])

    if patterns:
        low_quality = [p for p in patterns if p['quality_level'] == 'low']
        if low_quality:
            lines.append(f"- {len(low_quality)} 个 Pattern 质量较低（源内容不足）")
        else:
            lines.append("- 无明显风险")
    else:
        lines.append("- 源案例内容过少，无法提取有效 Pattern")
        lines.append("- 建议补充更完整的策划案文档")

    lines.extend([
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    return "\n".join(lines)


def load_fragments(case_id: str) -> Optional[List[Dict]]:
    """加载 case 的 fragments"""
    fragments_path = Config.CASES_DIR / case_id / "fragments.json"
    if not fragments_path.exists():
        return None

    with open(fragments_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_meta(case_id: str) -> Optional[Dict]:
    """加载 case 的 meta"""
    meta_path = Config.CASES_DIR / case_id / "source_meta.json"
    if not meta_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_ai_fragments(case_id: str) -> List[Dict]:
    """加载 case 的 ai_fragments.json（如果存在）"""
    ai_path = Config.CASES_DIR / case_id / "ai_fragments.json"
    if not ai_path.exists():
        return []
    with open(ai_path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_fragments(fragments: List[Dict], ai_fragments: List[Dict]) -> List[Dict]:
    """合并文本 fragments 和视觉 ai_fragments"""
    merged = []

    # 文本 fragments
    for f in fragments:
        merged.append({
            **f,
            "source_layer": "text",
        })

    # 视觉 ai_fragments
    for af in ai_fragments:
        merged.append({
            **af,
            "source_layer": "vision",
        })

    return merged


def save_patterns(case_id: str, patterns: List[Dict]) -> Path:
    """保存 patterns"""
    patterns_path = Config.CASES_DIR / case_id / "patterns.json"
    with open(patterns_path, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    return patterns_path


def save_case_card(case_id: str, content: str) -> Path:
    """保存 case_card"""
    card_path = Config.CASES_DIR / case_id / "case_card.md"
    Path(card_path).write_text(content, encoding="utf-8")
    return card_path


def extract_patterns_for_case(case_id: str) -> Dict:
    """
    为 case 提取 patterns

    同时读取 fragments.json（文本）和 ai_fragments.json（视觉），
    合并后提取 patterns。

    Returns:
        {"success": bool, "message": str, "patterns_count": int}
    """
    # 检查 case 是否存在
    meta = load_meta(case_id)
    if meta is None:
        return {"success": False, "message": f"Case 不存在: {case_id}"}

    # 加载文本 fragments
    fragments = load_fragments(case_id)
    if fragments is None:
        return {"success": False, "message": f"Fragments 不存在，请先运行 compile-case"}

    # 加载视觉 ai_fragments（如果存在）
    ai_fragments = load_ai_fragments(case_id)

    # 合并
    all_fragments = merge_fragments(fragments, ai_fragments)

    # 提取 patterns（带 source_layer 追踪）
    patterns = extract_patterns_with_layer(case_id, all_fragments)

    # 保存 patterns.json
    patterns_path = save_patterns(case_id, patterns)

    # 生成 case_card.md
    card_content = generate_case_card(case_id, patterns, meta, fragments, ai_fragments)
    card_path = save_case_card(case_id, card_content)

    # 更新 job
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now = now_iso()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (job_id, case_id, stage, status, started_at, finished_at)
        VALUES (?, ?, 'patterns', 'success', ?, ?)
    """, (job_id, case_id, now, now))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Patterns 提取成功",
        "case_id": case_id,
        "patterns_count": len(patterns),
        "patterns_path": str(patterns_path),
        "card_path": str(card_path),
    }