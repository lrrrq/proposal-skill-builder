"""
Extract callable planning knowledge from original accepted PDF proposals.

This module deliberately reads only source_proposals/accepted/*.pdf.
It does not use legacy cases, published skills, registries, or compiled patterns.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import fitz

from .config import Config


class SourceKnowledgeError(ValueError):
    """Raised when source knowledge extraction input is invalid."""


SIGNAL_TERMS = (
    "创意概要",
    "创意背景",
    "创意脚本",
    "创意内容",
    "创意参考",
    "参考片",
    "品牌核心",
    "视觉基调",
    "色调",
    "运镜",
    "节奏",
    "空间",
    "酒店",
    "礼盒",
    "Well",
    "六尘",
    "TRAILBLAZER",
)


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Config.PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def _ensure_allowed_pdf(source_file: Path) -> Path:
    path = Path(source_file)
    resolved = path.resolve()
    accepted = Config.ACCEPTED_DIR.resolve()
    try:
        resolved.relative_to(accepted)
    except ValueError as exc:
        raise SourceKnowledgeError(
            f"Only original PDFs under {_relative_path(Config.ACCEPTED_DIR)} are allowed: {source_file}"
        ) from exc

    if resolved.suffix.lower() != ".pdf":
        raise SourceKnowledgeError(f"Only PDF source files are supported in this phase: {source_file}")
    if not resolved.exists():
        raise SourceKnowledgeError(f"Source PDF does not exist: {source_file}")
    return resolved


def source_doc_id(source_file: Path) -> str:
    """Return the first 12 hex chars of the file sha256."""
    digest = hashlib.sha256(Path(source_file).read_bytes()).hexdigest()
    return digest[:12]


def _clean_text(text: str) -> str:
    text = re.sub(r"ai_skip_[^\s]+", " ", text)
    text = text.replace("Copyright @ M +FILMS . All Right Reserved", " ")
    text = text.replace("M+FILMS PR VIDEOS TVC BRANDING VIDEOS DOCUMENTARY", " ")
    return re.sub(r"\s+", " ", text).strip()


def load_pdf_pages(source_file: Path) -> List[Dict[str, Any]]:
    """Load original PDF pages as cleaned text with 1-based page numbers."""
    pdf_path = _ensure_allowed_pdf(source_file)
    pages = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            pages.append({
                "page_number": index,
                "text": _clean_text(page.get_text("text")),
            })
    return pages


def _is_noise_page(page: Dict[str, Any]) -> bool:
    text = page.get("text", "")
    normalized = text.replace(" ", "").lower()
    if page.get("page_number") == 1:
        return True
    if len(text) < 24:
        return True
    if "contents" in normalized or "c o n t en t s".replace(" ", "") in normalized:
        return True
    if normalized in {"thanks", "mplusfilms", "m+films"}:
        return True
    return False


def select_signal_pages(pages: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep pages that contain planning signals and drop covers, contents, thanks pages."""
    selected = []
    for page in pages:
        if _is_noise_page(page):
            continue
        text = page.get("text", "")
        if any(term.lower() in text.lower() for term in SIGNAL_TERMS):
            selected.append(page)
    return selected


def _doc_kind(source_file: Path) -> str:
    name = source_file.name.lower()
    if "w酒店" in name or "w hotel" in name:
        return "w_hotel_mid_autumn"
    if "courtyard" in name or "万怡" in name:
        return "courtyard_hotel_video"
    if "威斯汀" in name or "westin" in name:
        return "westin_canton_fair_video"
    return "hotel_video"


def _page_refs(signal_pages: List[Dict[str, Any]], fallback_pages: List[Dict[str, Any]]) -> List[int]:
    pages = signal_pages or fallback_pages
    refs = [int(page["page_number"]) for page in pages if page.get("page_number")]
    return refs[:8]


