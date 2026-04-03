import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from chatarch.db.models import Session, Message
from .base import BaseParser

class ClaudeParser(BaseParser):
    """
    Anthropic Claude 官方导出 `conversations.json` 解析器
    支持全量无脑导入：提取对话中所有用户的输入和助手的回复。
    """
    
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        if not file_path.exists():
            raise FileNotFoundError(f"找不到指定的 Claude 导出文件: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        if not isinstance(raw_data, list):
            raise ValueError("非法的 Claude 导出格式：顶层非列表结构。请确保导入的是 conversations.json 文件。")
            
        sessions: List[Session] = []
        
        for item in raw_data:
            session_id = item.get("uuid", "") 
            title = item.get("name", "未命名会话")
            create_time_str = item.get("created_at")
            update_time_str = item.get("updated_at")
            
            session = Session(
                title=title,
                model_platform="Claude",
                source_type="claude_export",
                tags=default_tags,
                source_url=f"https://claude.ai/chat/{session_id}" if session_id else None
            )
            
            # 尝试解析 ISO 8601 时间戳
            if create_time_str:
                try:
                    # Claude 的时间格式通常是 2024-04-01T12:00:00Z 等
                    clean_time_str = create_time_str.replace("Z", "+00:00")
                    session.created_at = datetime.datetime.fromisoformat(clean_time_str)
                    session.updated_at = session.created_at
                except ValueError:
                    pass
                    
            if update_time_str:
                try:
                    clean_time_str = update_time_str.replace("Z", "+00:00")
                    session.updated_at = datetime.datetime.fromisoformat(clean_time_str)
                except ValueError:
                    pass

            chat_messages = item.get("chat_messages", [])
            # 确保消息按照时间顺序排序
            chat_messages.sort(key=lambda m: m.get("created_at", ""))
            
            for seq, msg_data in enumerate(chat_messages, start=1):
                # sender 通常是 "human" 或 "assistant"
                raw_sender = msg_data.get("sender", "unknown")
                role = "user" if raw_sender == "human" else ("assistant" if raw_sender == "assistant" else raw_sender)
                
                content = msg_data.get("text", "")
                if not content and role == "unknown":
                    continue
                    
                msg_timestamp_str = msg_data.get("created_at")
                
                new_msg = Message(
                    sequence=seq,
                    role=role,
                    sender_name=role,
                    content=content,
                    content_format="markdown",
                )
                
                if msg_timestamp_str:
                    try:
                        clean_time_str = msg_timestamp_str.replace("Z", "+00:00")
                        new_msg.timestamp = datetime.datetime.fromisoformat(clean_time_str)
                    except ValueError:
                        pass
                
                session.messages.append(new_msg)
            
            sessions.append(session)
            
        return sessions
