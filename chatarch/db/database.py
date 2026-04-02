import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 获取用户主目录下的配置路径
HOME_DIR = Path.home()
CHATARCH_DIR = HOME_DIR / ".chatarch"
DB_PATH = CHATARCH_DIR / "data.db"

# 确保目录存在
CHATARCH_DIR.mkdir(parents=True, exist_ok=True)

# 创建数据库引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()

def setup_fts(connection):
    """设置 SQLite FTS5 虚拟表及触发器，以支持全文检索"""
    
    # 会话标题和标签的 FTS
    connection.execute(text('''
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
            id UNINDEXED,
            title,
            tags,
            content='sessions',
            content_rowid='rowid'
        );
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
            INSERT INTO sessions_fts(rowid, id, title, tags) VALUES (new.rowid, new.id, new.title, new.tags);
        END;
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS sessions_ad AFTER DELETE ON sessions BEGIN
            INSERT INTO sessions_fts(sessions_fts, rowid, id, title, tags) VALUES('delete', old.rowid, old.id, old.title, old.tags);
        END;
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
            INSERT INTO sessions_fts(sessions_fts, rowid, id, title, tags) VALUES('delete', old.rowid, old.id, old.title, old.tags);
            INSERT INTO sessions_fts(rowid, id, title, tags) VALUES (new.rowid, new.id, new.title, new.tags);
        END;
    '''))

    # 消息内容的 FTS
    connection.execute(text('''
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            id UNINDEXED,
            session_id UNINDEXED,
            role UNINDEXED,
            content,
            content='messages',
            content_rowid='rowid'
        );
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, id, session_id, role, content) VALUES (new.rowid, new.id, new.session_id, new.role, new.content);
        END;
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, id, session_id, role, content) VALUES('delete', old.rowid, old.id, old.session_id, old.role, old.content);
        END;
    '''))
    
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, id, session_id, role, content) VALUES('delete', old.rowid, old.id, old.session_id, old.role, old.content);
            INSERT INTO messages_fts(rowid, id, session_id, role, content) VALUES (new.rowid, new.id, new.session_id, new.role, new.content);
        END;
    '''))

def init_db():
    """初始化数据库，创建所有表，并设置全文检索"""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        setup_fts(conn)

def get_db():
    """获取数据库会话生成器 (用于依赖注入)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

