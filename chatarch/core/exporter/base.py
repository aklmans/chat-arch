from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from chatarch.db.models import Session

class BaseExporter(ABC):
    """
    基础导出器接口
    所有的导出格式支持都必须继承自该基类
    """
    
    @abstractmethod
    def export(self, sessions: List[Session], output_path: Path) -> None:
        """
        将会话列表导出为目标格式
        
        Args:
            sessions: 需要导出的会话实体列表
            output_path: 输出的文件或目录路径
        """
        pass
