from typing import List, Optional
from sqlalchemy.orm import Session as DbSession
from chatarch.db.models import Session, Message

def create_session_with_message(
    db: DbSession, 
    title: str, 
    content: str, 
    role: str = "user", 
    model_name: str = "manual",
    tags: Optional[str] = None
) -> Session:
    """手动创建一条会话，并附带一条初始消息"""
    
    new_session = Session(
        title=title,
        model_name=model_name,
        source_type="manual",
        tags=tags
    )
    
    initial_message = Message(
        role=role,
        content=content,
        sequence=1,
        sender_name="user" if role == "user" else "assistant",
        content_format="text"
    )
    
    new_session.messages.append(initial_message)
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

def get_recent_sessions(db: DbSession, limit: int = 10, tag: Optional[str] = None, starred: bool = False) -> List[Session]:
    """获取最近的会话列表"""
    query = db.query(Session)
    
    if starred:
        query = query.filter(Session.is_starred == True)
        
    if tag:
        query = query.filter(Session.tags.like(f"%{tag}%"))
        
    query = query.order_by(Session.created_at.desc()).limit(limit)
    return query.all()
