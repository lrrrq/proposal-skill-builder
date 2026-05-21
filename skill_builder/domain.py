"""domain.py - Centralized domain constants"""

# Pattern Types
PATTERN_TYPES = {
    # Chinese + English keywords for bilingual support
    "strategy": ["目标", "目的", "策略", "定位", "核心", "价值", "品牌", "差异化", "优势",
                "strategy", "objective", "goal", "positioning", "core", "value", "brand", "advantage"],
    "content_structure": ["目录", "流程", "章节", "结构", "框架", "模块", "层次", "逻辑",
                         "contents", "toc", "outline", "structure", "chapter", "section", "flow"],
    "visual_direction": ["视觉", "风格", "画面", "色彩", "设计", "图形", "排版", "字体", "色调",
                         "visual", "style", "design", "color", "layout", "typography", "aesthetic"],
    "audience_insight": ["用户", "客户", "人群", "受众", "会员", "消费者", "目标群体", "画像",
                         "audience", "user", "customer", "consumer", "target", "demographic"],
    "execution_method": ["执行", "落地", "排期", "预算", "物料", "实施", "步骤", "时间节点", "资源",
                        "execution", "timeline", "budget", "deliverable", "schedule", "step"],
}

# Strategy Types
STRATEGY_TYPES = {
    "positioning_strategy": ["定位", "品牌", "差异化", "核心价值", "竞争优势", "战略",
                             "positioning", "brand", "differentiation", "advantage"],
    "audience_strategy": ["用户", "客户", "受众", "人群", "会员", "消费者", "目标群体", "画像",
                         "audience", "user", "customer", "consumer", "target"],
    "narrative_strategy": ["叙事", "故事", "内容", "结构", "章节", "节奏", "弧线", "线索",
                          "narrative", "story", "content", "structure", "rhythm"],
    "visual_strategy": ["视觉", "风格", "画面", "色彩", "设计", "图形", "排版", "色调", "留白",
                       "visual", "style", "color", "design", "layout", "aesthetic"],
    "execution_strategy": ["执行", "落地", "排期", "预算", "物料", "实施", "步骤", "时间节点",
                          "execution", "timeline", "budget", "schedule"],
    "conversion_strategy": ["转化", "传播", "会员", "销售", "报名", "邀约", "注册", "购买", "成交",
                           "conversion", "sales", "registration", "purchase"],
}

# Pattern to Strategy mapping
PATTERN_TO_STRATEGY = {
    "strategy": "positioning_strategy",
    "content_structure": "narrative_strategy",
    "visual_direction": "visual_strategy",
    "audience_insight": "audience_strategy",
    "execution_method": "execution_strategy",
}

# Quality Flags
QUALITY_FLAGS = {
    "too_short": "文本过短（<20字符）",
    "duplicate": "重复内容",
    "low_information": "低信息密度",
    "normal": "正常质量",
    "merged": "多个 fragment 合并",
    "vision_only": "纯视觉来源",
    "text_only": "纯文本来源",
}

# Skill JSON required fields
REQUIRED_SKILL_JSON_FIELDS = [
    "skill_id", "display_name", "description", "status", "dataset",
    "quality_level", "callable", "source_cases", "source_patterns",
    "source_fragments_count", "source_ai_fragments_count", "allowed_tasks",
    "created_at", "updated_at", "version",
]

# Skill MD required sections
REQUIRED_SKILL_MD_SECTIONS = [
    "适用场景", "输入要求", "核心判断逻辑", "处理流程", "输出格式",
    "可复用策略", "视觉策略", "内容结构策略", "受众洞察", "执行方法",
    "限制条件", "来源案例",
]