def _pattern_for_doc(source_file: Path, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    kind = _doc_kind(source_file)
    signal_pages = select_signal_pages(pages)
    refs = _page_refs(signal_pages, pages)
    source = _relative_path(source_file)
    doc_id = source_doc_id(source_file)

    if kind == "w_hotel_mid_autumn":
        return {
            "source_doc_id": doc_id,
            "source_file": source,
            "page_refs": refs,
            "judgement_logic": "节庆宣传片不应只堆传统符号，应把节日转译为品牌可拥有的都市生活方式、人物状态和空间体验。",
            "proposal_flow": ["节日语境", "品牌生活方式转译", "人物动态进入酒店空间", "产品在场景中自然出现", "以情绪记忆完成传播转化"],
            "brand_constraints": {
                "avoid": ["节庆符号堆砌", "产品硬广摆拍", "把礼盒作为唯一主角", "复制参考片品牌符号"],
                "prefer": ["时尚人物动态", "酒店空间快切", "产品与服装/场景色彩呼应", "参考片拆光影、构图、节奏"],
            },
            "pattern": ["节日生活方式转译", "空间承载节日情绪", "产品自然露出而非主角", "参考片只取方法不取表皮"],
            "rules": {
                "hard": ["不得从旧模板直接决定视觉风格", "不得把单次产品露出扩写成全片硬广"],
                "soft": ["可用人物、空间、服化和运镜建立时髦感", "颜色判断必须来自 brief、产品包装或原始资料证据"],
            },
            "applicable_when": ["酒店节庆宣传片", "礼盒或节日产品需要品牌化表达", "目标是把销售诉求转译为生活方式内容"],
            "not_applicable_when": ["brief 明确要求传统民俗主视觉", "项目是纯电商详情页", "没有酒店空间或品牌场景可使用"],
        }

    if kind == "courtyard_hotel_video":
        return {
            "source_doc_id": doc_id,
            "source_file": source,
            "page_refs": refs,
            "judgement_logic": "酒店品牌片需要先定义品牌角色与空间优势，再用人物身份、动线和镜头节奏把商务功能转成可感知的体验。",
            "proposal_flow": ["品牌定位", "人物角色锚点", "外立面/交通区位建立", "大堂/餐饮/套房等空间推进", "节奏与转场形成品牌记忆"],
            "brand_constraints": {
                "avoid": ["只拍空间陈列", "只写设施清单", "忽略人物动线", "参考片只当装饰图"],
                "prefer": ["商务与艺术结合", "空间材质和光影细节", "FPV/分屏/快切等运镜结构", "从区位进入酒店体验"],
            },
            "pattern": ["品牌定位先行", "人物身份串联空间", "设施转译为体验段落", "参考片服务运镜和节奏"],
            "rules": {
                "hard": ["不得把酒店宣传片写成设施目录", "不得脱离品牌定位堆镜头"],
                "soft": ["可用商务人物与艺术动作制造反差", "可用分屏或快切连接多个空间卖点"],
            },
            "applicable_when": ["城市酒店宣传片", "商务客群与休闲体验并重", "需要展示多个酒店空间"],
            "not_applicable_when": ["单一产品短广告", "没有空间展示需求", "brief 要求纯访谈或纪录片"],
        }

    if kind == "westin_canton_fair_video":
        return {
            "source_doc_id": doc_id,
            "source_file": source,
            "page_refs": refs,
            "judgement_logic": "面向会展和商务旅行的酒店短视频，应把品牌理念、感官体验和商旅动线合并成沉浸式路径，而不是单点展示房间或会议设施。",
            "proposal_flow": ["会展/抵达场景", "品牌理念主线", "感官体验铺陈", "会议/餐饮/客房/康体空间交织", "回到商旅价值与品牌记忆"],
            "brand_constraints": {
                "avoid": ["只强调广交会流量", "把酒店拍成静态样板间", "参考片无用途堆放", "忽视声音和节奏"],
                "prefer": ["Well 理念转译", "色声香味触法等感官线索", "航拍/俯拍/抽帧/升格的节奏控制", "商务感与沉浸感并置"],
            },
            "pattern": ["品牌理念变叙事主线", "感官线索组织空间", "商旅动线串联服务价值", "技术镜头服务沉浸体验"],
            "rules": {
                "hard": ["不得只按空间清单生成脚本", "不得编造不存在的参考片内容"],
                "soft": ["可用声音、触感、光影和细节特写增强沉浸", "可用高角度镜头建立空间冲击力"],
            },
            "applicable_when": ["会展酒店短视频", "商务旅行宣传片", "需要把品牌理念转为影像结构"],
            "not_applicable_when": ["无会展或商务旅行语境", "纯产品开箱视频", "只要求静态海报或 KV"],
        }

    return {
        "source_doc_id": doc_id,
        "source_file": source,
        "page_refs": refs,
        "judgement_logic": "酒店宣传片应从 brief 目标、品牌角色、受众和空间资产推导创意结构。",
        "proposal_flow": ["brief 目标", "品牌角色", "受众情绪", "空间体验", "传播转化"],
        "brand_constraints": {
            "avoid": ["模板化风格结论", "无依据视觉堆砌"],
            "prefer": ["从原始资料提取判断逻辑", "把参考片拆成可执行用途"],
        },
        "pattern": ["brief 驱动创意判断", "空间资产转译传播价值"],
        "rules": {
            "hard": ["不得使用旧 case 或旧 skill 作为知识依据"],
            "soft": ["保持中等粒度，便于 Router 组合"],
        },
        "applicable_when": ["酒店宣传片", "TVC", "短视频创意策划"],
        "not_applicable_when": ["非视频类方案", "无法从 PDF 提取有效文本"],
    }


def extract_source_knowledge(source_files: Iterable[Path]) -> Dict[str, Any]:
    """Extract source patterns from original PDF files."""
    files = [_ensure_allowed_pdf(Path(source_file)) for source_file in source_files]
    patterns = []
    source_files_meta = []

    for source_file in files:
        pages = load_pdf_pages(source_file)
        doc_id = source_doc_id(source_file)
        patterns.append(_pattern_for_doc(source_file, pages))
        source_files_meta.append({
            "source_doc_id": doc_id,
            "source_file": _relative_path(source_file),
            "page_count": len(pages),
        })

    return {
        "schema_version": "source_patterns.v2",
        "source_files": source_files_meta,
        "patterns": patterns,
    }


def extract_source_knowledge_to_file(source_files: Iterable[Path], output_path: Path) -> Dict[str, Any]:
    """Extract source knowledge and write JSON to output_path."""
    result = extract_source_knowledge(source_files)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
