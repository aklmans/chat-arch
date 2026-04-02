import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from chatarch.db.database import init_db

app = typer.Typer(help="ChatArch: 聊天资产管理 CLI 工具")
console = Console()

@app.callback()
def main_callback():
    """
    ChatArch - 将零散的聊天记录转化为结构化的知识资产。
    """
    # 确保数据库与表创建
    init_db()

@app.command(name="add")
def add_session(
    title: str = typer.Option(..., "--title", "-t", prompt=True, help="会话标题"),
    content: str = typer.Option(..., "--content", "-c", prompt=True, help="消息内容")
):
    """
    手动录入单条会话记录
    """
    console.print(f"[bold green]✓ 已添加新会话：[/bold green] {title}")
    # TODO: 实现数据库插入逻辑
    
@app.command(name="import")
def import_sessions(
    source: str = typer.Option(..., "--source", "-s", help="文件或目录路径"),
    format: str = typer.Option("markdown", "--format", "-f", help="导入格式: openai, markdown, txt"),
    tags: str = typer.Option("", "--tags", help="附加标签 (逗号分隔)")
):
    """
    从外部文件或目录导入聊天记录
    """
    console.print(f"正在从 [cyan]{source}[/cyan] 导入数据 (格式: {format})...")
    # TODO: 实现解析器与入库逻辑

@app.command(name="list")
def list_sessions(
    limit: int = typer.Option(10, "--limit", "-l", help="显示条数"),
    tag: str = typer.Option(None, "--tag", help="按标签过滤"),
    starred: bool = typer.Option(False, "--starred", help="只显示收藏")
):
    """
    列出最近的会话概览
    """
    table = Table(title="最近会话概览")
    table.add_column("ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("标题", style="magenta")
    table.add_column("创建时间", justify="right", style="green")
    
    # 占位：目前暂无真实查询
    table.add_row("abc-123", "CLI 工具设计讨论", "2026-04-02")
    table.add_row("def-456", "Rust 异步模型探究", "2026-04-01")
    
    console.print(table)

@app.command(name="search")
def search_sessions(
    query: str = typer.Argument(..., help="搜索关键词"),
    role: str = typer.Option(None, "--role", help="按角色过滤 (user/assistant)"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式 (table/json)")
):
    """
    全文检索历史对话
    """
    console.print(f"🔍 搜索关键词: [bold]{query}[/bold]")
    # TODO: 接入 FTS5 检索逻辑

if __name__ == "__main__":
    app()
