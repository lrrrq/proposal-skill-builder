"""
registry - Skill 注册表管理
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .config import Config
from .db import get_cursor


class SkillRegistry:
    """Skill 注册表"""

    def __init__(self):
        self.registry_path = Config.SKILL_REGISTRY_JSON

    def ensure_registry_file(self):
        """确保注册表 JSON 文件存在"""
        if not self.registry_path.exists():
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            self.save_registry({"skills": [], "updated_at": datetime.now().isoformat()})

    def load_registry(self) -> dict:
        """加载注册表，带格式校验和错误处理"""
        self.ensure_registry_file()
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"registry 文件格式错误或无法读取: {e}")

        # 确保必需字段存在且类型正确
        if not isinstance(data, dict):
            raise ValueError(f"registry 根对象必须是 dict，实际为 {type(data).__name__}")

        # skills 字段校验：不存在或为 None 时使用空列表
        if "skills" not in data or data["skills"] is None:
            data["skills"] = []
        elif not isinstance(data["skills"], list):
            raise ValueError(f"registry['skills'] 必须是 list，实际为 {type(data['skills']).__name__}")

        return data

    def save_registry(self, data: dict):
        """保存注册表"""
        data["updated_at"] = datetime.now().isoformat()
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_skill(self, skill_data: dict) -> str:
        """添加或更新 Skill"""
        registry = self.load_registry()
        if registry["skills"] is None:
            registry["skills"] = []

        skill_id = skill_data.get("skill_id")
        for i, existing in enumerate(registry["skills"]):
            if existing.get("skill_id") == skill_id:
                registry["skills"][i] = skill_data
                self.save_registry(registry)
                return skill_id

        registry["skills"].append(skill_data)
        self.save_registry(registry)
        return skill_id

    def remove_skill(self, skill_id: str) -> bool:
        """移除 Skill"""
        registry = self.load_registry()
        original_len = len(registry["skills"])
        registry["skills"] = [s for s in registry["skills"] if s.get("skill_id") != skill_id]

        if len(registry["skills"]) < original_len:
            self.save_registry(registry)
            return True
        return False

    def get_skill(self, skill_id: str) -> Optional[dict]:
        """获取 Skill"""
        registry = self.load_registry()
        for skill in registry.get("skills", []):
            if skill.get("skill_id") == skill_id:
                return skill
        return None

    def list_skills(self, callable_only: bool = False) -> List[dict]:
        """
        列出所有 Skills

        Args:
            callable_only: 如果为 True，只返回 callable=True 且 status=published 的 Skills
        """
        registry = self.load_registry()
        skills = registry.get("skills", [])

        if callable_only:
            skills = [s for s in skills if s.get("callable") is True and s.get("status") == "published"]

        return skills

    def list_callable_skills(self) -> List[dict]:
        """只返回 callable=True 且 status=published 的 Skills（供 OpenClaw 使用）"""
        return self.list_skills(callable_only=True)

    def search(self, query: str = "", callable_only: bool = False, **filters) -> List[dict]:
        """
        搜索 Skills

        Args:
            query: 关键词匹配（搜索整个 JSON）
            callable_only: 如果为 True，只返回 callable=True 且 status=published 的 Skills
            **filters: 其他字段过滤器
        """
        registry = self.load_registry()
        results = []

        for skill in registry.get("skills", []):
            # OpenClaw 治理：只返回正式发布的 Skills
            if callable_only:
                if skill.get("callable") is not True or skill.get("status") != "published":
                    continue

            # 关键词匹配
            if query:
                searchable = json.dumps(skill, ensure_ascii=False).lower()
                if query.lower() not in searchable:
                    continue

            # 过滤器
            match = True
            for key, value in filters.items():
                if key not in skill:
                    match = False
                    break
                if isinstance(value, list):
                    if not any(v in skill[key] for v in value):
                        match = False
                        break
                elif skill[key] != value:
                    match = False
                    break

            if match:
                results.append(skill)

        return results

    def get_best_version(self, skill_id: str) -> Optional[dict]:
        """
        获取同一 skill_id 的最高版本

        如果有多个版本，选择 published_at 最新的那个。
        只考虑 status=published 的版本。
        """
        registry = self.load_registry()
        candidates = [
            s for s in registry.get("skills", [])
            if s.get("skill_id") == skill_id and s.get("status") == "published"
        ]

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        # 按 published_at 降序，选择最新
        best = max(candidates, key=lambda s: s.get("published_at", ""))
        return best

    def repair_registry(self) -> dict:
        """
        修复 filesystem 和 JSON registry 之间的 drift

        - 发现 filesystem (skills/published/) 中存在但 JSON registry 中不存在的 skill → 添加
        - 发现 JSON registry 中存在但 filesystem 中不存在的 skill → 移除

        Returns:
            {
                "success": bool,
                "added": list,      # 新增到 registry 的 skill_id 列表
                "removed": list,    # 从 registry 移除的 skill_id 列表
                "message": str,
            }
        """
        from .config import Config

        registry = self.load_registry()
        registry_skills = registry.get("skills", [])

        # 获取 filesystem 中 published skills (排除 backup 目录)
        filesystem_skill_ids = set()
        if Config.PUBLISHED_DIR.exists():
            for item in Config.PUBLISHED_DIR.iterdir():
                if item.is_dir() and "__backup_" not in item.name:
                    skill_json_path = item / "skill.json"
                    if skill_json_path.exists():
                        filesystem_skill_ids.add(item.name)

        # 获取 registry 中的 skill_ids
        registry_skill_ids = set(s.get("skill_id") for s in registry_skills if s.get("skill_id"))

        # 计算 drift
        to_add = filesystem_skill_ids - registry_skill_ids  # 在 fs 但不在 registry
        to_remove = registry_skill_ids - filesystem_skill_ids  # 在 registry 但不在 fs

        added = []
        removed = []

        # 添加 filesystem 中存在但 registry 中不存在的 skills
        for skill_id in to_add:
            skill_json_path = Config.PUBLISHED_DIR / skill_id / "skill.json"
            try:
                with open(skill_json_path, "r", encoding="utf-8") as f:
                    skill_json = json.load(f)

                skill_data = {
                    "skill_id": skill_id,
                    "display_name": skill_json.get("display_name", skill_id),
                    "status": skill_json.get("status", "published"),
                    "quality_level": skill_json.get("quality_level", "unknown"),
                    "callable": skill_json.get("callable", True),
                    "path": str(Config.PUBLISHED_DIR / skill_id),
                    "source_cases": skill_json.get("source_cases", []),
                    "source_strategies": skill_json.get("source_strategies", []),
                    "allowed_tasks": skill_json.get("allowed_tasks", []),
                    "published_at": skill_json.get("published_at"),
                }
                registry["skills"].append(skill_data)
                added.append(skill_id)
            except (json.JSONDecodeError, IOError):
                pass

        # 移除 registry 中存在但 filesystem 中不存在的 skills
        for skill_id in to_remove:
            registry["skills"] = [s for s in registry["skills"] if s.get("skill_id") != skill_id]
            removed.append(skill_id)

        # 保存更新后的 registry
        if added or removed:
            self.save_registry(registry)

        return {
            "success": True,
            "added": sorted(added),
            "removed": sorted(removed),
            "message": f"added {len(added)}, removed {len(removed)}",
        }


def get_registry():
    """获取注册表实例"""
    return SkillRegistry()


def create_case_card(skill_data: dict, output_dir: Path = None) -> Path:
    """创建 Case Card"""
    if output_dir is None:
        output_dir = Config.CASE_CARDS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)
    skill_id = skill_data.get("skill_id", "unknown")
    card_path = output_dir / f"{skill_id}.md"

    lines = [
        f"# Case Card: {skill_data.get('display_name', skill_id)}",
        "",
        f"**Skill ID**: `{skill_id}`",
        f"**状态**: {skill_data.get('status', 'draft')}",
        f"**质量级别**: {skill_data.get('quality_level', 'bronze')}",
        f"**可调用**: {'是' if skill_data.get('callable') else '否'}",
        "",
        "---",
        "",
        "## 基本信息",
        "",
    ]

    # 输出所有字段
    for key, value in skill_data.items():
        if key not in ["skill_id", "display_name", "status", "quality_level", "callable"]:
            if isinstance(value, list):
                lines.append(f"**{key}**:")
                for v in value:
                    lines.append(f"- {v}")
            elif isinstance(value, dict):
                lines.append(f"**{key}**:")
                for k, v in value.items():
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"**{key}**: {value}")

    lines.extend([
        "",
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    card_path.write_text("\n".join(lines), encoding="utf-8")
    return card_path