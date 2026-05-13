"""
ai_client - AI API 客户端接口
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path


class AIClient(ABC):
    """AI 客户端抽象接口"""

    @abstractmethod
    def describe_image(self, image_path: str, prompt: str = None) -> dict:
        raise NotImplementedError


class MockAIClient(AIClient):
    """Mock AI 客户端（不调用真实 API）"""

    def describe_image(self, image_path: str, prompt: str = None) -> dict:
        return {
            "description": "",
            "detected_text": "",
            "visual_summary": "",
            "layout_summary": "",
            "confidence": 0.0,
            "status": "mock",
            "error": None,
            "note": "当前为 mock 模式，未调用真实 AI API",
        }


# ========== Vision Analysis Prompt ==========

PROMPT_VISION_ANALYSIS = """请分析这张策划案页面或设计稿，输出严格 JSON：
1. detected_text：页面中可读文字
2. visual_summary：画面内容摘要
3. layout_summary：版式结构
4. style_keywords：视觉风格关键词
5. strategy_hint：这页可能承担的策划功能
6. reusable_pattern：可复用的方法论
7. confidence：0 到 1

要求：
不要编造看不见的内容。
无法识别时返回空字符串或 unknown。
输出必须是 JSON。"""


class MiniMaxTextClient(AIClient):
    """
    MiniMax Token Plan 文本客户端

    通过 OpenAI-Compatible 端点调用 MiniMax-M2.7 文本模型。
    只处理文本任务，不处理图片。
    """

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("MINIMAX_TOKEN_PLAN_KEY", "")
        self.base_url = base_url or os.environ.get("MINIMAX_TEXT_BASE_URL", "https://api.minimaxi.com/v1")
        self.model = model or os.environ.get("MINIMAX_TEXT_MODEL", "MiniMax-M2.7")
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            return
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            pass

    def describe_image(self, image_path: str, prompt: str = None) -> dict:
        return self._error_result(
            "MiniMax-Text 客户端不能处理图片。"
            "请使用 minimax-mcp provider 进行图片理解。"
        )

    def text_complete(self, prompt: str, max_tokens: int = 1024) -> dict:
        if not self.client:
            return {"success": False, "text": "", "error": "API 未初始化"}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content if response.choices else ""
            return {"success": True, "text": text, "error": None}
        except Exception as e:
            return {"success": False, "text": "", "error": str(e)}

    def ping(self) -> dict:
        if not self.client:
            return {"success": False, "message": "API 未初始化"}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "回复 OK"}],
                max_tokens=10,
            )
            text = response.choices[0].message.content if response.choices else ""
            if "OK" in text:
                return {"success": True, "message": "API 连接正常"}
            return {"success": False, "message": f"Unexpected response: {text}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _error_result(self, error_msg: str) -> dict:
        return {
            "description": "",
            "detected_text": "",
            "visual_summary": "",
            "layout_summary": "",
            "style_keywords": [],
            "strategy_hint": "",
            "reusable_pattern": "",
            "confidence": 0.0,
            "status": "error",
            "error": error_msg,
            "model": self.model,
        }


class MiniMaxMCPClient(AIClient):
    """
    MiniMax Token Plan 图片理解客户端

    直接调用 MiniMax VLM API 端点 /v1/coding_plan/vlm
    Token Plan Key 可以直接使用，不需要 uvx 或 MCP 服务启动

    环境变量：
      MINIMAX_TOKEN_PLAN_KEY：Token Plan 专属 Key
      MINIMAX_API_HOST：API 主机（默认 https://api.minimaxi.com）
    """

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("MINIMAX_TOKEN_PLAN_KEY", "")
        self.base_url = base_url or os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com")
        self.session = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            return
        try:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        except ImportError:
            pass

    def check_environment(self) -> dict:
        return {
            "key_exists": bool(self.api_key),
            "can_process_images": bool(self.api_key),
            "supported_formats": list(self.SUPPORTED_FORMATS),
            "max_size_mb": self.MAX_FILE_SIZE // (1024 * 1024),
        }

    def validate_image(self, image_path: str) -> dict:
        path = Path(image_path)
        if not path.exists():
            return {"valid": False, "error": f"文件不存在: {image_path}", "details": {}}
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            return {"valid": False, "error": f"不支持的格式: {ext}", "details": {"format": ext}}
        size = path.stat().st_size
        if size > self.MAX_FILE_SIZE:
            return {"valid": False, "error": f"文件过大: {size / 1024 / 1024:.1f}MB", "details": {"size_mb": size / 1024 / 1024}}
        return {"valid": True, "error": "", "details": {"format": ext, "size_mb": size / 1024 / 1024}}

    def describe_image(self, image_path: str, prompt: str = None) -> dict:
        validation = self.validate_image(image_path)
        if not validation["valid"]:
            return self._error_result(validation["error"])

        if not self.session:
            return self._error_result("API 未初始化，请检查 MINIMAX_TOKEN_PLAN_KEY")

        default_prompt = prompt or PROMPT_VISION_ANALYSIS

        try:
            import base64
            path = Path(image_path)
            with open(path, "rb") as f:
                image_data = f.read()

            ext = path.suffix.lower()
            mime_type = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"
            }.get(ext, "image/png")

            b64_data = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64_data}"

            payload = {"prompt": default_prompt, "image_url": data_url}
            url = f"{self.base_url}/v1/coding_plan/vlm"
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            resp_data = response.json()
            content = resp_data.get("content", "")

            if not content:
                return self._error_result("VLM API 返回为空")

            result = self._parse_json_response(content)
            result["status"] = "success"
            result["model"] = "MiniMax-VLM"
            return result

        except Exception as e:
            return self._error_result(f"VLM 调用失败: {str(e)}")

    def _error_result(self, error_msg: str) -> dict:
        return {
            "description": "",
            "detected_text": "",
            "visual_summary": "",
            "layout_summary": "",
            "style_keywords": [],
            "strategy_hint": "",
            "reusable_pattern": "",
            "confidence": 0.0,
            "status": "error",
            "error": error_msg,
            "model": "MiniMax-VLM",
        }

    def _parse_json_response(self, text: str) -> dict:
        import json
        import re
        try:
            return json.loads(text)
        except Exception:
            pass
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return {
            "description": text[:500] if text else "",
            "detected_text": "",
            "visual_summary": text[:300] if len(text) > 300 else text,
            "layout_summary": "",
            "style_keywords": [],
            "strategy_hint": "",
            "reusable_pattern": "",
            "confidence": 0.5,
        }


class OpenAICompatibleVisionClient(AIClient):
    """
    OpenAI-Compatible API 客户端（用于通用代理）
    """

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 supports_vision: bool = None):
        self.api_key = api_key or os.environ.get("AICLIENT_API_KEY", "")
        self.base_url = base_url or os.environ.get("AICLIENT_BASE_URL", "")
        self.model = model or os.environ.get("AICLIENT_MODEL", "gpt-4o")
        if supports_vision is None:
            supports_vision_str = os.environ.get("AICLIENT_SUPPORTS_VISION", "true").lower()
            supports_vision = supports_vision_str != "false"
        self.supports_vision = supports_vision
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key or not self.base_url:
            return
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            pass

    def describe_image(self, image_path: str, prompt: str = None) -> dict:
        if self.client is None:
            return self._error_result("API 未初始化")
        if not self.supports_vision:
            return self._error_result(f"当前 model ({self.model}) 不支持图片输入")
        default_prompt = prompt or PROMPT_VISION_ANALYSIS
        try:
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                        {"type": "text", "text": default_prompt}
                    ]
                }],
                max_tokens=1024,
            )
            text = response.choices[0].message.content if response.choices else ""
            result = self._parse_json_response(text)
            result["status"] = "success"
            result["model"] = self.model
            return result
        except Exception as e:
            return self._error_result(str(e))

    def ping(self) -> dict:
        if not self.client:
            return {"success": False, "message": "API 未初始化"}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "回复 OK"}],
                max_tokens=10,
            )
            text = response.choices[0].message.content if response.choices else ""
            if "OK" in text:
                return {"success": True, "message": "API 连接正常"}
            return {"success": False, "message": f"Unexpected response: {text}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _error_result(self, error_msg: str) -> dict:
        return {
            "description": "",
            "detected_text": "",
            "visual_summary": "",
            "layout_summary": "",
            "style_keywords": [],
            "strategy_hint": "",
            "reusable_pattern": "",
            "confidence": 0.0,
            "status": "error",
            "error": error_msg,
            "model": self.model,
        }

    def _parse_json_response(self, text: str) -> dict:
        import json
        import re
        try:
            return json.loads(text)
        except Exception:
            pass
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return {
            "description": text[:500] if text else "",
            "detected_text": "",
            "visual_summary": "",
            "layout_summary": "",
            "style_keywords": [],
            "strategy_hint": "",
            "reusable_pattern": "",
            "confidence": 0.5,
        }


def create_ai_client(provider: str = "mock", **kwargs) -> AIClient:
    if provider == "mock":
        return MockAIClient()
    elif provider == "minimax-text":
        return MiniMaxTextClient(**kwargs)
    elif provider == "minimax-mcp":
        return MiniMaxMCPClient(**kwargs)
    elif provider == "openai-compatible":
        return OpenAICompatibleVisionClient(**kwargs)
    else:
        raise ValueError(f"不支持的 provider: {provider}")
