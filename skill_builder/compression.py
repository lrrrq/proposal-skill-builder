"""
compression - Fragment 压缩引擎
"""

import json
import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config
from .utils import now_iso


# 短文本阈值（字符数）
SHORT_TEXT_THRESHOLD = 20

# 低信息密度关键词
LOW_INFO_KEYWORDS = [
    "无", "空", "暂无", "未提供", "待定", "未知",
    "none", "null", "n/a", "tbd",
]


def load_case_data(case_id: str) -> Dict:
    """加载 case 的所有 fragment 相关数据"""
    case_dir = Config.CASES_DIR / case_id

    data = {
        "case_id": case_id,
        "fragments": [],
        "ai_fragments": [],
        "patterns": [],
        "strategies": [],
        "meta": None,
    }

    # fragments.json
    fp = case_dir / "fragments.json"
    if fp.exists():
        with open(fp, "r", encoding="utf-8") as f:
            data["fragments"] = json.load(f)

    # ai_fragments.json
    ap = case_dir / "ai_fragments.json"
    if ap.exists():
        with open(ap, "r", encoding="utf-8") as f:
            data["ai_fragments"] = json.load(f)

    # patterns.json
    pp = case_dir / "patterns.json"
    if pp.exists():
        with open(pp, "r", encoding="utf-8") as f:
            data["patterns"] = json.load(f)

    # strategies.json
    sp = case_dir / "strategies.json"
    if sp.exists():
        with open(sp, "r", encoding="utf-8") as f:
            data["strategies"] = json.load(f)

    # source_meta.json
    mp = case_dir / "source_meta.json"
    if mp.exists():
        with open(mp, "r", encoding="utf-8") as f:
            data["meta"] = json.load(f)

    return data


def is_low_information(text: str) -> bool:
    """判断文本是否低信息密度"""
    if not text or len(text.strip()) < SHORT_TEXT_THRESHOLD:
        return True

    text_lower = text.lower()
    for kw in LOW_INFO_KEYWORDS:
        if kw in text_lower:
            return True

    return False


def is_duplicate(fragment: Dict, all_fragments: List[Dict]) -> bool:
    """判断 fragment 是否为重复"""
    raw_text = fragment.get("raw_text", "").strip()
    if not raw_text or len(raw_text) < 10:
        return False

    # 完全相同
    for other in all_fragments:
        if other.get("fragment_id") == fragment.get("fragment_id"):
            continue
        other_text = other.get("raw_text", "").strip()
        if raw_text == other_text and len(raw_text) > 20:
            return True

    return False


def extract_keywords_from_text(text: str) -> List[str]:
    """从文本中提取关键词（简单实现）"""
    if not text:
        return []

    # 移除标点，提取中英文词
    chinese_words = re.findall(r'[一-鿿]+', text)
    english_words = re.findall(r'[a-zA-Z]+', text)

    # 取出现次数多的词
    all_words = chinese_words + [w for w in english_words if len(w) > 2]
    word_count = {}
    for word in all_words:
        word_count[word] = word_count.get(word, 0) + 1

    # 按出现次数排序，取前 5
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:5]]


def merge_fragment(fragments_to_merge: List[Dict], case_id: str) -> Dict:
    """
    合并多个相似的 fragments
    """
    if len(fragments_to_merge) == 1:
        f = fragments_to_merge[0]
        return {
            "compressed_id": f"cmp-{uuid.uuid4().hex[:10]}",
            "case_id": case_id,
            "source_fragment_ids": [f.get("fragment_id", "")],
            "source_layers": [f.get("source_layer", "text")],
            "merged_text": f.get("raw_text", ""),
            "summary": f.get("summary", "") or f.get("raw_text", "")[:100],
            "keywords": f.get("keywords", []),
            "related_patterns": [],
            "related_strategies": [],
            "quality_flags": f.get("quality_flags", ["normal"]),
            "confidence_score": f.get("confidence", 0.5),
        }

    # 多个 fragment 合并
    primary = fragments_to_merge[0]
    all_texts = [f.get("raw_text", "") for f in fragments_to_merge]
    all_keywords = []
    for f in fragments_to_merge:
        all_keywords.extend(f.get("keywords", []))

    merged_text = " || ".join(filter(None, all_texts))
    summary = primary.get("summary", "") or all_texts[0][:100] if all_texts else ""

    return {
        "compressed_id": f"cmp-{uuid.uuid4().hex[:10]}",
        "case_id": case_id,
        "source_fragment_ids": [f.get("fragment_id", "") for f in fragments_to_merge],
        "source_layers": list(set(f.get("source_layer", "text") for f in fragments_to_merge)),
        "merged_text": merged_text,
        "summary": summary,
        "keywords": list(dict.fromkeys(all_keywords))[:10],
        "related_patterns": [],
        "related_strategies": [],
        "quality_flags": ["merged"],
        "confidence_score": min(0.9, 0.4 + len(fragments_to_merge) * 0.1),
    }


