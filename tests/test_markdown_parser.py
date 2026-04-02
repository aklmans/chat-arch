import pytest
from pathlib import Path
from chatarch.core.parser.markdown import MarkdownParser

DUMMY_MD = Path(__file__).parent / "dummy_chat.md"

def test_markdown_parser_file_not_found():
    parser = MarkdownParser()
    with pytest.raises(FileNotFoundError):
        parser.parse(Path("non_existent_file.md"))

def test_markdown_parser_success():
    parser = MarkdownParser()
    sessions = parser.parse(DUMMY_MD, default_tags="md-test")
    
    assert len(sessions) == 1
    session = sessions[0]
    
    # 验证启发式提取的标题
    assert session.title == "Rust 借用检查器探讨"
    assert session.source_type == "markdown"
    assert session.tags == "md-test"
    
    # 验证消息解析是否正确根据角色拆分
    assert len(session.messages) == 4
    
    # User 的第一句话
    msg1 = session.messages[0]
    assert msg1.role == "user"
    assert msg1.sequence == 1
    assert "能简单说明一下 Rust 中借用检查器（Borrow Checker）的核心原则吗？" in msg1.content
    
    # Assistant 的第一句话
    msg2 = session.messages[1]
    assert msg2.role == "assistant"
    assert msg2.sequence == 2
    assert "借用检查器主要基于以下两个核心原则" in msg2.content
    assert "唯一的并且是可变的引用" in msg2.content # 验证多行合并
    
    # User 的第二句话
    msg3 = session.messages[2]
    assert msg3.role == "user"
    assert msg3.sequence == 3
    assert "所以如果我有一个可变借用，就不能再创建不可变借用了是吗？" in msg3.content

    # Assistant 的第二句话
    msg4 = session.messages[3]
    assert msg4.role == "assistant"
    assert msg4.sequence == 4
    assert "完全正确。如果你已经创建了一个可变借用" in msg4.content
