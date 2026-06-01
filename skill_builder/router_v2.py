"""
Router V2 - frozen minimal loop for W Hotel promo video planning.

This module is intentionally isolated from the legacy published registry.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Config


V2_REGISTRY_PATH = Config.ROUTER_V2_REGISTRY_JSON
SOURCE_PATTERNS_PATH = Config.KNOWLEDGE_DIR / "v2" / "w-hotel-tvc" / "source_patterns.json"
SUPPORTED_BRAND_TERMS = ("W酒店", "w酒店", "W 酒店", "w hotel", "W Hotel")
SUPPORTED_VIDEO_TERMS = ("TVC", "tvc", "宣传片", "短视频", "品牌片", "广告片")


def _contains_any(text: str, terms: Tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _extract_after_label(brief: str, labels: List[str]) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:{label_pattern})[是为:：]?\s*([^，。；;\n]+)",
        brief,
    )
    return match.group(1).strip() if match else ""


def _extract_duration(brief: str) -> str:
    match = re.search(r"(\d+\s*(?:秒|分钟|min|s))", brief, re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else ""


def _extract_channels(brief: str) -> List[str]:
    channels = []
    for channel in ("小红书", "视频号", "抖音", "B站", "朋友圈", "官网", "活动现场"):
        if channel in brief:
            channels.append(channel)
    return channels


def _extract_deliverables(brief: str) -> List[str]:
    deliverables = []
    for item in ("创意方向", "脚本大纲", "分镜", "MD", "PPT", "PDF"):
        if item in brief:
            deliverables.append(item)
    return deliverables


def _extract_reference_inputs(brief: str) -> List[str]:
    references = []
    pattern = re.compile(r"参考([^，。；;\n]+)")
    for match in pattern.finditer(brief):
        raw = match.group(1).strip()
        parts = re.split(r"[、,，]|以及|和(?=[A-Za-z\u4e00-\u9fff]+(?:宣传片|短片|广告|TVC|tvc))", raw)
        references.extend(part.strip() for part in parts if part.strip())
    return list(dict.fromkeys(references))


def _extract_forbidden(brief: str) -> List[str]:
    forbidden = []
    for match in re.finditer(r"(?:不要|禁止|避免)([^，。；;\n]+)", brief):
        value = match.group(1).strip()
        if value:
            forbidden.append(value)
    return list(dict.fromkeys(forbidden))


def _extract_constraints(brief: str) -> List[str]:
    constraints = []
    for match in re.finditer(r"(?:要求|需要)([^，。；;\n]+)", brief):
        value = match.group(1).strip()
        if value and not value.startswith("参考"):
            constraints.append(value)
    if "金色点缀" in brief:
        constraints.append("金色点缀")
    return list(dict.fromkeys(constraints))


def decompose_brief(brief: str) -> Dict[str, Any]:
    """Extract explicit brief facts before any creative generation."""
    business_goal = _extract_after_label(brief, ["业务目标", "商业目标"])
    audience = _extract_after_label(brief, ["目标人群", "受众", "目标受众"])
    deliverables = _extract_deliverables(brief)
    duration = _extract_duration(brief)
    channels = _extract_channels(brief)

    if "W酒店" in brief or "W 酒店" in brief:
        brand = "W酒店"
    else:
        brand = _extract_after_label(brief, ["品牌", "客户"])

    project_type = ""
    for term in SUPPORTED_VIDEO_TERMS:
        if term in brief:
            project_type = "TVC" if term.lower() == "tvc" else term
            break

    missing = []
    if not brand:
        missing.append("brand_or_subject")
    if not project_type:
        missing.append("project_type")
    if not business_goal:
        missing.append("business_goal")
    if not audience:
        missing.append("target_audience")
    if not deliverables:
        missing.append("deliverables")

    key_judgements = [
        {
            "judgement": "先拆 brief 和约束，再进入创意命题；当前不生成 PPT/PDF。",
            "basis": "系统 Phase 1 最小闭环要求",
        }
    ]
    if business_goal:
        key_judgements.append({
            "judgement": f"商业目标已明确为「{business_goal}」，不应重复追问业务目标。",
            "basis": "brief 明示字段",
        })
    if _extract_reference_inputs(brief):
        key_judgements.append({
            "judgement": "参考输入已出现，后续必须拆解参考什么和不参考什么。",
            "basis": "brief 明示参考片",
        })

    return {
        "raw_brief": brief,
        "brand_or_subject": brand,
        "project_type": project_type,
        "business_goal": business_goal,
        "communication_goal": "",
        "target_audience": audience,
        "duration": duration,
        "channels": channels,
        "deliverables": deliverables,
        "reference_inputs": _extract_reference_inputs(brief),
        "explicit_constraints": _extract_constraints(brief),
        "explicit_forbidden": _extract_forbidden(brief),
        "missing_information": missing,
        "key_judgements": key_judgements,
        "assumptions": [],
    }


def _source_material_constraints(source_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    constraints = []
    for claim in source_claims:
        if "judgement_logic" in claim:
            reason = (
                f"source_doc_id={claim['source_doc_id']}; "
                f"source_file={claim['source_file']}; "
                f"page_refs={','.join(str(page) for page in claim['page_refs'])}"
            )
            constraints.append({
                "type": "strategy",
                "rule": claim["judgement_logic"],
                "source": "source_material",
                "strength": "soft",
                "reason": reason,
                "allowed_alternatives": claim.get("pattern", []),
            })
        else:
            constraints.append({
                "type": "strategy",
                "rule": claim["claim"],
                "source": "source_material",
                "strength": "soft",
                "reason": f"候选原始资料，需人工复核: {claim['evidence_source']} / {claim.get('page', '')}",
                "allowed_alternatives": [],
            })
    return constraints


def resolve_constraints(
    analysis: Dict[str, Any],
    source_claims: List[Dict[str, Any]],
    qa_confirmed: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Resolve dynamic constraints from brief, source evidence, and QA."""
    constraints = []
    forbidden_text = " ".join(analysis.get("explicit_forbidden", []))
    explicit_text = " ".join(analysis.get("explicit_constraints", []))

    if "金色点缀" in explicit_text or "金色点缀" in analysis.get("raw_brief", ""):
        constraints.append({
            "type": "visual",
            "rule": "允许克制的金色点缀，但必须服务品牌质感和画面层次。",
            "source": "brief",
            "strength": "soft",
            "reason": "用户 brief 明示品牌要求金色点缀。",
            "allowed_alternatives": ["香槟金", "暖光", "局部金属点缀"],
        })

    for item in analysis.get("explicit_forbidden", []):
        if item:
            constraint_type = "visual" if any(term in item for term in ("色", "配色", "视觉", "风格")) else "strategy"
            constraints.append({
                "type": constraint_type,
                "rule": f"避免{item}",
                "source": "brief",
                "strength": "hard",
                "reason": "用户 brief 明示禁忌；该约束只适用于本次 brief。",
                "allowed_alternatives": [],
            })

    constraints.extend(_source_material_constraints(source_claims))

    for item in qa_confirmed or []:
        constraints.append({
            "type": item.get("type", "strategy"),
            "rule": item.get("rule", ""),
            "source": "qa_confirmed",
            "strength": item.get("strength", "hard"),
            "reason": item.get("reason", "用户追问确认。"),
            "allowed_alternatives": item.get("allowed_alternatives", []),
        })

    return {"constraints": constraints}


