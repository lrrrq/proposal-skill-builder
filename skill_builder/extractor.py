"""
extractor - fragment 构造
"""

import re
from collections import Counter
from typing import List, Dict
from pathlib import Path

import uuid


def generate_fragment_id() -> str:
    """生成短 fragment ID"""
    return uuid.uuid4().hex[:12]


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    简单关键词提取：
    - 统计词频（过滤停用词）
    - 返回 top_n 高频词
    """
    # 停用词
    stopwords = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "来",
        "对", "把", "他", "她", "它", "们", "为", "而", "但", "与",
        "或", "以", "及", "等", "之", "于", "被", "给", "让", "从",
        "用", "所", "后", "前", "中", "下", "可以", "能", "还", "更",
        "这个", "那个", "什么", "怎么", "如何", "为什么", "因为",
        "如果", "虽然", "但是", "然后", "所以", "因此", "于是",
        "以及", "或者", "并且", "而且", "不过", "只是", "否则",
    }

    # 简单分词（按非字母数字分割）
    words = re.findall(r"[\w一-鿿]{2,}", text)

    # 过滤停用词和单字
    filtered = [w for w in words if w.lower() not in stopwords and len(w) >= 2]

    if not filtered:
        return []

    # 统计词频
    counter = Counter(filtered)
    return [word for word, count in counter.most_common(top_n)]


def make_summary(text: str, max_length: int = 120) -> str:
    """
    简单摘要：
    - 取前 max_length 个字符
    - 结尾加 ...
    """
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def determine_fragment_type(page_type: str, text_length: int) -> str:
    """判断 fragment 类型"""
    if page_type == "title":
        return "title"
    if text_length < 50:
        return "empty"
    if text_length < 200:
        return "short"
    return "normal"


def build_fragment(fragment_id: str, case_id: str, index: int, page: Dict) -> Dict:
    """构建 fragment 对象"""
    raw_text = page.get("raw_text", "")
    text_length = len(raw_text.strip())

    fragment_type = determine_fragment_type(page.get("page_type", "content"), text_length)

    # 构建 summary
    if text_length > 0:
        summary = make_summary(raw_text)
    else:
        summary = ""

    # 提取 keywords
    if text_length > 10:
        keywords = extract_keywords(raw_text)
    else:
        keywords = []

    # quality_flags
    quality_flags = []
    if fragment_type == "empty":
        quality_flags.append("empty")
    elif fragment_type == "short":
        quality_flags.append("too_short")
    else:
        quality_flags.append("normal")

    return {
        "fragment_id": fragment_id,
        "case_id": case_id,
        "index": index,
        "fragment_type": fragment_type,
        "raw_text": raw_text,
        "summary": summary,
        "keywords": keywords,
        "quality_flags": quality_flags,
    }


def extract_fragments(case_id: str, pages: List[Dict]) -> List[Dict]:
    """
    从 pages 列表提取 fragments

    Returns:
        fragments 列表
    """
    fragments = []

    for i, page in enumerate(pages, 1):
        fragment_id = generate_fragment_id()
        fragment = build_fragment(fragment_id, case_id, i, page)
        fragments.append(fragment)

    return fragments