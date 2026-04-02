import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from chatarch.db.models import Session, Message
from .base import BaseParser

class OpenAIParser(BaseParser):
    """
    OpenAI ChatGPT 官方导出 `conversations.json` 解析器
    支持全量无脑导入：提取每一个包含有用户输入的对话节点作为一次完整 Message 流。
    """
    
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        if not file_path.exists():
            raise FileNotFoundError(f"找不到指定的 OpenAI 导出文件: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        if not isinstance(raw_data, list):
            raise ValueError("非法的 OpenAI 导出格式：顶层非列表结构。请确保导入的是 conversations.json 文件。")
            
        sessions: List[Session] = []
        
        for item in raw_data:
            # 基础元数据
            session_id = item.get("id", "") # OpenAI 的内置 ID，可以直接覆写或用它生成我们的本地 ID
            title = item.get("title", "未命名会话")
            create_time = item.get("create_time") # Unix timestamp
            
            # 使用我们的生成策略创建对象
            session = Session(
                title=title,
                model_platform="ChatGPT",
                source_type="openai_export",
                tags=default_tags,
                source_url=f"https://chat.openai.com/c/{session_id}" if session_id else None
            )
            
            # 设置时间
            if create_time:
                try:
                    session.created_at = datetime.datetime.fromtimestamp(float(create_time))
                    session.updated_at = session.created_at
                except (ValueError, TypeError):
                    pass

            mapping = item.get("mapping", {})
            
            # 解析消息节点并整理顺序
            messages = self._extract_messages(mapping)
            
            # 将提取出的按序排列的消息附加到会话上
            for seq, msg_data in enumerate(messages, start=1):
                role = msg_data.get("role", "unknown")
                content = msg_data.get("content", "")
                
                # 如果为空且是用户输入，或者其他，只要有内容才加，不拦截空对话但拦截空消息以防止数据库约束失败
                if not content and role == "unknown":
                    continue
                
                msg_timestamp = msg_data.get("create_time")
                
                new_msg = Message(
                    sequence=seq,
                    role=role,
                    sender_name=role,
                    content=content,
                    content_format="markdown",
                )
                
                if msg_timestamp:
                    try:
                        new_msg.timestamp = datetime.datetime.fromtimestamp(float(msg_timestamp))
                    except (ValueError, TypeError):
                        pass
                
                session.messages.append(new_msg)
            
            sessions.append(session)
            
        return sessions

    def _extract_messages(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 OpenAI 的树状结构(mapping) 中提取当前时间线的线性消息列表
        在全量策略下，我们这里只抽取最新的/最主干的一条分支记录
        """
        messages = []
        
        # 寻找最终叶子节点 (没有 children 的节点通常认为是最后一个回答)
        # 这里用一种简单启发式：找 create_time 最新或者位于末端的节点，反向溯源
        leaf_nodes = [node for node in mapping.values() if not node.get("children")]
        
        if not leaf_nodes:
            return []
            
        # 选择最新的一条叶子节点为主干
        latest_leaf = max(leaf_nodes, key=lambda n: n.get("message", {}).get("create_time", 0) if n.get("message") else 0)
        
        # 反向追溯树结构
        current_id = latest_leaf.get("id")
        chain = []
        
        while current_id:
            node = mapping.get(current_id)
            if not node:
                break
                
            msg = node.get("message")
            if msg and msg.get("content", {}).get("content_type") == "text":
                author_role = msg.get("author", {}).get("role", "unknown")
                parts = msg.get("content", {}).get("parts", [])
                text_content = "".join([str(p) for p in parts if p])
                
                create_time = msg.get("create_time")
                
                chain.append({
                    "role": author_role,
                    "content": text_content,
                    "create_time": create_time
                })
                
            current_id = node.get("parent")
            
        # 因为我们是自下而上追溯的，所以需要反转列表恢复正常的时间顺序
        chain.reverse()
        return chain