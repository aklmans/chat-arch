from typing import List, Optional, Tuple
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import text
from chatarch.db.models import Session, Message
from chatarch.core.parser.markdown import MarkdownParser

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

def get_session_by_id(db: DbSession, session_id: str) -> Optional[Session]:
    """通过精确 ID 或短 ID 获取会话"""
    # 尝试精确匹配
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        return session
    
    # 尝试短前缀匹配
    session = db.query(Session).filter(Session.id.startswith(session_id)).first()
    return session

def search_sessions_fts(db: DbSession, query_str: str, role: Optional[str] = None) -> List[Tuple[Session, str]]:
    """
    使用 FTS5 执行全文检索。
    返回 List[Tuple[Session, snippet]], 其中 snippet 是高亮的上下文片段。
    """
    # SQLite FTS5 的 MATCH 语法
    # 搜索包含在 titles/tags 以及 messages 内容中的数据
    
    # 查询标题或标签命中的会话
    session_fts_query = """
        SELECT id, snippet(sessions_fts, 1, '[bold cyan]', '[/bold cyan]', '...', 10) as snip
        FROM sessions_fts 
        WHERE sessions_fts MATCH :q
    """
    
    # 查询消息内容命中的会话
    msg_fts_query = """
        SELECT session_id as id, snippet(messages_fts, 3, '[bold cyan]', '[/bold cyan]', '...', 10) as snip
        FROM messages_fts 
        WHERE messages_fts MATCH :q
    """
    
    if role:
        # FTS5 中限定特定字段搜索的方式: role:user AND <query>
        fts_match_str = f"role:{role} AND {query_str}"
    else:
        fts_match_str = query_str
        
    session_results = db.execute(text(session_fts_query), {"q": query_str}).fetchall()
    msg_results = db.execute(text(msg_fts_query), {"q": fts_match_str}).fetchall()
    
    # 聚合结果
    hit_map = {} # session_id -> snippet
    
    for row in session_results:
        hit_map[row.id] = f"标题/标签命中: {row.snip}"
        
    for row in msg_results:
        # 消息命中优先级/覆盖
        if row.id not in hit_map:
            hit_map[row.id] = f"内容命中: {row.snip}"
        else:
            hit_map[row.id] += f" | 内容命中: {row.snip}"
            
    if not hit_map:
        return []
        
    # 查询真实的 Session 实体
    # 注意：在数据量极大时，使用 in_ 会有数量限制，但这满足 MVP
    sessions = db.query(Session).filter(Session.id.in_(hit_map.keys())).order_by(Session.created_at.desc()).limit(50).all()
    
    return [(s, hit_map[s.id]) for s in sessions]

def update_session_from_text(db: DbSession, session: Session, new_text: str) -> None:
    """使用新编辑的 Markdown 文本覆盖更新现有会话内容"""
    parser = MarkdownParser()
    # 我们调用解析文本的方法，并默认传承它原本的标题和标签作为备用
    parsed_sessions = parser.parse_text(new_text, default_title=session.title, default_tags=session.tags)
    
    if not parsed_sessions:
        raise ValueError("解析后的文本中未包含任何有效的会话内容")
        
    updated_model = parsed_sessions[0]
    
    # 覆盖标题（如果文本被 `# xxx` 语法修改了的话）
    if updated_model.title and updated_model.title != "未命名":
        session.title = updated_model.title
        
    # 覆盖消息体，利用 SQLAlchemy cascade="all, delete-orphan" 删除旧记录，插入新记录
    session.messages = updated_model.messages
    
    # 更新版本号与元数据
    session.version = (session.version or 1) + 1
    
    db.commit()
    db.refresh(session)


