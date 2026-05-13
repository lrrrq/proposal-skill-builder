"""
parser - 文件读取与切分
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


# 支持的文件类型
SUPPORTED_EXTENSIONS = {".md", ".txt"}


def read_text_file(file_path: Path) -> str:
    """
    读取文本文件内容

    Returns:
        文件内容字符串

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不支持
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文本格式: {ext}，当前仅支持 .md 和 .txt")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def is_heading_line(line: str) -> bool:
    """判断是否是标题行"""
    line = line.strip()
    # # 标题 或 **标题** 或 数字.标题
    if line.startswith("#"):
        return True
    if line.startswith("**") and line.endswith("**"):
        return True
    if re.match(r"^\d+\.", line):
        return True
    return False


def split_by_paragraphs(text: str) -> List[Dict]:
    """
    将文本按段落切分

    Returns:
        [
            {
                "page_number": 1,
                "page_type": "title" | "content" | "section",
                "text_content": ["line1", "line2", ...],
                "raw_text": "完整原始文本"
            },
            ...
        ]
    """
    # 先按双换行分割成段落
    raw_paragraphs = re.split(r"\n\s*\n", text.strip())

    pages = []
    page_number = 0

    for para in raw_paragraphs:
        para = para.strip()
        if not para:
            continue

        lines = para.split("\n")
        cleaned_lines = [line.rstrip() for line in lines if line.strip()]

        if not cleaned_lines:
            continue

        page_number += 1

        # 判断段落类型
        first_line = cleaned_lines[0].strip()
        if is_heading_line(first_line):
            page_type = "title"
        elif page_number == 1 and len(cleaned_lines) < 5:
            page_type = "title"
        else:
            page_type = "content"

        pages.append({
            "page_number": page_number,
            "page_type": page_type,
            "text_content": cleaned_lines,
            "raw_text": para,
        })

    # 如果只有一个很短的段落，把它归类为 title
    if len(pages) == 1 and len(pages[0]["text_content"]) <= 3:
        pages[0]["page_type"] = "title"

    return pages


def parse_file(file_path: Path) -> List[Dict]:
    """
    解析文件并返回切分后的页面

    Returns:
        pages 列表
    """
    content = read_text_file(file_path)
    return split_by_paragraphs(content)