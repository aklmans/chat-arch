import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Session(Base):
    """会话表模型"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    model_platform = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 存为逗号分隔的字符串或 JSON
    tags = Column(String, nullable=True)
    project = Column(String, nullable=True)
    language = Column(String, nullable=True)
    status = Column(String, nullable=True)
    is_starred = Column(Boolean, default=False)
    priority = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    external_links = Column(Text, nullable=True)
    
    token_count = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    privacy_level = Column(String, nullable=True)
    version = Column(Integer, default=1)
    note = Column(Text, nullable=True)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.sequence")


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    sequence = Column(Integer, nullable=False, default=0)
    
    role = Column(String, nullable=False) # system/user/assistant/tool
    sender_name = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    content_format = Column(String, default="text") # text/markdown/code/json
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    attachments = Column(Text, nullable=True) # JSON 格式存储本地路径
    tags = Column(String, nullable=True)
    is_key_node = Column(Boolean, default=False)
    
    reply_to_id = Column(String, ForeignKey("messages.id"), nullable=True)
    
    token_count = Column(Integer, default=0)
    execution_result = Column(Text, nullable=True)
    error_status = Column(String, nullable=True)
    hash_val = Column(String, nullable=True)

    session = relationship("Session", back_populates="messages")
