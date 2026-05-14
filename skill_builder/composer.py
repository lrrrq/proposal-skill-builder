"""
composer - Skill 合成
"""

import json
import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config
from .db import get_connection
from .utils import now_iso


def load_case_data(case_id: str) -> Dict:
    """加载 case 所有相关数据"""
    case_dir = Config.CASES_DIR / case_id

    data = {
        "case_id": case_id,
        "meta": None,
        "patterns": [],
        "fragments": [],
        "ai_fragments": [],
        "strategies": [],
        "compressed": None,  # 压缩后的 fragments
    }

    # source_meta.json
    meta_path = case_dir / "source_meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            data["meta"] = json.load(f)

    # patterns.json
    patterns_path = case_dir / "patterns.json"
    if patterns_path.exists():
        with open(patterns_path, "r", encoding="utf-8") as f:
            data["patterns"] = json.load(f)

    # fragments.json
    fragments_path = case_dir / "fragments.json"
    if fragments_path.exists():
        with open(fragments_path, "r", encoding="utf-8") as f:
            data["fragments"] = json.load(f)

    # ai_fragments.json
    ai_path = case_dir / "ai_fragments.json"
    if ai_path.exists():
        with open(ai_path, "r", encoding="utf-8") as f:
            data["ai_fragments"] = json.load(f)

    # strategies.json (如果存在)
    strategies_path = case_dir / "strategies.json"
    if strategies_path.exists():
        with open(strategies_path, "r", encoding="utf-8") as f:
            data["strategies"] = json.load(f)

    # compressed_fragments.json (如果存在 - 压缩后的数据)
    compressed_path = case_dir / "compressed_fragments.json"
    if compressed_path.exists():
        with open(compressed_path, "r", encoding="utf-8") as f:
            data["compressed"] = json.load(f)

    return data


def calculate_quality_level(patterns: List[Dict], fragments: List[Dict], ai_fragments: List[Dict]) -> str:
    """计算质量等级"""
    pattern_count = len(patterns)
    text_count = len(fragments)
    vision_count = len(ai_fragments)

    # Gold: patterns >= 5, text >= 20, vision >= 3
    if pattern_count >= 5 and text_count >= 20 and vision_count >= 3:
        return "gold"

    # Silver: patterns >= 5, with both text and vision fragments
    if pattern_count >= 5 and text_count > 0 and vision_count > 0:
        return "silver"

    # Bronze: patterns >= 3
    if pattern_count >= 3:
        return "bronze"

    return "bronze"


def build_allowed_tasks(patterns: List[Dict]) -> List[str]:
    """从 patterns 推断 allowed_tasks"""
    tasks = []
    pattern_types = set(p.get("pattern_type", "") for p in patterns)

    type_to_tasks = {
        "strategy": ["策略规划", "品牌定位", "差异化分析"],
        "content_structure": ["内容策划", "结构设计", "叙事框架"],
        "visual_direction": ["视觉设计", "风格定义", "画面构思"],
        "audience_insight": ["受众分析", "用户洞察", "需求理解"],
        "execution_method": ["执行规划", "落地排期", "物料设计"],
    }

    for ptype, task_list in type_to_tasks.items():
        if ptype in pattern_types:
            tasks.extend(task_list)

    return list(dict.fromkeys(tasks))[:6]


def build_visual_strategy(ai_fragments: List[Dict], patterns: List[Dict]) -> str:
    """从视觉 fragments 和 patterns 构建视觉策略"""
    if len(ai_fragments) < 3:
        return (
            "当前视觉样本较少，视觉策略仅供初步参考。\n"
            "如需精确视觉策略，建议补充更多视觉案例。"
        )

    # 收集视觉描述中的关键词
    keywords = []
    for af in ai_fragments:
        keywords.extend(af.get("keywords", []))

    # 收集视觉相关 patterns
    visual_patterns = [p for p in patterns if p.get("pattern_type") == "visual_direction"]

    lines = ["## 视觉策略", "",]

    if visual_patterns:
        lines.append("**视觉方向 Pattern**:")
        for p in visual_patterns[:2]:
            lines.append(f"- {p.get('description', '')[:100]}")
        lines.append("")

    if keywords:
        unique_kw = list(dict.fromkeys(k for k in keywords if len(k) < 20))[:10]
        lines.append(f"**视觉关键词**: {', '.join(unique_kw)}")
        lines.append("")

    return "\n".join(lines)


