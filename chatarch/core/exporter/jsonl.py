import json
from typing import List
from pathlib import Path
from chatarch.db.models import Session
from .base import BaseExporter

class JsonlExporter(BaseExporter):
    """
    导出为 JSONL (JSON Lines) 格式
    这是一种极度适合 LLM SFT 微调训练和批量数据处理的格式，每行一个 JSON 对象
    """
    
    def export(self, sessions: List[Session], output_path: Path) -> None:
        if not sessions:
            return
            
        with open(output_path, "w", encoding="utf-8") as f:
            for session in sessions:
                # 构造符合 OpenAI/开源模型微调习惯的 messages 结构
                messages_list = []
                for msg in session.messages:
                    messages_list.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                # 构建单行 JSON 对象
                line_obj = {
                    "id": session.id,
                    "title": session.title,
                    "tags": session.tags,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "messages": messages_list
                }
                
                # 写入一行，不带换行和缩进，保证一行一个独立 JSON
                json_str = json.dumps(line_obj, ensure_ascii=False)
                f.write(f"{json_str}\n")
