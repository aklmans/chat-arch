from pathlib import Path
from typing import Dict, Type

from .base import BaseParser
from .openai import OpenAIParser
from .markdown import MarkdownParser
from .claude import ClaudeParser
from .gemini import GeminiParser
from .cursor import CursorParser

# 解析器注册表
PARSER_REGISTRY: Dict[str, Type[BaseParser]] = {
    "openai": OpenAIParser,
    "markdown": MarkdownParser,
    "md": MarkdownParser,
    "claude": ClaudeParser,
    "gemini": GeminiParser,
    "cursor": CursorParser,
}

def get_parser(format_name: str) -> BaseParser:
    """获取对应的解析器实例"""
    parser_class = PARSER_REGISTRY.get(format_name.lower())
    if not parser_class:
        supported = ", ".join(PARSER_REGISTRY.keys())
        raise ValueError(f"不支持的格式: {format_name}。目前支持的格式有: {supported}")
    return parser_class()