class RouterV2:
    """Minimal Router V2 that only reads the V2 registry namespace."""

    def __init__(self, registry_path: Path = V2_REGISTRY_PATH, source_patterns_path: Path = SOURCE_PATTERNS_PATH):
        self.registry_path = Path(registry_path)
        self.source_patterns_path = Path(source_patterns_path)
        self.project_root = Config.PROJECT_ROOT

    def route(self, brief: str) -> Dict[str, Any]:
        analysis = decompose_brief(brief)
        if not self._is_supported(analysis):
            return {
                "supported": False,
                "reason": "当前 Phase 1 只支持 W 酒店 / 酒店宣传片风格验证。",
                "next_action": "进入人工拆解或等待 Phase 2。",
                "skill_ids": [],
                "brief_analysis": analysis,
            }

        skills = self._load_v2_skills()
        source_patterns = self._load_source_patterns()
        constraints = resolve_constraints(analysis, source_patterns)
        context_packet = {
            "brief_analysis": analysis,
            "skills": skills,
            "source_patterns": source_patterns,
            "constraints": constraints,
        }
        proposal_md = self._render_md(context_packet)
        return {
            "supported": True,
            "brief_analysis": analysis,
            "skill_ids": [skill["skill_id"] for skill in skills],
            "context_packet": context_packet,
            "constraints": constraints,
            "proposal_md": proposal_md,
        }

    def route_to_file(self, brief: str, output_path: Path) -> Dict[str, Any]:
        result = self.route(brief)
        if result.get("supported"):
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result["proposal_md"], encoding="utf-8")
            result["output_path"] = str(output)
        return result

    def _is_supported(self, analysis: Dict[str, Any]) -> bool:
        brand = analysis.get("brand_or_subject", "")
        project_type = analysis.get("project_type", "")
        return brand == "W酒店" and bool(project_type)

    def _load_registry(self) -> Dict[str, Any]:
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _load_v2_skills(self) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        allowed = registry.get("allowed_skill_ids", [])
        loaded = []
        for entry in registry.get("skills", []):
            if entry.get("skill_id") not in allowed:
                continue
            skill_path = self.project_root / entry["path"]
            skill = json.loads(skill_path.read_text(encoding="utf-8"))
            # V2 source evidence comes from knowledge/v2/source_patterns.json.
            # Legacy claims in early V2 assets are ignored to avoid case_id leakage.
            skill.pop("claims", None)
            loaded.append(skill)
        if [skill["skill_id"] for skill in loaded] != allowed:
            raise ValueError("Router V2 registry must load exactly the allowed skill set in order.")
        return loaded

    def _load_source_patterns(self) -> List[Dict[str, Any]]:
        if not self.source_patterns_path.exists():
            return []
        payload = json.loads(self.source_patterns_path.read_text(encoding="utf-8"))
        return payload.get("patterns", [])

    def _collect_claims(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        claims = []
        for skill in skills:
            claims.extend(skill.get("claims", []))
        return claims

    def _render_md(self, context_packet: Dict[str, Any]) -> str:
        analysis = context_packet["brief_analysis"]
        constraints = context_packet["constraints"]["constraints"]
        source_patterns = context_packet.get("source_patterns", [])

        title = "# W酒店端午节TVC创意提案"
        lines = [
            title,
            "",
            "## 1. Brief 摘要",
            f"- 品牌/主体：{analysis.get('brand_or_subject') or '待确认'}",
            f"- 项目类型：{analysis.get('project_type') or '待确认'}",
            f"- 商业目标：{analysis.get('business_goal') or '待确认'}",
            f"- 目标人群：{analysis.get('target_audience') or '待确认'}",
            f"- 时长/渠道：{analysis.get('duration') or '待确认'} / {'、'.join(analysis.get('channels', [])) or '待确认'}",
            f"- 交付内容：{'、'.join(analysis.get('deliverables', [])) or '待确认'}",
            "",
            "## 2. 关键判断",
        ]
        for item in analysis.get("key_judgements", []):
            lines.append(f"- {item['judgement']}（依据：{item['basis']}）")

        lines.extend([
            "",
            "## 3. 核心洞察",
            "- 城市年轻家庭不是缺少节日符号，而是缺少一个能把节日变轻、变松弛、变值得分享的场景。",
            "- W酒店的角色不是传统礼盒销售终端，而是把节日变成城市生活方式的情绪入口。",
            "",
            "## 4. 创意命题",
            "- 让端午从礼盒回到一次城市里的短暂逃离。",
            "- 创意不从传统符号和包装摆拍出发，而从年轻家庭的周末情绪、酒店空间和轻盈夏日感出发。",
            "",
            "## 5. 影片结构",
            "- 片头：城市热度与日常节奏，建立需要逃离的情绪。",
            "- 发展：进入酒店空间，噪音退场，光线、窗景、亲子状态成为主角。",
            "- 转折：端午礼盒自然出现，成为关系和场景的一部分，不做硬广摆拍。",
            "- 收束：城市仍在窗外，节日已经被重新打开。",
            "",
            "## 6. 视觉与参考方向",
        ])
        references = analysis.get("reference_inputs", [])
        if references:
            for reference in references:
                lines.append(f"- {reference}：只拆光影、构图、节奏和松弛感；不复制品牌符号和具体场景。")
        else:
            lines.append("- 待补参考片；当前不编造参考图。")

        lines.extend([
            "",
            "## 7. 传播价值",
            "- 小红书负责情绪种草：窗边、夏日、亲子、轻度度假的画面记忆。",
            "- 视频号负责品牌心智：W酒店不是传统节庆场地，而是城市家庭的短途情绪目的地。",
            "- 礼盒预订作为自然转化，不抢占影片第一主角。",
            "",
            "## 8. 动态约束与禁忌",
        ])
        for item in constraints:
            alternatives = item.get("allowed_alternatives", [])
            alt = f" 可替代：{'、'.join(alternatives)}。" if alternatives else ""
            lines.append(
                f"- [{item['source']} / {item['strength']}] {item['rule']} 理由：{item['reason']}{alt}"
            )

        lines.extend([
            "",
            "## 9. 待确认问题",
        ])
        missing = analysis.get("missing_information", [])
        if missing:
            for key in missing:
                lines.append(f"- 请补充：{key}")
        else:
            lines.append("- 当前 brief 已足够进入 MD 方案评审；不进入 PPT/PDF。")

        lines.extend([
            "",
            "## 证据来源",
        ])
        for pattern in source_patterns:
            lines.append(
                f"- {pattern['source_doc_id']} / {pattern['source_file']} / pages {','.join(str(page) for page in pattern['page_refs'])}：{pattern['judgement_logic']}"
            )
        if not source_patterns:
            lines.append("- 暂无 source_patterns.json；当前只输出 brief 拆解与动态约束。")

        return "\n".join(lines) + "\n"
