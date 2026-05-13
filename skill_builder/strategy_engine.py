"""
strategy_engine - Strategy 层聚合
"""

import json
import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config
from .db import get_connection
from .utils import now_iso


STRATEGY_TYPES = {
    "positioning_strategy": ["定位", "品牌", "差异化", "核心价值", "竞争优势", "战略"],
    "audience_strategy": ["用户", "客户", "受众", "人群", "会员", "消费者", "目标群体", "画像"],
    "narrative_strategy": ["叙事", "故事", "内容", "结构", "章节", "节奏", "弧线", "线索"],
    "visual_strategy": ["视觉", "风格", "画面", "色彩", "设计", "图形", "排版", "色调", "留白"],
    "execution_strategy": ["执行", "落地", "排期", "预算", "物料", "实施", "步骤", "时间节点"],
    "conversion_strategy": ["转化", "传播", "会员", "销售", "报名", "邀约", "注册", "购买", "成交"],
}


def load_case_for_strategy(case_id: str) -> Dict:
    """加载 case 的 fragments、ai_fragments、patterns"""
    case_dir = Config.CASES_DIR / case_id

    data = {
        "case_id": case_id,
        "fragments": [],
        "ai_fragments": [],
        "patterns": [],
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

    # source_meta.json
    mp = case_dir / "source_meta.json"
    if mp.exists():
        with open(mp, "r", encoding="utf-8") as f:
            data["meta"] = json.load(f)

    return data


def detect_strategy_type(text: str) -> List[str]:
    """检测文本中包含的策略类型"""
    detected = []
    text_lower = text.lower()

    for stype, keywords in STRATEGY_TYPES.items():
        for keyword in keywords:
            if keyword in text_lower:
                if stype not in detected:
                    detected.append(stype)
                break

    return detected


def collect_evidence(patterns: List[Dict], fragments: List[Dict],
                     ai_fragments: List[Dict], strategy_type: str) -> Dict:
    """收集特定策略类型的证据"""
    evidence_patterns = []
    evidence_fragments = []
    source_layers = set()

    # 从 patterns 中收集
    for p in patterns:
        ptype = p.get("pattern_type", "")
        source_sum = p.get("source_summary", "")

        # 类型映射
        type_to_strategy = {
            "strategy": "positioning_strategy",
            "content_structure": "narrative_strategy",
            "audience_insight": "audience_strategy",
            "visual_direction": "visual_strategy",
            "execution_method": "execution_strategy",
        }

        expected_strategy = type_to_strategy.get(ptype, "")

        if strategy_type == "conversion_strategy":
            # conversion_strategy 从所有 patterns 中检测关键词
            desc = p.get("description", "")
            if detect_strategy_type(desc):
                evidence_patterns.append(p["pattern_id"])
                source_layers.add("pattern")
        elif expected_strategy == strategy_type:
            evidence_patterns.append(p["pattern_id"])
            source_layers.add("pattern")
            if "视觉" in source_sum:
                source_layers.add("vision")
            if "文本" in source_sum:
                source_layers.add("text")

    # 从 ai_fragments 中收集证据
    for af in ai_fragments:
        raw_text = af.get("raw_text", "")
        if detect_strategy_type(raw_text):
            evidence_fragments.append(af["fragment_id"])
            source_layers.add("vision")

    # 从 text fragments 中收集（如果需要）
    if len(evidence_fragments) < 2:
        for f in fragments:
            raw_text = f.get("raw_text", "")
            if detect_strategy_type(raw_text):
                if f["fragment_id"] not in evidence_fragments:
                    evidence_fragments.append(f["fragment_id"])
                    source_layers.add("text")

    return {
        "evidence_patterns": evidence_patterns,
        "evidence_fragments": evidence_fragments,
        "source_layers": list(source_layers),
    }


def generate_strategy_id() -> str:
    """生成短 strategy ID"""
    return f"stg-{uuid.uuid4().hex[:10]}"


def build_strategy_name(strategy_type: str, index: int) -> str:
    """构建 strategy 名称"""
    type_names = {
        "positioning_strategy": "定位策略",
        "audience_strategy": "受众策略",
        "narrative_strategy": "叙事策略",
        "visual_strategy": "视觉策略",
        "execution_strategy": "执行策略",
        "conversion_strategy": "转化策略",
    }
    return f"{type_names.get(strategy_type, strategy_type)}_{index:02d}"


def build_description(evidence_patterns: List, patterns: List[Dict],
                       evidence_fragments: List, fragments: List[Dict]) -> str:
    """从证据构建 strategy 描述"""
    desc_parts = []

    # 从 pattern description 中提取
    for pid in evidence_patterns[:3]:
        for p in patterns:
            if p.get("pattern_id") == pid:
                d = p.get("description", "")
                if d:
                    desc_parts.append(d[:80])
                break

    return " | ".join(desc_parts[:3]) if desc_parts else ""


def build_reusable_principle(strategy_type: str, evidence_count: int) -> str:
    """构建可复用原则"""
    principles = {
        "positioning_strategy": "通过差异化定位建立品牌竞争优势，围绕核心价值构建说服逻辑。",
        "audience_strategy": "基于受众洞察设计沟通策略，满足目标群体真实需求。",
        "narrative_strategy": "通过故事结构引导受众情绪，建立叙事张力实现信息传递。",
        "visual_strategy": "视觉风格统一品牌调性，强化信息层次和记忆点。",
        "execution_strategy": "清晰的执行步骤和时间节点确保方案落地。",
        "conversion_strategy": "通过行为引导和激励机制实现目标转化。",
    }
    base = principles.get(strategy_type, "")

    if evidence_count < 3:
        base += "（当前证据有限，需补充更多案例验证）"

    return base


def build_applicable_scenarios(strategy_type: str) -> List[str]:
    """构建适用场景"""
    scenarios = {
        "positioning_strategy": [
            "品牌年度策略规划",
            "新品上市定位",
            "企业形象升级",
        ],
        "audience_strategy": [
            "目标人群深度洞察",
            "用户画像构建",
            "精准营销策略",
        ],
        "narrative_strategy": [
            "品牌故事构建",
            "活动叙事设计",
            "内容营销框架",
        ],
        "visual_strategy": [
            "视觉风格定义",
            "品牌视觉系统设计",
            "活动视觉呈现",
        ],
        "execution_strategy": [
            "大型活动策划",
            "项目执行排期",
            "物料清单规划",
        ],
        "conversion_strategy": [
            "会员招募与转化",
            "销售话术设计",
            "活动邀约策略",
        ],
    }
    return scenarios.get(strategy_type, [])


def build_risk_notes(strategy_type: str, evidence_patterns: List,
                     evidence_fragments: List) -> str:
    """构建风险说明"""
    notes = []

    if not evidence_patterns:
        notes.append("缺乏 Pattern 证据支持")

    if not evidence_fragments:
        notes.append("缺乏 Fragment 证据支持")

    if len(evidence_patterns) < 2:
        notes.append("Pattern 证据不足，可能影响策略稳定性")

    if len(evidence_fragments) < 2:
        notes.append("Fragment 证据不足，需要补充更多样本")

    # 类型特定风险
    if strategy_type == "visual_strategy":
        notes.append("视觉策略依赖图像分析，文本-only 数据可能不完整")

    if strategy_type == "conversion_strategy":
        notes.append("转化策略需要实际数据验证，无法仅靠策划文档推断")

    return "; ".join(notes) if notes else "无明显风险"


def extract_strategies(data: Dict) -> List[Dict]:
    """
    从 patterns、fragments、ai_fragments 中提取 StrategyUnits

    聚合规则：
    1. strategy 类型 patterns → positioning_strategy
    2. audience_insight patterns → audience_strategy
    3. visual_direction patterns + ai_fragments → visual_strategy
    4. content_structure patterns → narrative_strategy
    5. execution_method patterns → execution_strategy
    6. 包含转化相关关键词 → conversion_strategy（跨类型）
    """
    patterns = data.get("patterns", [])
    fragments = data.get("fragments", [])
    ai_fragments = data.get("ai_fragments", [])
    case_id = data["case_id"]

    strategies = []
    counters = {stype: 0 for stype in STRATEGY_TYPES.keys()}

    # 映射 pattern_type -> strategy_type
    pattern_to_strategy = {
        "strategy": "positioning_strategy",
        "content_structure": "narrative_strategy",
        "audience_insight": "audience_strategy",
        "visual_direction": "visual_strategy",
        "execution_method": "execution_strategy",
    }

    # 第一遍：基于 pattern_type 聚合
    for p in patterns:
        ptype = p.get("pattern_type", "")
        stype = pattern_to_strategy.get(ptype)

        if not stype:
            continue

        counters[stype] += 1
        strategy_id = generate_strategy_id()
        strategy_name = build_strategy_name(stype, counters[stype])

        # 收集证据
        evidence = collect_evidence(patterns, fragments, ai_fragments, stype)

        # 置信度：基于证据数量
        evidence_total = len(evidence["evidence_patterns"]) + len(evidence["evidence_fragments"])
        confidence = min(0.9, 0.5 + evidence_total * 0.1)

        strategy = {
            "strategy_id": strategy_id,
            "case_id": case_id,
            "name": strategy_name,
            "strategy_type": stype,
            "description": build_description(evidence["evidence_patterns"], patterns,
                                            evidence["evidence_fragments"], fragments),
            "evidence_patterns": evidence["evidence_patterns"],
            "evidence_fragments": evidence["evidence_fragments"],
            "source_layers": evidence["source_layers"],
            "reusable_principle": build_reusable_principle(stype, evidence_total),
            "applicable_scenarios": build_applicable_scenarios(stype),
            "risk_notes": build_risk_notes(stype, evidence["evidence_patterns"],
                                          evidence["evidence_fragments"]),
            "confidence_score": round(confidence, 2),
        }

        strategies.append(strategy)

    # 第二遍：检测 conversion_strategy（跨类型关键词检测）
    conversion_evidence = collect_evidence(patterns, fragments, ai_fragments, "conversion_strategy")
    if conversion_evidence["evidence_patterns"] or conversion_evidence["evidence_fragments"]:
        counters["conversion_strategy"] += 1
        strategy_id = generate_strategy_id()
        strategy_name = build_strategy_name("conversion_strategy", counters["conversion_strategy"])

        evidence_total = (len(conversion_evidence["evidence_patterns"]) +
                         len(conversion_evidence["evidence_fragments"]))
        confidence = min(0.8, 0.4 + evidence_total * 0.1)

        strategy = {
            "strategy_id": strategy_id,
            "case_id": case_id,
            "name": strategy_name,
            "strategy_type": "conversion_strategy",
            "description": "通过行为引导和激励机制实现目标转化的策略",
            "evidence_patterns": conversion_evidence["evidence_patterns"],
            "evidence_fragments": conversion_evidence["evidence_fragments"],
            "source_layers": conversion_evidence["source_layers"],
            "reusable_principle": "通过明确的转化路径设计和激励机制，实现预期行为改变。",
            "applicable_scenarios": ["会员招募", "销售转化", "活动邀约", "注册引导"],
            "risk_notes": build_risk_notes("conversion_strategy",
                                         conversion_evidence["evidence_patterns"],
                                         conversion_evidence["evidence_fragments"]),
            "confidence_score": round(confidence, 2),
        }

        strategies.append(strategy)

    return strategies


def build_strategy_dna_md(data: Dict, strategies: List[Dict]) -> str:
    """生成 strategy_dna.md"""
    meta = data.get("meta", {}) or {}
    patterns = data.get("patterns", [])
    fragments = data.get("fragments", [])
    ai_fragments = data.get("ai_fragments", [])
    case_id = data["case_id"]

    lines = [
        f"# Strategy DNA: {case_id}",
        "",
        f"**案例标题**: {meta.get('title', '未知')}",
        f"**数据集**: {meta.get('dataset', 'prod')}",
        f"**生成时间**: {now_iso()}",
        "",
        "---",
        "",
    ]

    # 策略总览
    type_to_name = {
        "positioning_strategy": "定位策略",
        "audience_strategy": "受众策略",
        "narrative_strategy": "叙事策略",
        "visual_strategy": "视觉策略",
        "execution_strategy": "执行策略",
        "conversion_strategy": "转化策略",
    }

    lines.extend([
        "## 策略总览",
        "",
        f"共提取 **{len(strategies)}** 个 StrategyUnits：",
        "",
    ])

    for s in strategies:
        stype_name = type_to_name.get(s["strategy_type"], s["strategy_type"])
        lines.append(f"- **{s['name']}** ({stype_name}): {s['description'][:60]}...")

    lines.append("")

    # 分类型详细说明
    for stype, stype_name in type_to_name.items():
        type_strategies = [s for s in strategies if s["strategy_type"] == stype]
        if not type_strategies:
            continue

        lines.append(f"## {stype_name}")
        lines.append("")

        for s in type_strategies:
            lines.append(f"### {s['name']}")
            lines.append(f"**描述**: {s['description'][:120]}")
            lines.append(f"**置信度**: {s['confidence_score']}")
            lines.append(f"**可复用原则**: {s['reusable_principle']}")
            lines.append(f"**风险**: {s['risk_notes']}")

            if s["evidence_patterns"]:
                lines.append(f"**证据 Patterns**: {len(s['evidence_patterns'])} 个")
            if s["evidence_fragments"]:
                lines.append(f"**证据 Fragments**: {len(s['evidence_fragments'])} 个")
            if s["source_layers"]:
                lines.append(f"**来源层次**: {', '.join(s['source_layers'])}")

            lines.append("")
        lines.append("")

    # 可复用方法论
    lines.extend([
        "## 可复用方法论",
        "",
    ])

    for s in strategies:
        stype_name = type_to_name.get(s["strategy_type"], s["strategy_type"])
        lines.append(f"- **{s['name']}**: {s['reusable_principle']}")

    lines.append("")

    # 适用场景
    all_scenarios = []
    for s in strategies:
        all_scenarios.extend(s.get("applicable_scenarios", []))
    all_scenarios = list(dict.fromkeys(all_scenarios))[:10]

    lines.extend([
        "## 适用场景",
        "",
    ])
    for sc in all_scenarios:
        lines.append(f"- {sc}")
    lines.append("")

    # 风险与缺口
    lines.extend([
        "## 风险与缺口",
        "",
    ])

    low_confidence = [s for s in strategies if s["confidence_score"] < 0.6]
    if low_confidence:
        lines.append(f"⚠️ {len(low_confidence)} 个策略置信度较低，需要补充证据")

    if not ai_fragments:
        lines.append("⚠️ 缺乏视觉片段，视觉策略可信度受限")

    if not all_scenarios:
        lines.append("⚠️ 适用场景过少，需要更多案例验证")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*由 Proposal Skill Builder 自动生成*")

    return "\n".join(lines)


def save_strategies(case_id: str, strategies: List[Dict]) -> Path:
    """保存 strategies.json"""
    strategies_path = Config.CASES_DIR / case_id / "strategies.json"
    with open(strategies_path, "w", encoding="utf-8") as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)
    return strategies_path


