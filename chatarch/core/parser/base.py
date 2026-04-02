from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from chatarch.db.models import Session

class BaseParser(ABC):
    """
    基础解析器接口
    所有的聊天记录导入解析器都必须继承自该基类
    """
    
    @abstractmethod
    def parse(self, file_path: Path, default_tags: str = "") -> List[Session]:
        """
        解析给定的文件，返回标准化后的会话模型列表
        
        Args:
            file_path: 需要解析的文件路径 (如 conversations.json 或 markdown 文件)
            default_tags: 用户指定的默认附加标签
            
        Returns:
            List[Session]: 解析后的会话实体对象列表（附带关联的 Message 对象）
        """
        pass
