"""
quality_checker - 质量检查
"""

from typing import List, Dict

from .config import Config
from .db import get_cursor


class QualityChecker:
    """质量检查器"""

    QUALITY_LEVELS = ["bronze", "silver", "gold"]

    def __init__(self):
        pass

    def check_skill(self, skill_path: Path) -> Dict:
        """
        检查 Skill 质量

        Returns:
            {
                "passed": bool,
                "level": str,
                "issues": List[str],
                "warnings": List[str]
            }
        """
        issues = []
        warnings = []

        # 检查必要文件
        skill_json = skill_path / "skill.json"
        skill_md = skill_path / "SKILL.md"

        if not skill_json.exists():
            issues.append("缺少 skill.json")
        if not skill_md.exists():
            warnings.append("缺少 SKILL.md")

        # 确定级别
        if issues:
            level = "rejected"
        elif warnings:
            level = "bronze"
        else:
            level = "bronze"  # 默认 bronze

        return {
            "passed": len(issues) == 0,
            "level": level,
            "issues": issues,
            "warnings": warnings,
        }

    def check_all_draft_skills(self) -> List[Dict]:
        """检查所有 draft Skills"""
        results = []

        if not Config.DRAFT_DIR.exists():
            return results

        for skill_dir in Config.DRAFT_DIR.iterdir():
            if skill_dir.is_dir():
                result = self.check_skill(skill_dir)
                result["skill_id"] = skill_dir.name
                results.append(result)

        return results

    def auto_promote_eligible(self) -> int:
        """
        自动提升符合条件的 Skills

        Returns:
            提升的数量
        """
        promoted = 0

        # bronze -> silver: 有完整的 skill.json 和 SKILL.md
        # 这个逻辑后续可以扩展
        with get_cursor() as cur:
            cur.execute("""
                SELECT skill_id FROM skills
                WHERE status = 'draft' AND quality_level = 'bronze'
            """)
            for row in cur.fetchall():
                # 简化：所有 bronze draft 都保持原样
                pass

        return promoted