def compress_fragments(data: Dict) -> List[Dict]:
    """
    压缩 fragments

    规则：
    1. 标记过短 fragment (too_short)
    2. 标记重复 fragment (duplicate)
    3. 标记低信息密度 fragment (low_information)
    4. 合并相似的 fragments
    5. 保留原始 fragment_id
    """
    fragments = data.get("fragments", [])
    ai_fragments = data.get("ai_fragments", [])
    case_id = data["case_id"]

    # 合并所有 fragments（带 source_layer）
    all_frags = []
    for f in fragments:
        all_frags.append({**f, "source_layer": "text"})
    for af in ai_fragments:
        all_frags.append({**af, "source_layer": "vision"})

    if not all_frags:
        return []

    compressed = []
    processed_ids = set()

    # 第一遍：处理重复和低信息
    for frag in all_frags:
        frag_id = frag.get("fragment_id", "")
        if frag_id in processed_ids:
            continue

        raw_text = frag.get("raw_text", "")
        quality_flags = []
        notes = []

        # 检查是否过短
        if len(raw_text) < SHORT_TEXT_THRESHOLD:
            quality_flags.append("too_short")
            notes.append("文本过短")

        # 检查是否低信息
        if is_low_information(raw_text):
            quality_flags.append("low_information")
            notes.append("低信息密度")

        # 检查是否重复
        if is_duplicate(frag, all_frags):
            quality_flags.append("duplicate")
            notes.append("重复内容")

        # 确定 source_layer
        if frag.get("fragment_id", "").startswith("ai-"):
            if "vision_only" not in quality_flags:
                quality_flags.append("vision_only")
        else:
            if "text_only" not in quality_flags:
                quality_flags.append("text_only")

        # 如果有多个 quality_flags，检查是否混合来源
        if frag.get("fragment_id", "").startswith("ai-"):
            quality_flags.append("vision_only")
        else:
            quality_flags.append("text_only")

        # 构建 compressed fragment
        keywords = frag.get("keywords", [])
        if not keywords and raw_text:
            keywords = extract_keywords_from_text(raw_text)

        cfrag = {
            "compressed_id": f"cmp-{uuid.uuid4().hex[:10]}",
            "case_id": case_id,
            "source_fragment_ids": [frag_id],
            "source_layers": [frag.get("source_layer", "text")],
            "merged_text": raw_text,
            "summary": frag.get("summary", "") or raw_text[:100],
            "keywords": keywords,
            "related_patterns": [],
            "related_strategies": [],
            "quality_flags": quality_flags if quality_flags else ["normal"],
            "confidence_score": frag.get("confidence", frag.get("confidence_score", 0.5)),
        }

        compressed.append(cfrag)
        processed_ids.add(frag_id)

    # 第二遍：建立关联（patterns 和 strategies）
    patterns = data.get("patterns", [])
    strategies = data.get("strategies", [])

    pattern_ids = set(p.get("pattern_id", "") for p in patterns)
    strategy_ids = set(s.get("strategy_id", "") for s in strategies)

    for cfrag in compressed:
        src_ids = cfrag.get("source_fragment_ids", [])

        # 关联 patterns
        for p in patterns:
            p_frag_ids = []
            for src in p.get("source_fragment_ids", []):
                if isinstance(src, dict):
                    p_frag_ids.append(src.get("fragment_id", ""))
                else:
                    p_frag_ids.append(src)

            if any(fid in p_frag_ids for fid in src_ids):
                cfrag["related_patterns"].append(p.get("pattern_id", ""))

        # 关联 strategies
        for s in strategies:
            ev_frag_ids = s.get("evidence_fragments", [])
            if any(fid in ev_frag_ids for fid in src_ids):
                cfrag["related_strategies"].append(s.get("strategy_id", ""))

        # 去重
        cfrag["related_patterns"] = list(dict.fromkeys(cfrag["related_patterns"]))
        cfrag["related_strategies"] = list(dict.fromkeys(cfrag["related_strategies"]))

    return compressed


