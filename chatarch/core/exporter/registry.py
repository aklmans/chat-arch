from typing import Dict, Type

from .base import BaseExporter
from .markdown import MarkdownExporter
from .jsonl import JsonlExporter

# 导出器注册表
EXPORTER_REGISTRY: Dict[str, Type[BaseExporter]] = {
    "markdown": MarkdownExporter,
    "md": MarkdownExporter,
    "jsonl": JsonlExporter,
}

def get_exporter(format_name: str) -> BaseExporter:
    """获取对应的导出器实例"""
    exporter_class = EXPORTER_REGISTRY.get(format_name.lower())
    if not exporter_class:
        supported = ", ".join(EXPORTER_REGISTRY.keys())
        raise ValueError(f"不支持的导出格式: {format_name}。目前支持的格式有: {supported}")
    return exporter_class()
