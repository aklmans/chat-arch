import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from chatarch.db.models import Session, Message
from .base import BaseParser

class GeminiParser(BaseParser):
    """
    Google AI Studio (Gemini) 导出的 JSON 解析器。
    支持 contents/role/parts/text 结构。
    """
    
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        if not file_path.exists():
            raise FileNotFoundError(f"找不到指定的 Gemini 导出文件: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        # Gemini 导出可能是单个会话对象，也可能是包含多个会话的列表
        # 根据调研，AI Studio 导出的单个文件通常是一个会话对象
        items = raw_data if isinstance(raw_data, list) else [raw_data]
        
        sessions: List[Session] = []
        
        for item in items:
            contents = item.get("contents", [])
            if not contents:
                continue
                
            # 尝试获取标题（某些导出可能有，没有则用默认）
            title = item.get("title") or item.get("name") or "Gemini 会话"
            
            session = Session(
                title=title,
                model_platform="Gemini",
                source_type="gemini_export",
                tags=default_tags
            )
            
            # 遍历消息
            for seq, content_item in enumerate(contents, start=1):
                role_raw = content_item.get("role", "user")
                # 标准化角色：user -> user, model -> assistant
                role = "user" if role_raw == "user" else "assistant"
                
                parts = content_item.get("parts", [])
                # 合并 parts 中的 text
                text_parts = []
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        text_parts.append(p["text"])
                    elif isinstance(p, str):
                        text_parts.append(p)
                
                content = "\n".join(text_parts)
                
                if not content.strip():
                    continue
                    
                new_msg = Message(
                    sequence=seq,
                    role=role,
                    sender_name=role,
                    content=content,
                    content_format="markdown",
                    timestamp=datetime.datetime.utcnow() # Gemini 导出通常没带单条消息时间戳
                )
                session.messages.append(new_msg)
            
            if session.messages:
                sessions.append(session)
                
        return sessions
