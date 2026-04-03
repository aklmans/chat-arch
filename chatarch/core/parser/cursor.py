import json
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any

from chatarch.db.models import Session, Message
from .base import BaseParser

class CursorParser(BaseParser):
    """
    Cursor 聊天记录解析器。
    支持解析其内部 SQLite 数据库 (state.vscdb)。
    """
    
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        if not file_path.exists():
            raise FileNotFoundError(f"找不到指定的 Cursor 数据库文件: {file_path}")
            
        sessions: List[Session] = []
        
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # 1. 尝试从 ItemTable 中获取工作区聊天数据 (workbench.panel.aichat.view.aichat.chatdata)
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'workbench.panel.aichat.view.aichat.chatdata'")
            row = cursor.fetchone()
            
            if row:
                chat_data = json.loads(row[0])
                tabs = chat_data.get("tabs", [])
                
                for tab in tabs:
                    chat_id = tab.get("id", "cursor-chat")
                    bubbles = tab.get("bubbles", [])
                    if not bubbles:
                        continue
                        
                    # 尝试从第一个 bubble 提取标题，或者使用默认值
                    title = tab.get("chatTitle") or "Cursor 会话"
                    
                    session = Session(
                        title=title,
                        model_platform="Cursor",
                        source_type="cursor_db",
                        tags=default_tags,
                        source_url=f"cursor://{chat_id}"
                    )
                    
                    for seq, bubble in enumerate(bubbles, start=1):
                        role_raw = bubble.get("role", "user")
                        role = "user" if role_raw == "user" else "assistant"
                        content = bubble.get("text", "")
                        
                        if not content:
                            continue
                            
                        new_msg = Message(
                            sequence=seq,
                            role=role,
                            sender_name=role,
                            content=content,
                            content_format="markdown",
                            timestamp=datetime.datetime.utcnow()
                        )
                        session.messages.append(new_msg)
                    
                    if session.messages:
                        sessions.append(session)
            
            conn.close()
        except Exception as e:
            # 如果是 JSON 文件而不是 SQLite，则尝试 JSON 解析（针对用户已经导出的 JSON）
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 递归处理或是按照特定导出格式处理
                    # 这里先实现核心的 SQLite 逻辑
                    pass
            except:
                raise RuntimeError(f"解析 Cursor 数据库失败: {e}")
                
        return sessions
