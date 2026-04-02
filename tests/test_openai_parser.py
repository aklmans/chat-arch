import pytest
from pathlib import Path
from chatarch.core.parser.openai import OpenAIParser
from chatarch.db.models import Session, Message

# 固化测试数据路径
DUMMY_JSON = Path(__file__).parent / "dummy_conversations.json"

def test_openai_parser_file_not_found():
    parser = OpenAIParser()
    with pytest.raises(FileNotFoundError):
        parser.parse(Path("non_existent_file.json"))

def test_openai_parser_success():
    parser = OpenAIParser()
    
    # 解析测试文件
    sessions = parser.parse(DUMMY_JSON, default_tags="openai-test")
    
    # 验证是否解析出了两个会话（见 dummy_conversations.json）
    assert len(sessions) == 2
    
    # 获取第一个会话：完整对话分支
    session1 = sessions[0]
    assert session1.title == "如何用 Python 编写解释器"
    assert session1.model_platform == "ChatGPT"
    assert session1.source_type == "openai_export"
    assert session1.tags == "openai-test"
    assert len(session1.messages) == 3
    
    # 验证第一条消息
    msg1 = session1.messages[0]
    assert msg1.role == "system"
    assert msg1.sequence == 1
    assert "You are a helpful assistant." in msg1.content
    
    # 验证第三条消息
    msg3 = session1.messages[2]
    assert msg3.role == "assistant"
    assert msg3.sequence == 3
    assert "要实现解释器，你需要先做词法分析" in msg3.content

    # 获取第二个会话：包含一个空内容的异常废弃记录
    session2 = sessions[1]
    assert session2.title == "废弃的空对话"
    
    # 因为我们在 parser 里面对空的 unknown 角色进行了拦截处理，但是对于空内容的 user 会保留
    assert len(session2.messages) == 1
    assert session2.messages[0].role == "user"
    assert session2.messages[0].content == ""
