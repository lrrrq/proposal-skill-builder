"""
skill_checker - Skill 质量检查
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config
from .utils import now_iso


REQUIRED_SKILL_JSON_FIELDS = [
    "skill_id", "display_name", "description", "status", "dataset",
    "quality_level", "callable", "source_cases", "source_patterns",
    "source_fragments_count", "source_ai_fragments_count", "allowed_tasks",
    "created_at", "updated_at", "version",
]

REQUIRED_SKILL_MD_SECTIONS = [
    "适用场景", "输入要求", "核心判断逻辑", "处理流程", "输出格式",
    "可复用策略", "视觉策略", "内容结构策略", "受众洞察", "执行方法",
    "限制条件", "来源案例",
]


def load_skill_data(skill_id: str) -> Optional[Dict]:
    """加载 Skill 所有相关数据"""
    skill_dir = Config.DRAFT_DIR / skill_id

    if not skill_dir.exists():
        return None

    data = {
        "skill_id": skill_id,
        "dir": str(skill_dir),
        "skill_json": None,
        "skill_md": None,
        "examples_md": None,
    }

    # skill.json
    json_path = skill_dir / "skill.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data["skill_json"] = json.load(f)

    # SKILL.md
    md_path = skill_dir / "SKILL.md"
    if md_path.exists():
        data["skill_md"] = md_path.read_text(encoding="utf-8")

    # examples.md
    examples_path = skill_dir / "examples.md"
    if examples_path.exists():
        data["examples_md"] = examples_path.read_text(encoding="utf-8")

    return data


def check_structure(data: Dict) -> Dict:
    """结构检查"""
    issues = []
    passed = []

    skill_dir = Path(data["dir"])

    # 文件存在性检查
    if not (skill_dir / "skill.json").exists():
        issues.append("skill.json 不存在")
    else:
        passed.append("skill.json 存在")

    if not (skill_dir / "SKILL.md").exists():
        issues.append("SKILL.md 不存在")
    else:
        passed.append("SKILL.md 存在")

    if not (skill_dir / "examples.md").exists():
        issues.append("examples.md 不存在")
    else:
        passed.append("examples.md 存在")

    # skill.json 字段完整性
    if data["skill_json"]:
        missing_fields = [f for f in REQUIRED_SKILL_JSON_FIELDS if f not in data["skill_json"]]
        if missing_fields:
            issues.append(f"skill.json 缺少字段: {', '.join(missing_fields)}")
        else:
            passed.append("skill.json 字段完整")
    else:
        issues.append("skill.json 无法读取")

    return {
        "passed_count": len(passed),
        "failed_count": len(issues),
        "passed_items": passed,
        "failed_items": issues,
    }


def check_status(data: Dict) -> Dict:
    """状态检查"""
    issues = []
    passed = []

    if not data["skill_json"]:
        issues.append("skill.json 为空，无法检查状态")
        return {"passed_count": 0, "failed_count": len(issues), "passed_items": [], "failed_items": issues}

    sj = data["skill_json"]

    # status 必须是 draft
    if sj.get("status") != "draft":
        issues.append(f"status 必须是 draft，当前为 {sj.get('status')}")
    else:
        passed.append("status = draft")

    # callable 必须是 false
    if sj.get("callable") is not False:
        issues.append(f"callable 必须是 false，当前为 {sj.get('callable')}")
    else:
        passed.append("callable = false")

    # dataset 必须是 test 或 prod
    dataset = sj.get("dataset", "")
    if dataset not in ("test", "prod"):
        issues.append(f"dataset 必须是 test 或 prod，当前为 {dataset}")
    else:
        passed.append(f"dataset = {dataset}")

    # source_cases 不能为空
    source_cases = sj.get("source_cases", [])
    if not source_cases:
        issues.append("source_cases 不能为空")
    else:
        passed.append(f"source_cases 有 {len(source_cases)} 个案例")

    # source_patterns 不能为空
    source_patterns = sj.get("source_patterns", [])
    if not source_patterns:
        issues.append("source_patterns 不能为空")
    else:
        passed.append(f"source_patterns 有 {len(source_patterns)} 个")

    return {
        "passed_count": len(passed),
        "failed_count": len(issues),
        "passed_items": passed,
        "failed_items": issues,
    }


def check_skill_md_sections(data: Dict) -> Dict:
    """SKILL.md 章节检查"""
    issues = []
    passed = []

    if not data["skill_md"]:
        issues.append("SKILL.md 为空")
        return {"passed_count": 0, "failed_count": len(issues), "passed_items": [], "failed_items": issues}

    md_content = data["skill_md"]

    for section in REQUIRED_SKILL_MD_SECTIONS:
        if section in md_content:
            passed.append(f"章节『{section}』存在")
        else:
            issues.append(f"缺少章节『{section}』")

    return {
        "passed_count": len(passed),
        "failed_count": len(issues),
        "passed_items": passed,
        "failed_items": issues,
    }


def calculate_quality_score(data: Dict) -> Dict:
    """
    计算质量分数（满分 100）

    结构完整度 15 分
    来源溯源 15 分
    可复用抽象程度 20 分
    处理流程可执行性 15 分
    输出格式明确度 10 分
    视觉策略可信度 10 分
    示例质量 10 分
    限制条件清晰度 5 分
    """
    scores = {}
    details = {}

    # 1. 结构完整度 15 分
    structure = check_structure(data)
    # 文件存在 3分，字段完整 12分
    file_score = 3 if (data.get("skill_json") and data.get("skill_md") and data.get("examples_md")) else 0
    field_score = 12 if structure["failed_count"] == 0 else 0
    scores["structure"] = file_score + field_score
    details["structure"] = f"文件存在({file_score}/3) + 字段完整({field_score}/12)"

    # 2. 来源溯源 15 分
    if data["skill_json"]:
        sj = data["skill_json"]
        case_score = min(5, len(sj.get("source_cases", [])) * 2.5)  # 最多 5 分
        pattern_score = min(5, len(sj.get("source_patterns", [])) * 0.5)  # 最多 5 分
        frag_count = sj.get("source_fragments_count", 0) + sj.get("source_ai_fragments_count", 0)
        frag_score = min(5, frag_count * 0.1)  # 最多 5 分
        scores["traceability"] = round(case_score + pattern_score + frag_score, 1)
        details["traceability"] = f"案例({case_score}/5) + Patterns({pattern_score}/5) + Fragments({frag_score}/5)"
    else:
        scores["traceability"] = 0
        details["traceability"] = "无 skill.json"

    # 3. 可复用抽象程度 20 分
    # 检查 SKILL.md 中可复用策略章节的内容质量
    if data["skill_md"]:
        # 提取可复用策略章节内容
        match = re.search(r"## 可复用策略\s*\n(.*?)(?=\n##|\Z)", data["skill_md"], re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 按行数计算（每行约 2 分，上限 20 分）
            lines = [l for l in content.split("\n") if l.strip() and l.strip().startswith("-")]
            abstract_score = min(20, len(lines) * 2)
            scores["abstract"] = abstract_score
            details["abstract"] = f"可复用策略 {len(lines)} 条 ({abstract_score}/20)"
        else:
            scores["abstract"] = 5
            details["abstract"] = "无可用策略章节 (5/20)"
    else:
        scores["abstract"] = 0
        details["abstract"] = "无 SKILL.md"

    # 4. 处理流程可执行性 15 分
    if data["skill_md"]:
        match = re.search(r"## 处理流程\s*\n(.*?)(?=\n##|\Z)", data["skill_md"], re.DOTALL)
        if match:
            content = match.group(1).strip()
            steps = [l for l in content.split("\n") if l.strip().startswith(("1.", "2.", "3.", "4.", "5."))]
            step_score = min(15, len(steps) * 3)
            scores["process"] = step_score
            details["process"] = f"处理流程 {len(steps)} 步 ({step_score}/15)"
        else:
            scores["process"] = 3
            details["process"] = "无处理流程 (3/15)"
    else:
        scores["process"] = 0
        details["process"] = "无 SKILL.md"

    # 5. 输出格式明确度 10 分
    if data["skill_md"]:
        match = re.search(r"## 输出格式\s*\n(.*?)(?=\n##|\Z)", data["skill_md"], re.DOTALL)
        if match:
            content = match.group(1).strip()
            lines = [l for l in content.split("\n") if l.strip() and l.strip().startswith("-")]
            output_score = min(10, len(lines) * 2)
            scores["output"] = output_score
            details["output"] = f"输出格式 {len(lines)} 条 ({output_score}/10)"
        else:
            scores["output"] = 2
            details["output"] = "无输出格式 (2/10)"
    else:
        scores["output"] = 0
        details["output"] = "无 SKILL.md"

    # 6. 视觉策略可信度 10 分
    if data["skill_md"]:
        match = re.search(r"## 视觉策略\s*\n(.*?)(?=\n##|\Z)", data["skill_md"], re.DOTALL)
        if match:
            content = match.group(1).strip()
            has_warning = "⚠️" in content or "样本较少" in content
            has_keyword = any(kw in content for kw in ["视觉", "风格", "画面", "色彩"])
            visual_score = 10 if (has_keyword and not has_warning) else 6 if has_keyword else 3
            scores["visual"] = visual_score
            details["visual"] = f"视觉策略 ({visual_score}/10)" + (" [有警告]" if has_warning else "")
        else:
            scores["visual"] = 2
            details["visual"] = "无视觉策略章节 (2/10)"
    else:
        scores["visual"] = 0
        details["visual"] = "无 SKILL.md"

    # 7. 示例质量 10 分
    if data["examples_md"]:
        # 检查示例数量和质量
        brief_count = data["examples_md"].count("### Brief")
        output_count = data["examples_md"].count("### 输出方向")
        example_score = min(10, (brief_count * 4) + (output_count * 1))
        scores["examples"] = example_score
        details["examples"] = f"Brief({brief_count}个) + 输出方向({output_count}个) = {example_score}/10"
    else:
        scores["examples"] = 0
        details["examples"] = "无 examples.md (0/10)"

    # 8. 限制条件清晰度 5 分
    if data["skill_md"]:
        match = re.search(r"## 限制条件\s*\n(.*?)(?=\n##|\Z)", data["skill_md"], re.DOTALL)
        if match:
            content = match.group(1).strip()
            lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
            limit_score = min(5, len(lines))
            scores["limits"] = limit_score
            details["limits"] = f"限制条件 {len(lines)} 条 ({limit_score}/5)"
        else:
            scores["limits"] = 1
            details["limits"] = "无限制条件章节 (1/5)"
    else:
        scores["limits"] = 0
        details["limits"] = "无 SKILL.md"

    total = sum(scores.values())

    return {
        "total_score": total,
        "breakdown": scores,
        "details": details,
    }


def determine_quality_level(score: float, data: Dict) -> Dict:
    """
    根据分数和硬规则确定质量等级

    硬规则：
    - source_ai_fragments_count < 3，最高只能是 silver
    - source_cases 为空，直接 failed
    - source_patterns 少于 3，直接 failed
    - examples.md 为空，最高只能是 bronze
    - SKILL.md 缺少限制条件，最高只能是 bronze
    """
    sj = data.get("skill_json", {}) or {}

    # 硬规则检查
    if not sj.get("source_cases"):
        return {"level": "failed", "reason": "source_cases 为空"}

    if len(sj.get("source_patterns", [])) < 3:
        return {"level": "failed", "reason": f"source_patterns 只有 {len(sj.get('source_patterns', []))} 个，少于 3"}

    if not data.get("examples_md"):
        max_level = "bronze"
    elif not data.get("skill_md") or "限制条件" not in data.get("skill_md", ""):
        max_level = "bronze"
    elif sj.get("source_ai_fragments_count", 0) < 3:
        max_level = "silver"
    else:
        max_level = "gold"

    # 根据分数判断
    if score < 60:
        actual_level = "failed"
        reason = f"分数 {score} < 60"
    elif score < 75:
        actual_level = "bronze"
        reason = f"分数 {score} 在 60-74 之间"
    elif score < 90:
        actual_level = "silver"
        reason = f"分数 {score} 在 75-89 之间"
    else:
        actual_level = "gold"
        reason = f"分数 {score} >= 90"

    # 不能超过硬规则上限
    level_order = ["failed", "bronze", "silver", "gold"]
    max_idx = level_order.index(max_level)
    actual_idx = level_order.index(actual_level)

    if actual_idx > max_idx:
        final_level = max_level
        reason = f"分数建议 {actual_level}，但硬规则限制为 {max_level}：{reason}"
    else:
        final_level = actual_level

    return {
        "level": final_level,
        "score": score,
        "reason": reason,
        "max_allowed": max_level,
    }


def generate_report(skill_id: str, data: Dict, structure_result: Dict,
                    status_result: Dict, sections_result: Dict,
                    score_result: Dict, level_result: Dict) -> str:
    """生成检查报告"""
    sj = data.get("skill_json", {}) or {}
    current_level = sj.get("quality_level", "unknown")
    suggested_level = level_result["level"]

    # 通过项
    all_passed = []
    all_passed.extend(structure_result["passed_items"])
    all_passed.extend(status_result["passed_items"])
    all_passed.extend(sections_result["passed_items"])

    # 失败项
    all_failed = []
    all_failed.extend(structure_result["failed_items"])
    all_failed.extend(status_result["failed_items"])
    all_failed.extend(sections_result["failed_items"])

    lines = [
        f"# Skill Check Report: {skill_id}",
        "",
        f"**检查时间**: {now_iso()}",
        f"**Skill 目录**: {data['dir']}",
        "",
        "---",
        "",
        "## 基本信息",
        "",
        f"- **skill_id**: {skill_id}",
        f"- **dataset**: {sj.get('dataset', 'unknown')}",
        f"- **当前 quality_level**: {current_level}",
        f"- **检查后建议 quality_level**: **{suggested_level}**",
        f"- **评分**: {score_result['total_score']}/100",
        "",
        f"**建议**: {level_result['reason']}",
        "",
        "---",
        "",
        "## 检查结果汇总",
        "",
        f"- **结构检查**: {structure_result['passed_count']} 通过 / {structure_result['failed_count']} 失败",
        f"- **状态检查**: {status_result['passed_count']} 通过 / {status_result['failed_count']} 失败",
        f"- **章节检查**: {sections_result['passed_count']} 通过 / {sections_result['failed_count']} 失败",
        "",
    ]

    # 分数明细
    lines.extend([
        "## 分数明细",
        "",
    ])
    for k, v in score_result["breakdown"].items():
        detail = score_result["details"].get(k, "")
        lines.append(f"- **{k}**: {v}/? - {detail}")
    lines.append("")
    lines.append(f"**总分**: {score_result['total_score']}/100")
    lines.append("")

    # 通过项
    if all_passed:
        lines.extend([
            "## ✅ 通过项",
            "",
        ])
        for item in all_passed:
            lines.append(f"- {item}")
        lines.append("")

    # 失败项
    if all_failed:
        lines.extend([
            "## ❌ 失败项",
            "",
        ])
        for item in all_failed:
            lines.append(f"- {item}")
        lines.append("")

    # 风险项
    lines.extend([
        "## ⚠️ 风险项",
        "",
    ])
    if sj.get("source_ai_fragments_count", 0) < 3:
        lines.append(f"- 视觉片段仅 {sj.get('source_ai_fragments_count', 0)} 个，视觉策略可信度受限")
    if current_level != suggested_level:
        lines.append(f"- 当前等级 ({current_level}) 与建议等级 ({suggested_level}) 不一致")
    if score_result["total_score"] < 75:
        lines.append(f"- 总分 {score_result['total_score']} < 75，质量有待提升")
    if not all_failed:
        lines.append("- 暂无明显风险")
    lines.append("")

    # 是否建议发布
    can_publish = suggested_level != "failed" and score_result["total_score"] >= 60
    lines.extend([
        "## 📋 发布建议",
        "",
    ])
    if can_publish:
        lines.append(f"✅ **可以发布**（建议等级: {suggested_level}，评分: {score_result['total_score']}）")
    else:
        lines.append(f"❌ **不建议发布**（建议等级: {suggested_level}，评分: {score_result['total_score']}）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*由 Proposal Skill Builder 自动生成*")

    return "\n".join(lines)


def save_report(skill_id: str, content: str) -> str:
    """保存报告到 reports/"""
    Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = Config.REPORTS_DIR / f"skill_check_{skill_id}.md"
    report_path.write_text(content, encoding="utf-8")
    return str(report_path)


def check_skill(skill_id: str) -> Dict:
    """
    检查 Skill 质量

    Returns:
        {
            "success": bool,
            "skill_id": str,
            "score": float,
            "suggested_level": str,
            "can_publish": bool,
            "report_path": str,
            "passed_items": list,
            "failed_items": list,
            "risk_items": list,
        }
    """
    # 加载数据
    data = load_skill_data(skill_id)
    if data is None:
        return {"success": False, "message": f"Skill 不存在: {skill_id}"}

    # 执行各项检查
    structure_result = check_structure(data)
    status_result = check_status(data)
    sections_result = check_skill_md_sections(data)
    score_result = calculate_quality_score(data)
    level_result = determine_quality_level(score_result["total_score"], data)

    # 生成报告
    report_content = generate_report(
        skill_id, data, structure_result, status_result, sections_result,
        score_result, level_result
    )
    report_path = save_report(skill_id, report_content)

    # 汇总通过/失败项
    all_passed = []
    all_failed = []
    all_passed.extend(structure_result["passed_items"])
    all_passed.extend(status_result["passed_items"])
    all_passed.extend(sections_result["passed_items"])
    all_failed.extend(structure_result["failed_items"])
    all_failed.extend(status_result["failed_items"])
    all_failed.extend(sections_result["failed_items"])

    # 风险项
    risk_items = []
    sj = data.get("skill_json", {}) or {}
    if sj.get("source_ai_fragments_count", 0) < 3:
        risk_items.append(f"视觉片段仅 {sj.get('source_ai_fragments_count', 0)} 个")
    if level_result["level"] == "failed":
        risk_items.append("质量等级为 failed")
    if score_result["total_score"] < 60:
        risk_items.append(f"分数 {score_result['total_score']} < 60")

    can_publish = level_result["level"] != "failed" and score_result["total_score"] >= 60

    return {
        "success": True,
        "skill_id": skill_id,
        "score": score_result["total_score"],
        "suggested_level": level_result["level"],
        "can_publish": can_publish,
        "report_path": report_path,
        "passed_count": len(all_passed),
        "failed_count": len(all_failed),
        "passed_items": all_passed,
        "failed_items": all_failed,
        "risk_items": risk_items,
        "details": score_result,
    }