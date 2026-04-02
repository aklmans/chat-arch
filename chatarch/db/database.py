import os
from pathlib import Path
from sqlalchemy import create_engine
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

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话生成器 (用于依赖注入)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
