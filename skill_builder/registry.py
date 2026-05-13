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
        """加载注册表"""
        self.ensure_registry_file()
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

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

    def list_skills(self) -> List[dict]:
        """列出所有 Skills"""
        registry = self.load_registry()
        return registry.get("skills", [])

    def search(self, query: str = "", **filters) -> List[dict]:
        """搜索 Skills"""
        registry = self.load_registry()
        results = []

        for skill in registry.get("skills", []):
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