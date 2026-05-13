"""
数据模型 - 数据结构和验证
"""

import uuid
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from pathlib import Path


@dataclass
class SourceFile:
    """策划案源文件"""
    file_id: str
    original_filename: str
    current_path: str
    sha256: str
    file_size: int
    mime_type: str
    status: str = "staging"
    error_message: Optional[str] = None

    @classmethod
    def create(cls, filepath: Path) -> "SourceFile":
        """从文件路径创建 SourceFile"""
        file_id = uuid.uuid4().hex[:12]
        original_filename = filepath.name
        current_path = str(filepath)

        # 计算 SHA256
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        sha256 = hasher.hexdigest()

        # 文件大小
        file_size = filepath.stat().st_size

        # MIME 类型
        from .config import Config
        ext = filepath.suffix.lower()
        mime_type = Config.MIME_TYPES.get(ext, "application/octet-stream")

        return cls(
            file_id=file_id,
            original_filename=original_filename,
            current_path=current_path,
            sha256=sha256,
            file_size=file_size,
            mime_type=mime_type,
        )


@dataclass
class Case:
    """案例"""
    case_id: str
    title: Optional[str] = None
    status: str = "draft"

    @classmethod
    def create(cls, title: Optional[str] = None) -> "Case":
        case_id = f"case-{uuid.uuid4().hex[:8]}"
        return cls(case_id=case_id, title=title)


@dataclass
class Job:
    """任务"""
    job_id: str
    case_id: Optional[str]
    stage: str
    status: str = "pending"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def create(cls, case_id: str, stage: str) -> "Job":
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        return cls(job_id=job_id, case_id=case_id, stage=stage)


@dataclass
class Skill:
    """Skill"""
    skill_id: str
    display_name: Optional[str] = None
    status: str = "draft"
    quality_level: str = "bronze"
    callable: int = 0

    @classmethod
    def create(cls, name: str) -> "Skill":
        skill_id = name.lower().replace(" ", "-")
        return cls(skill_id=skill_id, display_name=name)