def build_skill_content(data: Dict, skill_id: str) -> Dict:
    """构建 Skill 内容（SKILL.md, skill.json, examples.md）"""

    meta = data.get("meta", {}) or {}
    patterns = data.get("patterns", [])
    fragments = data.get("fragments", [])
    ai_fragments = data.get("ai_fragments", [])
    case_id = data["case_id"]

    # 计算质量等级
    quality_level = calculate_quality_level(patterns, fragments, ai_fragments)

    # dataset
    case_dataset = meta.get("dataset", "prod")

    # allowed_tasks
    allowed_tasks = build_allowed_tasks(patterns)

    # Skill ID display name
    display_name = skill_id.replace("-", " ").replace("_", " ").title()

    # source_cases
    source_cases = [case_id]

    # source_patterns
    source_patterns = [p["pattern_id"] for p in patterns]

    # 统计
    text_count = len(fragments)
    vision_count = len(ai_fragments)

    now = now_iso()

    # skill.json
    skill_json = {
        "skill_id": skill_id,
        "display_name": display_name,
        "description": f"从案例 {case_id} 提炼的能力，包含 {len(patterns)} 个 Patterns（{text_count} 文本片段 + {vision_count} 视觉片段）",
        "status": "draft",
        "dataset": case_dataset,
        "quality_level": quality_level,
        "callable": False,
        "source_cases": source_cases,
        "source_patterns": source_patterns,
        "source_fragments_count": text_count,
        "source_ai_fragments_count": vision_count,
        "source_strategies": [s["strategy_id"] for s in data.get("strategies", [])],
        "allowed_tasks": allowed_tasks,
        "created_at": now,
        "updated_at": now,
        "version": "1.0",
        "output_template": {
            "version_type": "both_internal_and_client",
            "internal_fields": ["预算细节", "供应商信息", "风险详情"],
            "client_fields": ["策略框架", "执行概要", "视觉效果"],
            "visual_references": [
                {"type": "cover", "count": 1, "description": "封面视觉参考"},
                {"type": "style_guide", "count": 3, "description": "风格示例图"},
                {"type": "layout_sample", "count": 2, "description": "版式示例图"}
            ],
            "sections": [
                {"name": "项目判断", "min_words": 100, "max_words": 200},
                {"name": "目标人群", "min_words": 150, "max_words": 300},
                {"name": "内容结构", "min_words": 200, "max_words": 500},
                {"name": "视觉方向", "min_words": 100, "max_words": 250},
                {"name": "执行路径", "min_words": 150, "max_words": 400}
            ]
        },
    }

    # SKILL.md
    skill_md = build_skill_md(data, skill_id, display_name, quality_level, case_dataset)

    # examples.md
    examples_md = build_examples_md(data, skill_id)

    return {
        "skill_json": skill_json,
        "skill_md": skill_md,
        "examples_md": examples_md,
    }


