import pytest
from pathlib import Path
from chatarch.core.parser.claude import ClaudeParser
from chatarch.db.models import Session, Message

# 固化测试数据路径
DUMMY_CLAUDE = Path(__file__).parent / "dummy_claude.json"

def test_claude_parser_file_not_found():
    parser = ClaudeParser()
    with pytest.raises(FileNotFoundError):
        parser.parse(Path("non_existent_file.json"))

def test_claude_parser_success():
    parser = ClaudeParser()
    
    # 解析测试文件
    sessions = parser.parse(DUMMY_CLAUDE, default_tags="claude-test")
    
    # 验证是否解析出了两个会话
    assert len(sessions) == 2
    
    # 获取第一个会话
    session1 = sessions[0]
    assert session1.title == "Rust 并发编程探讨"
    assert session1.model_platform == "Claude"
    assert session1.source_type == "claude_export"
    assert session1.tags == "claude-test"
    assert len(session1.messages) == 4
    
    # 验证第一条消息
    msg1 = session1.messages[0]
    assert msg1.role == "user"  # human 被映射为 user
    assert msg1.sequence == 1
    assert "Rust 中的 Arc 和 Mutex 的组合使用场景" in msg1.content
    
    # 验证第二条消息
    msg2 = session1.messages[1]
    assert msg2.role == "assistant"
    assert msg2.sequence == 2
    assert "提供原子引用计数" in msg2.content

    # 获取第二个会话：包含一个空内容的废弃记录
    session2 = sessions[1]
    assert session2.title == "废弃的对话"
    
    # 因为我们在 parser 里面对空的 unknown 角色进行了拦截处理，但是对于空内容的 user(human) 会保留
    assert len(session2.messages) == 1
    assert session2.messages[0].role == "user"
    assert session2.messages[0].content == ""
