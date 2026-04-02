from typing import List
from pathlib import Path
from chatarch.db.models import Session
from .base import BaseExporter

class MarkdownExporter(BaseExporter):
    """
    导出为 Markdown 格式
    将一个或多个会话合并写入到一个 Markdown 文件中
    """
    
    def export(self, sessions: List[Session], output_path: Path) -> None:
        if not sessions:
            return
            
        with open(output_path, "w", encoding="utf-8") as f:
            for i, session in enumerate(sessions):
                # 写入会话元数据 Header
                f.write(f"# {session.title or '未命名会话'}\n\n")
                f.write(f"> **ID**: {session.id}\n")
                f.write(f"> **平台**: {session.model_platform or '未知'}\n")
                if session.tags:
                    f.write(f"> **标签**: {session.tags}\n")
                f.write(f"> **时间**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                # 写入消息体
                for msg in session.messages:
                    icon = "🧑" if msg.role == "user" else "🤖"
                    role_name = msg.role.capitalize()
                    time_str = msg.timestamp.strftime('%H:%M:%S') if msg.timestamp else ""
                    
                    f.write(f"### {icon} {role_name} ({time_str})\n\n")
                    f.write(f"{msg.content}\n\n")
                
                if i < len(sessions) - 1:
                    f.write("\n<br><br>\n\n")