def build_skill_md(data: Dict, skill_id: str, display_name: str, quality_level: str, dataset: str) -> str:
    """构建 SKILL.md 内容"""
    meta = data.get("meta", {}) or {}
    patterns = data.get("patterns", [])
    fragments = data.get("fragments", [])
    ai_fragments = data.get("ai_fragments", [])
    case_id = data["case_id"]

    lines = [
        f"# {display_name}",
        "",
    ]

    # 适用场景
    lines.extend([
        "## 适用场景",
        "### 本章节核心：场景匹配，一句话概括",
        ">",
        "- 奢侈品牌营销活动策划",
        "- 高端酒店/文旅项目提案",
        "- 品牌发布会/年会创意设计",
        "",
    ])

    # 输入要求
    lines.extend([
        "## 输入要求",
        "### 本章节核心：信息输入，一句话概括",
        ">",
        "- 客户品牌背景",
        "- 活动/项目基本信息",
        "- 目标受众描述",
        "- 预算范围（如有）",
        "",
    ])

    # 核心判断逻辑
    strategy_patterns = [p for p in patterns if p.get("pattern_type") == "strategy"]
    if strategy_patterns:
        lines.extend([
            "## 核心判断逻辑",
            "### 本章节核心：策略判断，一句话概括",
            ">",
        ])
        for p in strategy_patterns[:2]:
            desc = p.get("description", "")
            if desc:
                lines.append(f"▶ {desc[:120]}")
        lines.append("")

    # 处理流程
    lines.extend([
        "## 处理流程",
        "### 本章节核心：步骤执行，一句话概括",
        ">",
        "1. **品牌定位分析** - 理解客户品牌核心价值与差异化",
        "2. **受众洞察** - 分析目标用户心理与需求",
        "3. **内容结构设计** - 构建叙事框架与信息层次",
        "4. **视觉方向定义** - 确定视觉风格与调性",
        "5. **执行规划** - 输出物料清单与时间节点",
        "",
    ])

    # 输出格式
    lines.extend([
        "## 输出格式",
        "### 本章节核心：交付物结构，一句话概括",
        ">",
        "▶ 策略框架：Brand Position / Target Audience / Key Message",
        "▶ 内容结构：Content Outline / Story Arc",
        "▶ 视觉方向：Visual Direction / Style Guide",
        "▶ 执行方案：Timeline / Deliverables / Budget",
        "",
    ])

    # 版本类型 (P0-2)
    lines.extend([
        "### 版本类型",
        "> 适用版本：内部版 + 客户版",
        "",
    ])

    # 可复用策略
    lines.extend([
        "## 可复用策略",
        "### 本章节核心：模式复用，一句话概括",
        ">",
    ])
    for p in patterns[:5]:
        lines.append(f"▶ **{p['name']}** (*{p['pattern_type']}*): {p.get('description', '')[:80]}...")
    lines.append("")

    # 视觉方向
    lines.extend([
        "## 视觉方向",
        "",
        "### 色调关键词",
        "> 主色系：**奢华金**、**深空灰**",
        "> 辅色系：**象牙白**、**香槟银**",
        "> 禁忌色：荧光色、高饱和度色",
        "",
        "### 风格描述",
        "> **高端留白**、**质感细节**、**品牌调性统一**",
        "",
    ])

    # 视觉策略
    vision_lines = build_visual_strategy_section(patterns, ai_fragments)
    lines.append(vision_lines)
    lines.append("")

    # 视觉参考图
    lines.extend([
        "## 视觉参考图",
        "",
        "| 类型 | 数量 | 说明 |",
        "|------|------|------|",
        "| 封面视觉 | 1张 | [占位符] |",
        "| 风格示例 | 3张 | [占位符] |",
        "| 版式示例 | 2张 | [占位符] |",
        "",
        "### 色彩规范",
        "| 类型 | 色值 | 说明 |",
        "|------|------|------|",
        "| 主色 | #C9A962 | 奢华金 |",
        "| 辅色 | #1A1A2E | 深空灰 |",
        "| 点缀 | #F5F5F5 | 象牙白 |",
        "",
    ])

    # 策略 DNA（如果有 strategies）
    strategies = data.get("strategies", [])
    if strategies:
        lines.extend([
            "## 策略 DNA",
            "### 本章节核心：策略内核，一句话概括",
            ">",
        ])
        type_to_name = {
            "positioning_strategy": "定位策略",
            "audience_strategy": "受众策略",
            "narrative_strategy": "叙事策略",
            "visual_strategy": "视觉策略",
            "execution_strategy": "执行策略",
            "conversion_strategy": "转化策略",
        }
        for s in strategies[:5]:
            stype_name = type_to_name.get(s["strategy_type"], s["strategy_type"])
            lines.append(f"▶ **{s['name']}** ({stype_name}): {s.get('reusable_principle', '')[:80]}...")
        lines.append("")

    # 内容结构策略
    content_patterns = [p for p in patterns if p.get("pattern_type") == "content_structure"]
    if content_patterns:
        lines.extend([
            "## 内容结构策略",
            "### 本章节核心：内容编排，一句话概括",
            ">",
        ])
        for p in content_patterns[:2]:
            lines.append(f"▶ {p.get('description', '')[:100]}")
        lines.append("")

    # 受众洞察
    audience_patterns = [p for p in patterns if p.get("pattern_type") == "audience_insight"]
    if audience_patterns:
        lines.extend([
            "## 受众洞察",
            "### 本章节核心：用户理解，一句话概括",
            ">",
        ])
        for p in audience_patterns[:2]:
            lines.append(f"▶ {p.get('description', '')[:100]}")
        lines.append("")

    # 执行方法
    exec_patterns = [p for p in patterns if p.get("pattern_type") == "execution_method"]
    if exec_patterns:
        lines.extend([
            "## 执行方法",
            "### 本章节核心：落地执行，一句话概括",
            ">",
        ])
        for p in exec_patterns[:2]:
            lines.append(f"▶ {p.get('description', '')[:100]}")
        lines.append("")

    # 限制条件
    lines.extend([
        "## 限制条件",
        "### 本章节核心：使用边界，一句话概括",
        ">",
    ])
    if len(ai_fragments) < 3:
        lines.append("⚠️ 当前视觉样本较少，视觉策略仅供初步参考。")
        lines.append("")
    lines.append(f"▶ 数据来源案例: {case_id}")
    lines.append(f"▶ 质量等级: {quality_level}（{dataset}）")
    lines.append("▶ 仅为 draft 状态，不可直接用于生产")
    lines.append("")

    # 来源案例
    lines.extend([
        "## 来源案例",
        "### 本章节核心：数据溯源，一句话概括",
        ">",
        f"- **case_id**: {case_id}",
        f"- **标题**: {meta.get('title', '未知')}",
        f"- **来源文件**: {meta.get('original_filename', '未知')}",
        f"- **数据集**: {dataset}",
        "",
    ])

    # 片段统计
    lines.extend([
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
        f"*生成时间: {now_iso()}*",
    ])

    return "\n".join(lines)


