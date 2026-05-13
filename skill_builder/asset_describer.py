"""
asset_describer - 资产视觉描述
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config
from .db import get_connection
from .utils import now_iso
from .ai_client import create_ai_client


def load_assets(case_id: str) -> Optional[List[Dict]]:
    """加载 assets.json"""
    assets_path = Config.CASES_DIR / case_id / "assets.json"
    if not assets_path.exists():
        return None
    with open(assets_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_assets(case_id: str, assets: List[Dict]):
    """保存 assets.json"""
    assets_path = Config.CASES_DIR / case_id / "assets.json"
    with open(assets_path, "w", encoding="utf-8") as f:
        json.dump(assets, f, ensure_ascii=False, indent=2)


def load_fragments(case_id: str) -> Optional[List[Dict]]:
    """加载 fragments.json"""
    fragments_path = Config.CASES_DIR / case_id / "fragments.json"
    if not fragments_path.exists():
        return []
    with open(fragments_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ai_fragments(case_id: str, ai_fragments: List[Dict]):
    """保存 ai_fragments.json"""
    path = Config.CASES_DIR / case_id / "ai_fragments.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ai_fragments, f, ensure_ascii=False, indent=2)


def save_descriptions(case_id: str, descriptions: List[Dict]):
    """保存 descriptions.json"""
    path = Config.CASES_DIR / case_id / "descriptions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)


def generate_ai_fragment(asset_id: str, case_id: str, description_result: dict, index: int) -> Dict:
    """
    从描述结果生成 AI fragment
    """
    return {
        "fragment_id": f"ai-{uuid.uuid4().hex[:8]}",
        "case_id": case_id,
        "source_asset_id": asset_id,
        "index": index,
        "fragment_type": "visual_summary",
        "raw_text": description_result.get("visual_summary", ""),
        "summary": (description_result.get("visual_summary", "") or "")[:120],
        "detected_text": description_result.get("detected_text", ""),
        "keywords": [],
        "quality_flags": ["ai_generated"],
    }


def describe_assets_dry_run(case_id: str, assets: List[Dict], needs_vision: List[Dict],
                           provider: str, asset_id_filter: str = None, limit: int = 0) -> Dict:
    """
    Dry-run 模式：打印将要调用的图片路径，不真正请求 API

    Args:
        case_id: Case ID
        assets: 所有资产列表
        needs_vision: 需要处理的资产列表
        provider: AI provider
        asset_id_filter: 如果指定了 asset_id 过滤
        limit: 限制数量
    """
    # 获取 model 名称
    model_name = "MiniMax-VL-01" if provider == "minimax" else provider.upper()

    lines = [
        "# Asset Description Report (Dry-Run)",
        "",
        f"**Case ID**: {case_id}",
        f"**生成时间**: {now_iso()}",
        "",
        "## ⚠️ Dry-Run 模式",
        "",
        "此为 dry-run 模式，**没有调用真实的 AI API**。",
        f"**Provider**: {provider}",
        f"**Model**: {model_name}",
        "",
    ]

    # 添加过滤信息
    if asset_id_filter:
        lines.append(f"**Asset Filter**: {asset_id_filter}")
    if limit > 0:
        lines.append(f"**Limit**: {limit}")
    if asset_id_filter or limit > 0:
        lines.append("")

    lines.extend([
        "## 将会处理的资产",
        "",
    ])

    valid_count = 0
    invalid_count = 0

    for asset in needs_vision:
        asset_id = asset["asset_id"]
        stored_path = asset.get("stored_path")
        path_exists = stored_path and Path(stored_path).exists()

        if path_exists:
            valid_count += 1
            lines.append(f"### ✅ {asset_id}")
            lines.append(f"- **路径**: `{stored_path}`")
            lines.append(f"- **类型**: {asset.get('asset_type', 'unknown')}")
            lines.append(f"- **页码**: {asset.get('page_number', 'N/A')}")
            lines.append("")
        else:
            invalid_count += 1
            lines.append(f"### ❌ {asset_id}")
            lines.append(f"- **路径**: `{stored_path}`")
            lines.append(f"- **问题**: 路径无效或文件不存在")
            lines.append("")

    lines.extend([
        "## 统计",
        "",
        f"- **总资产数**: {len(assets)}",
        f"- **需要视觉理解**: {len(needs_vision)}",
        f"- **有效处理**: {valid_count}",
        f"- **无效路径**: {invalid_count}",
        "",
        "## 下一步",
        "",
        "1. 确认路径正确后，去掉 --dry-run 参数运行真实 API",
        "2. 确保 MINIMAX_API_KEY 环境变量已设置",
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成（Dry-Run）*",
    ])

    report_path = Config.CASES_DIR / case_id / "asset_description_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "success": True,
        "message": f"Dry-Run 完成，找到 {valid_count} 个有效资产，{invalid_count} 个无效路径",
        "total_assets": len(assets),
        "needs_vision_count": len(needs_vision),
        "processed_count": valid_count,
        "failed_count": invalid_count,
        "dry_run": True,
        "report_path": str(report_path),
    }


def describe_assets_for_case(case_id: str, provider: str = "mock", dry_run: bool = False,
                            limit: int = 0, asset_id: str = None) -> Dict:
    """
    为 case 的资产生成视觉描述

    Args:
        case_id: Case ID
        provider: AI 提供商 (mock, minimax, openai, claude)
        dry_run: dry-run 模式，不真正调用 API
        limit: 最多处理 N 个资产（0=不限制）
        asset_id: 只处理指定 asset_id

    Returns:
        {
            "success": bool,
            "message": str,
            "total_assets": int,
            "needs_vision_count": int,
            "processed_count": int,
            "failed_count": int,
            "report_path": str,
            "dry_run": bool,
        }
    """
    # 加载 assets
    assets = load_assets(case_id)
    if assets is None:
        return {"success": False, "message": f"assets.json 不存在，请先运行 compile-case"}

    if not assets:
        return {"success": False, "message": f"没有需要处理的资产"}

    # 如果指定了 asset_id，先筛选
    if asset_id:
        target_asset = None
        for a in assets:
            if a.get("asset_id") == asset_id:
                target_asset = a
                break

        if target_asset is None:
            return {"success": False, "message": f"asset_id 不存在: {asset_id}"}

        # 检查是否可处理
        if not target_asset.get("needs_vision_review"):
            return {"success": False, "message": f"asset_id {asset_id} 不需要视觉理解（needs_vision_review=false）"}

        if target_asset.get("description_status") != "pending":
            return {"success": False, "message": f"asset_id {asset_id} 状态不是 pending（当前: {target_asset.get('description_status')}）"}

        if not target_asset.get("stored_path") or not Path(target_asset["stored_path"]).exists():
            return {"success": False, "message": f"asset_id {asset_id} 路径无效或文件不存在"}

        # 只处理这一个
        needs_vision = [target_asset]
        asset_id_filter = asset_id
    else:
        # 筛选需要视觉理解的资产
        needs_vision = [a for a in assets if a.get("needs_vision_review") and a.get("description_status") == "pending"]
        asset_id_filter = None

    needs_vision_count = len(needs_vision)

    if needs_vision_count == 0:
        return {
            "success": True,
            "message": "没有需要视觉理解的资产",
            "total_assets": len(assets),
            "needs_vision_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "dry_run": dry_run,
        }

    # 应用 limit
    if limit > 0:
        needs_vision = needs_vision[:limit]

    # dry-run 模式
    if dry_run:
        return describe_assets_dry_run(case_id, assets, needs_vision, provider, asset_id_filter, limit)

    # 创建 AI 客户端
    try:
        ai_client = create_ai_client(provider)
    except Exception as e:
        return {"success": False, "message": f"无法创建 AI 客户端: {str(e)}"}

    # 处理每个需要视觉理解的资产
    descriptions = []
    ai_fragments = []
    processed_count = 0
    failed_count = 0

    for asset in needs_vision:
        asset_id = asset["asset_id"]
        stored_path = asset.get("stored_path")

        if not stored_path or not Path(stored_path).exists():
            failed_count += 1
            asset["description_status"] = "invalid"
            descriptions.append({
                "asset_id": asset_id,
                "provider": provider,
                "status": "invalid",
                "error": "文件不存在或路径无效",
            })
            continue

        # 调用 AI
        result = ai_client.describe_image(stored_path)

        # 记录描述结果
        desc_record = {
            "asset_id": asset_id,
            "provider": provider,
            "model": result.get("model", "unknown"),
            "status": result.get("status", "error"),
            "description": result.get("description", ""),
            "detected_text": result.get("detected_text", ""),
            "visual_summary": result.get("visual_summary", ""),
            "layout_summary": result.get("layout_summary", ""),
            "style_keywords": result.get("style_keywords", []),
            "strategy_hint": result.get("strategy_hint", ""),
            "reusable_pattern": result.get("reusable_pattern", ""),
            "confidence": result.get("confidence", 0.0),
            "error": result.get("error"),
            "note": result.get("note"),
        }
        descriptions.append(desc_record)

        if result.get("status") == "success":
            processed_count += 1
            asset["description_status"] = "completed"
            asset["manual_description"] = result.get("visual_summary", "")
            # 生成 AI fragment
            if result.get("visual_summary"):
                ai_frag = generate_ai_fragment(asset_id, case_id, result, len(ai_fragments) + 1)
                ai_fragments.append(ai_frag)
        elif result.get("status") == "mock":
            processed_count += 1
            asset["description_status"] = "mock"
        else:
            failed_count += 1
            asset["description_status"] = "failed"
            asset["error_message"] = result.get("error", "unknown error")

    # 保存更新后的 assets
    save_assets(case_id, assets)

    # 保存 descriptions.json
    save_descriptions(case_id, descriptions)

    # 保存 ai_fragments.json
    if ai_fragments:
        save_ai_fragments(case_id, ai_fragments)

    # 生成报告
    report_path = Config.CASES_DIR / case_id / "asset_description_report.md"
    generate_description_report(case_id, len(assets), needs_vision_count,
                                 processed_count, failed_count, provider, report_path)

    return {
        "success": True,
        "message": f"描述生成完成",
        "total_assets": len(assets),
        "needs_vision_count": needs_vision_count,
        "processed_count": processed_count,
        "failed_count": failed_count,
        "report_path": str(report_path),
    }


def generate_description_report(case_id: str, total: int, needs_vision: int,
                                 processed: int, failed: int, provider: str, output_path: Path):
    """生成描述报告"""
    lines = [
        "# Asset Description Report",
        "",
        f"**Case ID**: {case_id}",
        f"**生成时间**: {now_iso()}",
        "",
        "## 统计",
        "",
        f"- **总资产数**: {total}",
        f"- **需要视觉理解**: {needs_vision}",
        f"- **已处理**: {processed}",
        f"- **失败**: {failed}",
        f"- **Provider**: {provider}",
        "",
    ]

    if provider == "mock":
        lines.extend([
            "## ⚠️ Mock 模式",
            "",
            "当前运行在 mock 模式下，**没有调用真实的 AI API**。",
            "生成的描述结果为空，仅用于测试流程。",
            "",
        ])

    lines.extend([
        "## 下一步",
        "",
        "1. 查看 `descriptions.json` 了解 AI 生成的描述",
        "2. 查看 `ai_fragments.json` 了解提取的 AI 内容片段",
        "3. 如需真实描述，请接入真实 API (claude 或 openai)",
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_ai_fragments_for_case(case_id: str) -> Dict:
    """
    从 descriptions.json 生成 ai_fragments.json

    处理 status 为 success / done / manual_done / mock 的条目。

    Returns:
        {
            "success": bool,
            "message": str,
            "fragments_count": int,
            "output_path": str,
        }
    """
    descriptions_path = Config.CASES_DIR / case_id / "descriptions.json"
    if not descriptions_path.exists():
        return {"success": False, "message": f"descriptions.json 不存在，请先运行 describe-assets"}

    with open(descriptions_path, "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    # 过滤有效条目
    valid_statuses = {"success", "done", "manual_done", "mock"}
    valid_descriptions = [d for d in descriptions if d.get("status") in valid_statuses]

    if not valid_descriptions:
        return {"success": False, "message": "没有有效的描述条目（status 非 success/done/manual_done/mock）"}

    # 生成 ai fragments
    ai_fragments = []
    for idx, desc in enumerate(valid_descriptions, 1):
        asset_id = desc.get("asset_id", "")
        confidence = desc.get("confidence", 0.0)

        # 拼接 raw_text
        raw_parts = []
        for field in ["detected_text", "visual_summary", "layout_summary", "strategy_hint", "reusable_pattern"]:
            val = desc.get(field, "")
            if val:
                if isinstance(val, list):
                    raw_parts.extend([v for v in val if v])
                elif isinstance(val, str) and val.strip():
                    raw_parts.append(val.strip())
        raw_text = " ".join(raw_parts)

        # summary: 优先用 visual_summary 或 strategy_hint
        summary = desc.get("visual_summary", "") or desc.get("strategy_hint", "") or raw_text[:200]

        # keywords: 从 style_keywords + detected_text 提取
        keywords = []
        style_kw = desc.get("style_keywords", [])
        if isinstance(style_kw, list):
            keywords.extend(style_kw)
        detected = desc.get("detected_text", [])
        if isinstance(detected, list):
            keywords.extend([t for t in detected if t and len(t) < 20])
        keywords = list(dict.fromkeys(keywords))[:10]  # 去重，保留最多10个

        # quality_flags
        quality_flags = ["vision_generated"]
        if confidence < 0.5:
            quality_flags.append("low_confidence")

        # 构建 fragment
        fragment = {
            "fragment_id": f"ai-{uuid.uuid4().hex[:8]}",
            "case_id": case_id,
            "fragment_type": "visual_analysis",
            "source_type": "mcp_image_understanding",
            "source_asset_id": asset_id,
            "source_page_id": None,  # descriptions.json 不包含 page_id
            "raw_text": raw_text,
            "summary": summary[:300] if len(summary) > 300 else summary,
            "keywords": keywords,
            "confidence": confidence,
            "quality_flags": quality_flags,
            "provider": desc.get("provider", ""),
            "model": desc.get("model", ""),
        }
        ai_fragments.append(fragment)

    # 保存
    output_path = Config.CASES_DIR / case_id / "ai_fragments.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ai_fragments, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "message": f"生成 {len(ai_fragments)} 个 ai fragments",
        "fragments_count": len(ai_fragments),
        "output_path": str(output_path),
    }