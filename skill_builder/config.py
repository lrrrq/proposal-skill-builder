"""
配置 - 所有路径集中管理
"""

from pathlib import Path
import os


class Config:
    """项目配置"""

    # 项目根目录（向上找有 skill_builder 或 pyproject.toml 的目录）
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    # 源码目录
    SKILL_BUILDER_DIR = PROJECT_ROOT / "skill_builder"

    # 策划案源目录
    SOURCE_PROPOSALS_DIR = PROJECT_ROOT / "source_proposals"
    STAGING_DIR = SOURCE_PROPOSALS_DIR / "staging"
    ACCEPTED_DIR = SOURCE_PROPOSALS_DIR / "accepted"
    DUPLICATES_DIR = SOURCE_PROPOSALS_DIR / "duplicates"
    REJECTED_DIR = SOURCE_PROPOSALS_DIR / "rejected"
    ARCHIVED_DIR = SOURCE_PROPOSALS_DIR / "archived"

    # 数据目录
    DATA_DIR = PROJECT_ROOT / "data"
    DB_PATH = DATA_DIR / "skill_builder.db"

    # 编译输出
    COMPILED_DIR = PROJECT_ROOT / "compiled"
    CASES_DIR = COMPILED_DIR / "cases"

    # 知识库
    KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
    CASE_CARDS_DIR = KNOWLEDGE_DIR / "case_cards"

    # Skill 仓库
    SKILLS_DIR = PROJECT_ROOT / "skills"
    DRAFT_DIR = SKILLS_DIR / "draft"
    PUBLISHED_DIR = SKILLS_DIR / "published"
    QUARANTINE_DIR = SKILLS_DIR / "quarantine"

    # 注册表
    REGISTRY_DIR = PROJECT_ROOT / "registry"
    SKILL_REGISTRY_JSON = REGISTRY_DIR / "skill_registry.json"

    # 输出
    OUTPUTS_DIR = PROJECT_ROOT / "outputs"

    # 报告
    REPORTS_DIR = PROJECT_ROOT / "reports"

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {".pptx", ".pdf", ".docx", ".doc"}

    # MIME 类型映射
    MIME_TYPES = {
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }

    @classmethod
    def all_dirs(cls):
        """所有需要创建的目录"""
        return [
            cls.STAGING_DIR,
            cls.ACCEPTED_DIR,
            cls.DUPLICATES_DIR,
            cls.REJECTED_DIR,
            cls.ARCHIVED_DIR,
            cls.DATA_DIR,
            cls.CASES_DIR,
            cls.CASE_CARDS_DIR,
            cls.DRAFT_DIR,
            cls.PUBLISHED_DIR,
            cls.QUARANTINE_DIR,
            cls.REGISTRY_DIR,
            cls.OUTPUTS_DIR,
            cls.REPORTS_DIR,
        ]