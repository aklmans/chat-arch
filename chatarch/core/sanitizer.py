import re
from typing import List, Union
from chatarch.db.models import Session, Message

# 定义一些常见的 PII (个人隐私信息) 正则表达式
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone": r"(\+?86)?(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}",
    "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "api_key": r"(?:sk-[a-zA-Z0-9]{48}|AIza[0-9A-Za-z-_]{35})",
}

def sanitize_text(text: str) -> str:
    """
    对文本进行敏感词和 PII 脱敏处理
    """
    if not text:
        return text
        
    sanitized = text
    for pii_type, pattern in PII_PATTERNS.items():
        # 将匹配到的内容替换为类似 [EMAIL], [PHONE] 的占位符
        placeholder = f"[{pii_type.upper()}]"
        sanitized = re.sub(pattern, placeholder, sanitized)
        
    return sanitized

def sanitize_session(session: Session) -> Session:
    """
    对 Session 及其包含的消息进行深度脱敏
    """
    if session.title:
        session.title = sanitize_text(session.title)
    if session.summary:
        session.summary = sanitize_text(session.summary)
        
    for msg in session.messages:
        msg.content = sanitize_text(msg.content)
        
    return session

def sanitize_sessions(sessions: List[Session]) -> List[Session]:
    """
    批量脱敏会话列表
    """
    for session in sessions:
        sanitize_session(session)
    return sessions