def generate_compression_report(
    case_id: str,
    original_fragments_count: int,
    original_vision_count: int,
    compressed_count: int,
    duplicate_count: int,
    low_info_count: int,
    meta: Dict = None
) -> str:
    """生成压缩报告"""

    retention_rate = (compressed_count / original_fragments_count * 100) if original_fragments_count > 0 else 0

    lines = [
        f"# Fragment Compression Report: {case_id}",
        "",
        f"**生成时间**: {now_iso()}",
        "",
        "---",
        "",
        "## 案例信息",
        "",
    ]

    if meta:
        lines.extend([
            f"- **标题**: {meta.get('title', '未知')}",
            f"- **来源文件**: {meta.get('original_filename', '未知')}",
            f"- **数据集**: {meta.get('dataset', 'prod')}",
            "",
        ])

    lines.extend([
        "## 压缩统计",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 原始文本 Fragments | {original_fragments_count} |",
        f"| 原始视觉 Fragments | {original_vision_count} |",
        f"| 压缩后 Fragments | {compressed_count} |",
        f"| 重复项 | {duplicate_count} |",
        f"| 低信息密度 | {low_info_count} |",
        f"| 保留率 | {retention_rate:.1f}% |",
        "",
    ])

    # 质量分布
    lines.extend([
        "## 质量标志分布",
        "",
        "| 质量标志 | 说明 |",
        "|------|------|",
        "| too_short | 文本过短（<20字符） |",
        "| duplicate | 重复内容 |",
        "| low_information | 低信息密度 |",
        "| text_only | 纯文本来源 |",
        "| vision_only | 纯视觉来源 |",
        "| merged | 多个 fragment 合并 |",
        "| normal | 正常质量 |",
        "",
    ])

    # 主要风险
    lines.extend([
        "## 主要风险",
        "",
    ])

    risks = []
    if duplicate_count > original_fragments_count * 0.3:
        risks.append(f"- ⚠️ 重复率过高（{duplicate_count}个），可能影响 Pattern 质量")
    if low_info_count > original_fragments_count * 0.3:
        risks.append(f"- ⚠️ 低信息密度片段过多（{low_info_count}个），建议补充更多案例")
    if retention_rate < 50:
        risks.append(f"- ⚠️ 保留率偏低（{retention_rate:.1f}%），可能过度压缩")

    if risks:
        lines.extend(risks)
    else:
        lines.append("- 无明显风险")
    lines.append("")

    # 下一步建议
    lines.extend([
        "## 下一步建议",
        "",
        "1. 如果压缩后 Fragments 数量仍然过多，可提高合并阈值",
        "2. 如果保留率过低，建议检查 fragment 提取逻辑",
        "3. 重复率过高时，可考虑在 extract-patterns 阶段去重",
        "4. 确认压缩结果后，可用于 compose-skill 生成更高质量的 Skill",
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    return "\n".join(lines)


def save_compressed_fragments(case_id: str, compressed: List[Dict]) -> Path:
    """保存压缩后的 fragments"""
    path = Config.CASES_DIR / case_id / "compressed_fragments.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(compressed, f, ensure_ascii=False, indent=2)
    return path


def save_compression_report(case_id: str, content: str) -> Path:
    """保存压缩报告"""
    path = Config.CASES_DIR / case_id / "compression_report.md"
    Path(path).write_text(content, encoding="utf-8")
    return path


def compress_fragments_for_case(case_id: str) -> Dict:
    """
    为 case 执行 Fragment 压缩

    Returns:
        {
            "success": bool,
            "message": str,
            "original_count": int,
            "compressed_count": int,
            "compressed_path": str,
            "report_path": str,
        }
    """
    # 加载数据
    data = load_case_data(case_id)

    if data["meta"] is None:
        return {"success": False, "message": f"Case 不存在: {case_id}"}

    original_text = len(data["fragments"])
    original_vision = len(data["ai_fragments"])
    original_total = original_text + original_vision

    if original_total == 0:
        return {"success": False, "message": f"Case 没有 Fragments，请先运行 compile-case"}

    # 执行压缩
    compressed = compress_fragments(data)

    # 统计
    duplicate_count = sum(1 for c in compressed if "duplicate" in c.get("quality_flags", []))
    low_info_count = sum(1 for c in compressed if "low_information" in c.get("quality_flags", []))
    too_short_count = sum(1 for c in compressed if "too_short" in c.get("quality_flags", []))

    # 保存
    compressed_path = save_compressed_fragments(case_id, compressed)

    # 生成报告
    report_content = generate_compression_report(
        case_id,
        original_text,
        original_vision,
        len(compressed),
        duplicate_count,
        low_info_count + too_short_count,
        data["meta"]
    )
    report_path = save_compression_report(case_id, report_content)

    return {
        "success": True,
        "message": f"压缩完成",
        "original_count": original_total,
        "compressed_count": len(compressed),
        "duplicate_count": duplicate_count,
        "low_info_count": low_info_count + too_short_count,
        "compressed_path": str(compressed_path),
        "report_path": str(report_path),
    }