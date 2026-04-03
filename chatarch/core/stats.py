from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import func

from chatarch.db.models import Session, Message

def get_basic_stats(db: DbSession) -> Dict[str, Any]:
    """获取基础总量统计"""
    total_sessions = db.query(Session).count()
    total_messages = db.query(Message).count()
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages
    }

def get_platform_distribution(db: DbSession) -> List[Tuple[str, int]]:
    """统计各个平台的会话数量"""
    results = db.query(
        Session.model_platform, 
        func.count(Session.id)
    ).group_by(Session.model_platform).all()
    
    cleaned_results = []
    for platform, count in results:
        name = platform if platform else "未知/手工录入"
        cleaned_results.append((name, count))
    
    # 按数量降序排列
    cleaned_results.sort(key=lambda x: x[1], reverse=True)
    return cleaned_results

def get_tag_distribution(db: DbSession, limit: int = 10) -> List[Tuple[str, int]]:
    """统计出现频率最高的标签"""
    sessions_with_tags = db.query(Session.tags).filter(Session.tags.isnot(None)).all()
    
    tag_counter = Counter()
    for (tags_str,) in sessions_with_tags:
        if not tags_str:
            continue
        # 拆分逗号分隔的标签并清理两端空格
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        tag_counter.update(tags)
        
    return tag_counter.most_common(limit)

def get_daily_trend(db: DbSession, days: int = 14) -> List[Tuple[str, int]]:
    """获取过去 N 天每天的会话新增量"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # SQLite 专用的 strftime 提取日期
    results = db.query(
        func.strftime('%Y-%m-%d', Session.created_at).label('day'),
        func.count(Session.id)
    ).filter(
        Session.created_at >= cutoff_date
    ).group_by('day').order_by('day').all()
    
    return results
