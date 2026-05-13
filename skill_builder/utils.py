"""
工具函数
"""

import hashlib
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def now_iso() -> str:
    """返回当前时间的 ISO 格式字符串"""
    return datetime.now().isoformat()


def calculate_sha256(filepath: Path) -> str:
    """计算文件的 SHA256"""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def guess_mime_type(filepath: Path) -> str:
    """根据扩展名猜测 MIME 类型"""
    from .config import Config
    ext = filepath.suffix.lower()
    return Config.MIME_TYPES.get(ext, "application/octet-stream")


def safe_move_file(src: Path, dest_dir: Path, add_uuid_suffix: bool = True) -> Path:
    """
    安全移动文件到目标目录，避免重名覆盖

    Args:
        src: 源文件路径
        dest_dir: 目标目录
        add_uuid_suffix: 遇到重名时是否添加短 UUID 后缀

    Returns:
        实际保存的目标路径
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / src.name

    if dest_path.exists():
        if add_uuid_suffix:
            # 添加短 UUID 后缀
            uid = uuid.uuid4().hex[:6]
            stem = dest_path.stem
            suffix = dest_path.suffix
            dest_path = dest_dir / f"{stem}_{uid}{suffix}"
        else:
            # 覆盖（不推荐）
            pass

    shutil.move(str(src), str(dest_path))
    return dest_path


def generate_file_id() -> str:
    """生成短文件 ID"""
    return uuid.uuid4().hex[:12]