def build_visual_strategy_section(patterns: List[Dict], ai_fragments: List[Dict]) -> str:
    """构建视觉策略章节"""
    if len(ai_fragments) < 3:
        return "## 视觉策略\n\n⚠️ 当前视觉样本较少，视觉策略仅供初步参考。"

    visual_patterns = [p for p in patterns if p.get("pattern_type") == "visual_direction"]

    lines = ["## 视觉策略", ""]

    if visual_patterns:
        for p in visual_patterns[:2]:
            desc = p.get("description", "")
            if desc:
                lines.append(f"- {desc[:120]}")

    keywords = []
    for af in ai_fragments:
        keywords.extend(af.get("keywords", []))
    if keywords:
        unique_kw = list(dict.fromkeys(k for k in keywords if len(k) < 20))[:8]
        lines.append(f"- 视觉关键词: {', '.join(unique_kw)}")

    return "\n".join(lines)


def build_examples_md(data: Dict, skill_id: str) -> str:
    """构建 examples.md 内容"""
    patterns = data.get("patterns", [])
    case_id = data["case_id"]

    lines = [
        "# Examples",
        "",
        "## 示例 1: 奢侈酒店春节活动",
        "",
        "### Brief",
        "",
        "某国际奢侈酒店品牌计划在春节期间推出高端定制活动，",
        "目标客群为高净值家庭（企业主、金融从业者），",
        "预算约 200 万元，需要完整的活动方案。",
        "",
        "### 应调用能力",
        "",
        "- 奢侈品牌叙事策略",
        "- 高端受众洞察",
        "- 内容结构设计（节庆主题）",
        "- 视觉方向定义（高端简约风格）",
        "- 执行规划（高端活动落地）",
        "",
        "### 输出方向",
        "",
        "- 品牌核心信息（春节点题）",
        "- 目标受众画像（高净值家庭）",
        "- 内容框架（春节仪式感 + 品牌温度）",
        "- 视觉风格（简约留白、品牌色为主）",
        "- 活动流程与物料清单",
        "",
        "---",
        "",
        "## 示例 2: 品牌年会策划",
        "",
        "### Brief",
        "",
        "某国内领先家电品牌举办年度经销商大会，",
        "参会人数约 500 人，核心目标为强化品牌信念、激励经销商。",
        "预算约 150 万元，需要整体策划方案。",
        "",
        "### 应调用能力",
        "",
        "- 企业级叙事结构",
        "- 内容结构设计（年度总结 + 展望）",
        "- 视觉方向（专业商务风格）",
        "- 执行方法（大型活动落地）",
        "",
        "### 输出方向",
        "",
        "- 叙事主线（品牌成就 + 未来愿景）",
        "- 环节结构（开场 + 回顾 + 激励 + 展望）",
        "- 视觉呈现（品牌色 + 专业摄影）",
        "- 关键物料（主 KV、视频、舞台设计）",
        "",
        "---",
        "",
        f"*来源案例: {case_id}*",
    ]

    return "\n".join(lines)


