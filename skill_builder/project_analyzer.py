"""
project_analyzer - Project-Level Analysis Engine

Analyzes entire case's patterns and strategies at project level:
- emotion_curve: 情绪曲线
- persuasion_flow: 说服流程
- narrative_arc: 叙事弧线
- visual_progression: 视觉递进
- information_density_curve: 信息密度曲线
- climax_design: 高潮设计
- emotional_release: 情绪释放
- strategic_sequence: 策略序列
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config
from .utils import now_iso


def load_case_for_project_analysis(case_id: str) -> Dict:
    """加载 case 的 patterns、fragments、strategies、meta"""
    case_dir = Config.CASES_DIR / case_id

    data = {
        "case_id": case_id,
        "patterns": [],
        "fragments": [],
        "strategies": [],
        "meta": None,
    }

    # patterns.json
    pp = case_dir / "patterns.json"
    if pp.exists():
        with open(pp, "r", encoding="utf-8") as f:
            data["patterns"] = json.load(f)

    # fragments.json
    fp = case_dir / "fragments.json"
    if fp.exists():
        with open(fp, "r", encoding="utf-8") as f:
            data["fragments"] = json.load(f)

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


def analyze_emotion_curve(patterns: List[Dict], strategies: List[Dict]) -> Dict:
    """
    分析情绪曲线
    基于 narrative_strategy 和 visual_strategy 的分布推断情绪节奏
    """
    # 提取策略类型分布
    strategy_types = [s.get("strategy_type", "") for s in strategies]

    # 情绪阶段推断
    emotion_phases = []

    # 开头：定位 + 受众
    if "positioning_strategy" in strategy_types and "audience_strategy" in strategy_types:
        emotion_phases.append({
            "phase": "开场定调",
            "emotion": "期待感",
            "position": "opening",
            "evidence": "定位策略 + 受众策略"
        })

    # 中段：叙事 + 视觉
    if "narrative_strategy" in strategy_types and "visual_strategy" in strategy_types:
        emotion_phases.append({
            "phase": "内容展开",
            "emotion": "沉浸感",
            "position": "middle",
            "evidence": "叙事策略 + 视觉策略"
        })

    # 高潮：转化
    if "conversion_strategy" in strategy_types:
        emotion_phases.append({
            "phase": "转化引爆",
            "emotion": "行动感",
            "position": "climax",
            "evidence": "转化策略"
        })

    # 收尾：执行
    if "execution_strategy" in strategy_types:
        emotion_phases.append({
            "phase": "落地执行",
            "emotion": "确定感",
            "position": "ending",
            "evidence": "执行策略"
        })

    # 情绪曲线评分
    curve_score = len(emotion_phases) / 4.0 if len(emotion_phases) <= 4 else 1.0

    return {
        "phases": emotion_phases,
        "curve_score": round(curve_score, 2),
        "has_emotion_progression": len(emotion_phases) >= 3,
        "climax_position": "middle" if any(p.get("position") == "climax" for p in emotion_phases) else "unknown"
    }


def analyze_persuasion_flow(strategies: List[Dict]) -> Dict:
    """
    分析说服流程
    基于策略类型序列推断说服逻辑
    """
    flow = []
    seen_types = set()

    # 标准说服流程：定位 → 受众 → 叙事 → 视觉 → 转化 → 执行
    sequence_map = {
        "positioning_strategy": 1,
        "audience_strategy": 2,
        "narrative_strategy": 3,
        "visual_strategy": 4,
        "conversion_strategy": 5,
        "execution_strategy": 6,
    }

    # 按顺序提取
    for s in strategies:
        stype = s.get("strategy_type", "")
        if stype and stype not in seen_types:
            flow.append({
                "step": len(flow) + 1,
                "strategy_type": stype,
                "name": s.get("name", stype),
                "description": s.get("description", "")[:80]
            })
            seen_types.add(stype)

    # 计算覆盖率
    expected_types = set(sequence_map.keys())
    actual_types = set(seen_types)
    coverage = len(actual_types & expected_types) / len(expected_types)

    # 计算流畅度（是否按顺序）
    sorted_types = sorted(seen_types, key=lambda x: sequence_map.get(x, 99))
    is_smooth = list(sorted_types) == [t for t in sequence_map.keys() if t in seen_types]

    return {
        "flow": flow,
        "coverage": round(coverage, 2),
        "is_smooth": is_smooth,
        "missing_types": list(expected_types - actual_types),
        "flow_length": len(flow)
    }


def analyze_narrative_arc(patterns: List[Dict], strategies: List[Dict]) -> Dict:
    """
    分析叙事弧线
    基于 content_structure pattern 和 narrative_strategy
    """
    # 查找 content_structure pattern
    cs_patterns = [p for p in patterns if p.get("pattern_type") == "content_structure"]
    narrative_strategies = [s for s in strategies if s.get("strategy_type") == "narrative_strategy"]

    arc_segments = []

    # 开场
    arc_segments.append({
        "segment": "开场",
        "function": "建立基调、吸引注意",
        "position": "opening"
    })

    # 展开
    if cs_patterns or narrative_strategies:
        arc_segments.append({
            "segment": "展开",
            "function": "传递信息、建立关系",
            "position": "middle"
        })

    # 高潮
    arc_segments.append({
        "segment": "高潮",
        "function": "强化记忆、推动决策",
        "position": "climax"
    })

    # 收尾
    arc_segments.append({
        "segment": "收尾",
        "function": "明确行动、留下印象",
        "position": "ending"
    })

    return {
        "arc_segments": arc_segments,
        "arc_completeness": len(arc_segments) / 4.0,
        "has_narrative_structure": len(cs_patterns) > 0,
        "narrative_depth_score": round(len(arc_segments) / 4.0, 2)
    }


def analyze_visual_progression(patterns: List[Dict], strategies: List[Dict]) -> Dict:
    """
    分析视觉递进
    基于 visual_direction patterns 和 visual_strategy
    """
    visual_patterns = [p for p in patterns if p.get("pattern_type") == "visual_direction"]
    visual_strategies = [s for s in strategies if s.get("strategy_type") == "visual_strategy"]

    progression = []

    # 视觉主题
    if visual_patterns:
        progression.append({
            "stage": "视觉基调",
            "description": f"基于 {len(visual_patterns)} 个视觉方向 pattern",
            "confidence": visual_patterns[0].get("confidence_score", 0.5) if visual_patterns else 0.5
        })

    if visual_strategies:
        progression.append({
            "stage": "视觉策略",
            "description": f"包含 {len(visual_strategies)} 个视觉策略",
            "confidence": visual_strategies[0].get("confidence_score", 0.5) if visual_strategies else 0.5
        })

    return {
        "progression": progression,
        "has_visual_progression": len(progression) >= 2,
        "visual_diversity": len(visual_patterns),
        "progression_score": round(len(progression) / 3.0, 2)
    }


def analyze_information_density(patterns: List[Dict], fragments: List[Dict]) -> Dict:
    """
    分析信息密度曲线
    基于 fragment 数量和 pattern 分布
    """
    total_fragments = len(fragments)

    # 按 fragment 类型分组
    fragment_types = {}
    for f in fragments:
        ftype = f.get("fragment_type", "unknown")
        fragment_types[ftype] = fragment_types.get(ftype, 0) + 1

    # 信息密度推断
    density_phases = []

    # 开场：通常信息密度较低
    density_phases.append({
        "phase": "开场",
        "density": "低",
        "reason": "建立基调，吸引注意"
    })

    # 中段：信息密度最高
    if total_fragments > 10:
        density_phases.append({
            "phase": "展开",
            "density": "高",
            "reason": f"共 {total_fragments} 个 fragments，信息量大"
        })
    elif total_fragments > 5:
        density_phases.append({
            "phase": "展开",
            "density": "中",
            "reason": f"共 {total_fragments} 个 fragments"
        })

    # 收尾：信息密度降低
    density_phases.append({
        "phase": "收尾",
        "density": "低",
        "reason": "明确行动，减少认知负担"
    })

    return {
        "density_phases": density_phases,
        "total_fragments": total_fragments,
        "fragment_types": fragment_types,
        "density_score": round(min(total_fragments / 20.0, 1.0), 2)
    }


def analyze_climax_design(strategies: List[Dict]) -> Dict:
    """
    分析高潮设计
    找转化策略和视觉策略的交汇点
    """
    conversion_strategies = [s for s in strategies if s.get("strategy_type") == "conversion_strategy"]
    visual_strategies = [s for s in strategies if s.get("strategy_type") == "visual_strategy"]

    climax_indicators = []

    if conversion_strategies:
        climax_indicators.append({
            "indicator": "转化策略",
            "description": "推动受众做出决定",
            "strength": len(conversion_strategies)
        })

    if visual_strategies:
        climax_indicators.append({
            "indicator": "视觉冲击",
            "description": "强化记忆点",
            "strength": len(visual_strategies)
        })

    # 高潮位置推断
    climax_position = "middle"
    if len(strategies) >= 5:
        climax_position = "middle-late"
    elif len(strategies) < 3:
        climax_position = "early"

    return {
        "climax_indicators": climax_indicators,
        "climax_position": climax_position,
        "has_clear_climax": len(climax_indicators) >= 1,
        "climax_strength": round(len(climax_indicators) / 2.0, 2)
    }


def analyze_emotional_release(strategies: List[Dict]) -> Dict:
    """
    分析情绪释放
    找到执行策略和叙事策略的收尾
    """
    execution_strategies = [s for s in strategies if s.get("strategy_type") == "execution_strategy"]
    narrative_strategies = [s for s in strategies if s.get("strategy_type") == "narrative_strategy"]

    release_mechanisms = []

    # 执行策略 = 行动释放
    if execution_strategies:
        release_mechanisms.append({
            "mechanism": "行动号召",
            "description": "明确的执行步骤，转化为实际行为",
            "type": "action"
        })

    # 叙事策略 = 情感释放
    if narrative_strategies:
        release_mechanisms.append({
            "mechanism": "情感收束",
            "description": "故事收尾，留下情感印象",
            "type": "emotion"
        })

    return {
        "release_mechanisms": release_mechanisms,
        "has_release": len(release_mechanisms) >= 1,
        "release_depth": round(len(release_mechanisms) / 2.0, 2)
    }


def analyze_strategic_sequence(strategies: List[Dict]) -> Dict:
    """
    分析策略序列
    按顺序排列所有策略类型
    """
    sequence_map = {
        "positioning_strategy": 1,
        "audience_strategy": 2,
        "narrative_strategy": 3,
        "visual_strategy": 4,
        "conversion_strategy": 5,
        "execution_strategy": 6,
    }

    type_to_name = {
        "positioning_strategy": "定位策略",
        "audience_strategy": "受众策略",
        "narrative_strategy": "叙事策略",
        "visual_strategy": "视觉策略",
        "conversion_strategy": "转化策略",
        "execution_strategy": "执行策略",
    }

    # 按优先级排序
    sorted_strategies = sorted(strategies, key=lambda s: sequence_map.get(s.get("strategy_type", ""), 99))

    sequence = []
    for i, s in enumerate(sorted_strategies):
        stype = s.get("strategy_type", "")
        sequence.append({
            "step": i + 1,
            "strategy_type": stype,
            "name": type_to_name.get(stype, stype),
            "confidence": s.get("confidence_score", 0.5)
        })

    # 计算序列完整性
    covered_types = set(s.get("strategy_type", "") for s in strategies)
    expected_types = set(sequence_map.keys())
    completeness = len(covered_types & expected_types) / len(expected_types)

    return {
        "sequence": sequence,
        "completeness": round(completeness, 2),
        "sequence_length": len(sequence),
        "is_complete": completeness >= 0.8
    }


def build_project_pattern(data: Dict) -> Dict:
    """
    构建完整的 ProjectPattern
    """
    patterns = data.get("patterns", [])
    fragments = data.get("fragments", [])
    strategies = data.get("strategies", [])
    meta = data.get("meta", {}) or {}
    case_id = data["case_id"]

    # 各维度分析
    emotion_curve = analyze_emotion_curve(patterns, strategies)
    persuasion_flow = analyze_persuasion_flow(strategies)
    narrative_arc = analyze_narrative_arc(patterns, strategies)
    visual_progression = analyze_visual_progression(patterns, strategies)
    information_density = analyze_information_density(patterns, fragments)
    climax_design = analyze_climax_design(strategies)
    emotional_release = analyze_emotional_release(strategies)
    strategic_sequence = analyze_strategic_sequence(strategies)

    # 综合评分
    scores = [
        emotion_curve.get("curve_score", 0),
        persuasion_flow.get("coverage", 0),
        narrative_arc.get("narrative_depth_score", 0),
        visual_progression.get("progression_score", 0),
        information_density.get("density_score", 0),
        climax_design.get("climax_strength", 0),
        emotional_release.get("release_depth", 0),
        strategic_sequence.get("completeness", 0),
    ]
    overall_score = round(sum(scores) / len(scores), 2) if scores else 0

    return {
        "project_pattern_id": f"pp-{uuid.uuid4().hex[:10]}",
        "case_id": case_id,
        "title": meta.get("title", "未知"),
        "dataset": meta.get("dataset", "unknown"),
        # 叙事维度
        "narrative_arc": narrative_arc,
        "emotion_curve": emotion_curve,
        "persuasion_flow": persuasion_flow,
        "visual_progression": visual_progression,
        # 信息维度
        "information_density_curve": information_density,
        "climax_design": climax_design,
        "emotional_release": emotional_release,
        "strategic_sequence": strategic_sequence,
        # 综合评分
        "overall_score": overall_score,
        "analyzed_at": now_iso()
    }


def save_project_patterns(case_id: str, project_pattern: Dict) -> Path:
    """保存 project_patterns.json"""
    patterns_dir = Config.CASES_DIR / case_id
    pp_path = patterns_dir / "project_patterns.json"

    with open(pp_path, "w", encoding="utf-8") as f:
        json.dump([project_pattern], f, ensure_ascii=False, indent=2)

    return pp_path


def build_project_analysis_md(project_pattern: Dict) -> str:
    """生成 project_analysis.md"""
    case_id = project_pattern.get("case_id", "unknown")
    title = project_pattern.get("title", "未知")

    lines = [
        f"# Project Analysis: {case_id}",
        "",
        f"**标题**: {title}",
        f"**评分**: {project_pattern.get('overall_score', 0)}/100",
        f"**分析时间**: {project_pattern.get('analyzed_at', '')}",
        "",
        "---",
        "",
    ]

    # 叙事弧线
    na = project_pattern.get("narrative_arc", {})
    lines.extend([
        "## 叙事弧线",
        "",
        f"完整度: {na.get('arc_completeness', 0):.0%}",
        f"有叙事结构: {'是' if na.get('has_narrative_structure') else '否'}",
        "",
    ])
    for seg in na.get("arc_segments", []):
        lines.append(f"- **{seg.get('segment')}** ({seg.get('position')}): {seg.get('function')}")
    lines.append("")

    # 情绪曲线
    ec = project_pattern.get("emotion_curve", {})
    lines.extend([
        "## 情绪曲线",
        "",
        f"曲线评分: {ec.get('curve_score', 0):.2f}",
        f"高潮位置: {ec.get('climax_position', 'unknown')}",
        "",
    ])
    for phase in ec.get("phases", []):
        lines.append(f"- **{phase.get('phase')}** ({phase.get('position')}): {phase.get('emotion')} - {phase.get('evidence')}")
    lines.append("")

    # 说服流程
    pf = project_pattern.get("persuasion_flow", {})
    lines.extend([
        "## 说服流程",
        "",
        f"覆盖率: {pf.get('coverage', 0):.0%}",
        f"流畅度: {'是' if pf.get('is_smooth') else '否'}",
        "",
    ])
    for step in pf.get("flow", []):
        lines.append(f"- **Step {step.get('step')}**: {step.get('name')} - {step.get('description')[:60]}")
    lines.append("")

    # 视觉递进
    vp = project_pattern.get("visual_progression", {})
    lines.extend([
        "## 视觉递进",
        "",
        f"视觉多样性: {vp.get('visual_diversity', 0)}",
        f"递进评分: {vp.get('progression_score', 0):.2f}",
        "",
    ])
    for stage in vp.get("progression", []):
        lines.append(f"- **{stage.get('stage')}**: {stage.get('description')}")
    lines.append("")

    # 信息密度
    idc = project_pattern.get("information_density_curve", {})
    lines.extend([
        "## 信息密度曲线",
        "",
        f"总 fragments: {idc.get('total_fragments', 0)}",
        f"密度评分: {idc.get('density_score', 0):.2f}",
        "",
    ])
    for phase in idc.get("density_phases", []):
        lines.append(f"- **{phase.get('phase')}**: {phase.get('density')} - {phase.get('reason')}")
    lines.append("")

    # 高潮设计
    cd = project_pattern.get("climax_design", {})
    lines.extend([
        "## 高潮设计",
        "",
        f"高潮位置: {cd.get('climax_position', 'unknown')}",
        f"高潮清晰度: {'是' if cd.get('has_clear_climax') else '否'}",
        f"强度评分: {cd.get('climax_strength', 0):.2f}",
        "",
    ])
    for ind in cd.get("climax_indicators", []):
        lines.append(f"- **{ind.get('indicator')}**: {ind.get('description')}")
    lines.append("")

    # 情绪释放
    er = project_pattern.get("emotional_release", {})
    lines.extend([
        "## 情绪释放",
        "",
        f"释放机制数: {len(er.get('release_mechanisms', []))}",
        "",
    ])
    for mech in er.get("release_mechanisms", []):
        lines.append(f"- **{mech.get('mechanism')}** ({mech.get('type')}): {mech.get('description')}")
    lines.append("")

    # 策略序列
    ss = project_pattern.get("strategic_sequence", {})
    lines.extend([
        "## 策略序列",
        "",
        f"完整度: {ss.get('completeness', 0):.0%}",
        f"序列长度: {ss.get('sequence_length', 0)}",
        "",
    ])
    for step in ss.get("sequence", []):
        lines.append(f"- **Step {step.get('step')}**: {step.get('name')} (置信度: {step.get('confidence', 0):.2f})")
    lines.append("")

    lines.extend([
        "---",
        "",
        f"*由 Proposal Skill Builder 自动生成*",
    ])

    return "\n".join(lines)


def save_project_analysis_md(case_id: str, content: str) -> Path:
    """保存 project_analysis.md"""
    analysis_path = Config.CASES_DIR / case_id / "project_analysis.md"
    Path(analysis_path).write_text(content, encoding="utf-8")
    return analysis_path


def analyze_project(case_id: str) -> Dict:
    """
    执行完整的项目级分析

    Returns:
        {
            "success": bool,
            "message": str,
            "project_pattern": Dict or None,
            "project_patterns_path": str or None,
            "project_analysis_md_path": str or None,
        }
    """
    # 加载数据
    data = load_case_for_project_analysis(case_id)

    if data["meta"] is None:
        return {"success": False, "message": f"Case 不存在: {case_id}"}

    if not data["patterns"] and not data["strategies"]:
        return {"success": False, "message": f"Case 没有 patterns 或 strategies，请先运行 extract-patterns 和 build-strategies"}

    # 构建 project pattern
    project_pattern = build_project_pattern(data)

    # 保存
    patterns_path = save_project_patterns(case_id, project_pattern)
    analysis_content = build_project_analysis_md(project_pattern)
    analysis_path = save_project_analysis_md(case_id, analysis_content)

    return {
        "success": True,
        "message": f"项目分析完成，评分: {project_pattern.get('overall_score', 0)}",
        "project_pattern": project_pattern,
        "project_patterns_path": str(patterns_path),
        "project_analysis_md_path": str(analysis_path),
    }