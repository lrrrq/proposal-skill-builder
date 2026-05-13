"""
publisher - Skill 发布模块
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .config import Config
from .skill_checker import check_skill
from .utils import now_iso


def load_registry() -> Dict:
    """加载 registry"""
    registry_path = Config.SKILL_REGISTRY_JSON

    if registry_path.exists():
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    return {
        "skills": [],
        "updated_at": None,
    }


def save_registry(registry: Dict) -> None:
    """原子化保存 registry"""
    registry_path = Config.SKILL_REGISTRY_JSON
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    registry["updated_at"] = now_iso()

    tmp_path = str(registry_path) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, registry_path)


def create_backup(skill_id: str) -> Optional[str]:
    """如果 skills/published/<skill_id> 已存在，创建备份"""
    published_dir = Config.PUBLISHED_DIR / skill_id

    if not published_dir.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Config.PUBLISHED_DIR / f"{skill_id}__backup_{timestamp}"

    try:
        shutil.copytree(published_dir, backup_dir)
        return str(backup_dir)
    except Exception:
        return None


def publish_skill(skill_id: str) -> Dict:
    """
    发布 Skill

    Args:
        skill_id: Skill ID

    Returns:
        {
            "success": bool,
            "message": str,
            "backup_path": str or None,
            "published_path": str or None,
            "report_path": str or None,
        }
    """
    # 检查 draft 是否存在
    draft_dir = Config.DRAFT_DIR / skill_id
    if not draft_dir.exists():
        return {"success": False, "message": f"Draft Skill 不存在: {skill_id}"}

    # 检查必需文件
    required_files = ["SKILL.md", "skill.json", "examples.md"]
    for fname in required_files:
        if not (draft_dir / fname).exists():
            return {"success": False, "message": f"缺少必需文件: {fname}"}

    # 运行 check-skill
    check_result = check_skill(skill_id)
    if not check_result["success"]:
        return {"success": False, "message": f"检查失败: {check_result.get('message')}"}

    # 检查是否有真正失败项（阻塞发布）
    if check_result.get("failed_count", 0) > 0:
        failed_items = check_result.get("failed_items", [])
        return {
            "success": False,
            "message": f"检查存在失败项，禁止发布",
            "failed_items": failed_items,
        }

    # 检查是否是 failed 等级
    if check_result.get("suggested_level") == "failed":
        return {"success": False, "message": "质量等级为 failed，禁止发布"}

    # 检查分数是否低于 60
    if check_result.get("score", 0) < 60:
        return {"success": False, "message": f"分数 {check_result['score']} < 60，禁止发布"}

    # 创建备份（如果已存在）
    backup_path = create_backup(skill_id)

    # 复制到 published 目录
    published_dir = Config.PUBLISHED_DIR / skill_id
    published_dir.mkdir(parents=True, exist_ok=True)

    # 复制文件
    for fname in required_files:
        src = draft_dir / fname
        dst = published_dir / fname
        shutil.copy2(src, dst)

    # 修改 published skill.json
    skill_json_path = published_dir / "skill.json"
    with open(skill_json_path, "r", encoding="utf-8") as f:
        skill_json = json.load(f)

    # 更新字段
    skill_json["status"] = "published"
    skill_json["callable"] = True
    skill_json["published_at"] = now_iso()
    skill_json["source_path"] = str(draft_dir)
    skill_json["published_path"] = str(published_dir)

    # 保存
    with open(skill_json_path, "w", encoding="utf-8") as f:
        json.dump(skill_json, f, ensure_ascii=False, indent=2)

    # 更新 draft skill.json 的 status
    draft_skill_json_path = draft_dir / "skill.json"
    with open(draft_skill_json_path, "r", encoding="utf-8") as f:
        draft_skill_json = json.load(f)
    draft_skill_json["status"] = "published"
    draft_skill_json["published_at"] = now_iso()
    with open(draft_skill_json_path, "w", encoding="utf-8") as f:
        json.dump(draft_skill_json, f, ensure_ascii=False, indent=2)

    # 更新 registry
    registry = load_registry()

    # 检查是否已存在，存在则更新
    skill_exists = False
    for i, s in enumerate(registry["skills"]):
        if s.get("skill_id") == skill_id:
            registry["skills"][i] = {
                "skill_id": skill_id,
                "display_name": skill_json.get("display_name", skill_id),
                "status": "published",
                "quality_level": skill_json.get("quality_level", "unknown"),
                "callable": True,
                "path": str(published_dir),
                "source_cases": skill_json.get("source_cases", []),
                "source_strategies": skill_json.get("source_strategies", []),
                "allowed_tasks": skill_json.get("allowed_tasks", []),
                "published_at": skill_json.get("published_at"),
            }
            skill_exists = True
            break

    if not skill_exists:
        registry["skills"].append({
            "skill_id": skill_id,
            "display_name": skill_json.get("display_name", skill_id),
            "status": "published",
            "quality_level": skill_json.get("quality_level", "unknown"),
            "callable": True,
            "path": str(published_dir),
            "source_cases": skill_json.get("source_cases", []),
            "source_strategies": skill_json.get("source_strategies", []),
            "allowed_tasks": skill_json.get("allowed_tasks", []),
            "published_at": skill_json.get("published_at"),
        })

    save_registry(registry)

    # 生成发布报告
    warnings = check_result.get("warnings", [])
    risk_items = check_result.get("risk_items", [])

    report_lines = [
        f"# Publish Report: {skill_id}",
        "",
        f"**发布时间**: {now_iso()}",
        "",
        "---",
        "",
        "## 基本信息",
        "",
        f"- **skill_id**: {skill_id}",
        f"- **display_name**: {skill_json.get('display_name', skill_id)}",
        f"- **quality_level**: {skill_json.get('quality_level', 'unknown')}",
        f"- **score**: {check_result.get('score', 0)}/100",
        f"- **source_cases**: {len(skill_json.get('source_cases', []))}",
        f"- **source_strategies**: {len(skill_json.get('source_strategies', []))}",
        "",
    ]

    if backup_path:
        report_lines.append(f"**备份**: {backup_path}")

    report_lines.extend([
        "## 检查结果",
        "",
        f"- **通过项**: {check_result.get('passed_count', 0)}",
        f"- **失败项**: {check_result.get('failed_count', 0)}",
        f"- **警告项**: {check_result.get('warnings_count', 0)}",
        "",
    ])

    if warnings:
        report_lines.extend([
            "## ⚠️ 警告项",
            "",
        ])
        for w in warnings:
            report_lines.append(f"- {w}")
        report_lines.append("")

    if risk_items:
        report_lines.extend([
            "## ⚠️ 风险项",
            "",
        ])
        for r in risk_items:
            report_lines.append(f"- {r}")
        report_lines.append("")

    report_lines.extend([
        "## 📋 发布建议",
        "",
        f"✅ **{check_result.get('suggested_level', 'unknown')}**（评分: {check_result.get('score', 0)}）",
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    report_path = Config.REPORTS_DIR / f"publish_{skill_id}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "success": True,
        "message": "发布成功",
        "backup_path": backup_path,
        "published_path": str(published_dir),
        "report_path": str(report_path),
        "warnings": warnings,
        "risk_items": risk_items,
    }


def inspect_registry() -> Dict:
    """
    检查 registry 健康度

    Returns:
        {
            "success": bool,
            "message": str,
            "skills_count": int,
            "registry_path": str,
            "updated_at": str or None,
            "skills": list,
            "issues": list,
        }
    """
    registry_path = Config.SKILL_REGISTRY_JSON

    if not registry_path.exists():
        return {
            "success": True,
            "message": "registry 文件不存在",
            "skills_count": 0,
            "registry_path": str(registry_path),
            "updated_at": None,
            "skills": [],
            "issues": [],
        }

    registry = load_registry()
    skills = registry.get("skills", [])
    updated_at = registry.get("updated_at")

    issues = []
    skill_list = []

    for s in skills:
        skill_id = s.get("skill_id", "unknown")
        path = s.get("path", "")

        # 检查 path 是否指向 draft
        if "draft" in path:
            issues.append(f"[非法] {skill_id}: path 指向 draft（{path}）")

        # 检查 callable
        if not s.get("callable", False):
            issues.append(f"[非法] {skill_id}: callable=false")

        # 检查 status
        if s.get("status") != "published":
            issues.append(f"[非法] {skill_id}: status={s.get('status')}（应为 published）")

        # 检查 path 是否存在
        if path and not Path(path).exists():
            issues.append(f"[警告] {skill_id}: path 不存在（{path}）")

        skill_list.append({
            "skill_id": skill_id,
            "display_name": s.get("display_name", skill_id),
            "quality_level": s.get("quality_level", "unknown"),
            "callable": s.get("callable", False),
            "path": path,
            "source_cases": s.get("source_cases", []),
            "source_strategies": s.get("source_strategies", []),
        })

    return {
        "success": True,
        "message": f"registry 包含 {len(skills)} 个 skills",
        "skills_count": len(skills),
        "registry_path": str(registry_path),
        "updated_at": updated_at,
        "skills": skill_list,
        "issues": issues,
    }