def save_skill(skill_id: str, content: Dict) -> Dict:
    """保存 Skill 到 skills/draft/<skill_id>/"""
    draft_dir = Config.DRAFT_DIR / skill_id
    draft_dir.mkdir(parents=True, exist_ok=True)

    # skill.json
    skill_json_path = draft_dir / "skill.json"
    with open(skill_json_path, "w", encoding="utf-8") as f:
        json.dump(content["skill_json"], f, ensure_ascii=False, indent=2)

    # SKILL.md
    skill_md_path = draft_dir / "SKILL.md"
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(content["skill_md"])

    # examples.md
    examples_md_path = draft_dir / "examples.md"
    with open(examples_md_path, "w", encoding="utf-8") as f:
        f.write(content["examples_md"])

    return {
        "skill_json": str(skill_json_path),
        "skill_md": str(skill_md_path),
        "examples_md": str(examples_md_path),
    }


def upsert_skill_db(skill_json: Dict) -> None:
    """写入或更新 skills 表"""
    conn = get_connection()
    cur = conn.cursor()

    now = now_iso()

    # 检查是否已存在
    cur.execute("SELECT skill_id FROM skills WHERE skill_id = ?", (skill_json["skill_id"],))
    exists = cur.fetchone() is not None

    if exists:
        # 更新（保留 source_cases，更新 updated_at）
        cur.execute("""
            UPDATE skills SET
                display_name = ?,
                status = ?,
                quality_level = ?,
                callable = ?,
                dataset = ?,
                updated_at = ?
            WHERE skill_id = ?
        """, (
            skill_json["display_name"],
            skill_json["status"],
            skill_json["quality_level"],
            0,  # callable = false
            skill_json["dataset"],
            now,
            skill_json["skill_id"],
        ))
    else:
        # 插入
        cur.execute("""
            INSERT INTO skills (skill_id, display_name, status, quality_level, callable, dataset, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            skill_json["skill_id"],
            skill_json["display_name"],
            skill_json["status"],
            skill_json["quality_level"],
            0,  # callable = false
            skill_json["dataset"],
            now,
            now,
        ))

    conn.commit()
    conn.close()


def compose_skill_for_case(case_id: str, skill_id: str) -> Dict:
    """
    为 case 合成 draft Skill

    Args:
        case_id: Case ID
        skill_id: Skill ID（如 luxury-hotel-festival）

    Returns:
        {
            "success": bool,
            "message": str,
            "skill_id": str,
            "quality_level": str,
            "output_dir": str,
        }
    """
    # 加载 case 数据
    data = load_case_data(case_id)

    if data["meta"] is None:
        return {"success": False, "message": f"Case 不存在: {case_id}"}

    if not data["patterns"]:
        return {"success": False, "message": f"Case 没有 Patterns，请先运行 extract-patterns"}

    # 构建 Skill 内容
    content = build_skill_content(data, skill_id)

    # 保存到 draft 目录
    paths = save_skill(skill_id, content)

    # 更新数据库
    upsert_skill_db(content["skill_json"])

    return {
        "success": True,
        "message": f"Skill 合成成功 (draft)",
        "skill_id": skill_id,
        "quality_level": content["skill_json"]["quality_level"],
        "dataset": content["skill_json"]["dataset"],
        "output_dir": str(Config.DRAFT_DIR / skill_id),
    }