def save_strategy_dna(case_id: str, content: str) -> Path:
    """保存 strategy_dna.md"""
    dna_path = Config.CASES_DIR / case_id / "strategy_dna.md"
    Path(dna_path).write_text(content, encoding="utf-8")
    return dna_path


def build_strategies_for_case(case_id: str) -> Dict:
    """
    为 case 构建 StrategyUnits 和 strategy_dna.md

    Returns:
        {
            "success": bool,
            "message": str,
            "strategies_count": int,
            "strategies_path": str,
            "dna_path": str,
        }
    """
    # 加载数据
    data = load_case_for_strategy(case_id)

    if data["meta"] is None:
        return {"success": False, "message": f"Case 不存在: {case_id}"}

    if not data["patterns"] and not data["fragments"]:
        return {"success": False, "message": f"Case 没有 patterns 或 fragments，请先运行 extract-patterns"}

    # 提取 strategies
    strategies = extract_strategies(data)

    if not strategies:
        return {"success": False, "message": "未提取到任何 StrategyUnits"}

    # 保存
    strategies_path = save_strategies(case_id, strategies)

    # 生成 strategy_dna.md
    dna_content = build_strategy_dna_md(data, strategies)
    dna_path = save_strategy_dna(case_id, dna_content)

    # 记录 job
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now = now_iso()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (job_id, case_id, stage, status, started_at, finished_at)
        VALUES (?, ?, 'strategies', 'success', ?, ?)
    """, (job_id, case_id, now, now))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"提取 {len(strategies)} 个 StrategyUnits",
        "strategies_count": len(strategies),
        "strategies_path": str(strategies_path),
        "dna_path": str(dna_path),
    }