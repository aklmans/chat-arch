import re
from pathlib import Path
from typing import List

from chatarch.db.models import Session, Message
from .base import BaseParser

class MarkdownParser(BaseParser):
    """
    通用 Markdown 格式解析器
    通过简单的启发式规则识别标题和角色对话，并将结构化的数据入库。
    """
    
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        if not file_path.exists():
            raise FileNotFoundError(f"找不到指定的 Markdown 文件: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if not lines:
            return []

        # 启发式状态机变量
        title = file_path.stem # 默认使用文件名作为标题
        messages: List[Message] = []
        
        current_role = "user" # 默认第一句话是 user 说的
        current_content_buffer = []
        sequence = 1
        
        # 预编译正则提高性能
        # 匹配 H1 标题: `# 标题`
        title_pattern = re.compile(r"^#\s+(.+)$")
        # 匹配角色标记: `### User`, `**User**:`, `User:`, `### 🧑 User` 等
        role_pattern = re.compile(r"^(?:###\s*(?:[^\w\s]*\s*)?|(?:\*\*)?)(user|assistant|system|tool)(?:(?:\*\*)?:|\b)", re.IGNORECASE)

        def flush_message():
            nonlocal current_role, current_content_buffer, sequence
            content = "\n".join(current_content_buffer).strip()
            if content:
                msg = Message(
                    sequence=sequence,
                    role=current_role.lower(),
                    sender_name=current_role.lower(),
                    content=content,
                    content_format="markdown"
                )
                messages.append(msg)
                sequence += 1
            current_content_buffer = []

        for line in lines:
            clean_line = line.strip()
            
            # 尝试提取标题
            title_match = title_pattern.match(clean_line)
            if title_match and len(messages) == 0 and not current_content_buffer:
                title = title_match.group(1).strip()
                continue
                
            # 尝试提取角色标记
            role_match = role_pattern.match(clean_line)
            if role_match:
                # 遇到新的角色，先将上一个角色的内容刷入消息列表
                flush_message()
                current_role = role_match.group(1).lower()
                continue
                
            # 处理开头的冗余元数据 (仅在还没有任何真实消息之前)
            if len(messages) == 0:
                if clean_line.startswith("> **") or clean_line == "":
                    # 如果只有空白行或元数据，并且还没碰到过真正的非空白文本，就丢弃
                    # 为了判断是不是真正的文本，我们检查 buffer 里是不是全空
                    if all(not line.strip() for line in current_content_buffer):
                        continue
                    
            current_content_buffer.append(line.rstrip('\n'))
            
        # 循环结束，刷入最后一段缓冲
        flush_message()
        
        # 构建并返回 Session
        session = Session(
            title=title,
            source_type="markdown",
            tags=default_tags,
        )
        
        session.messages.extend(messages)
        
        return [session]
