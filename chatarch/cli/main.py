import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from chatarch.db.database import init_db, SessionLocal
from chatarch.core.session import create_session_with_message, get_recent_sessions

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
    content: str = typer.Option(..., "--content", "-c", prompt=True, help="消息内容"),
    tags: str = typer.Option(None, "--tags", help="附加标签 (逗号分隔)"),
    model_name: str = typer.Option("manual", "--model", "-m", help="模型名称")
):
    """
    手动录入单条会话记录
    """
    db = SessionLocal()
    try:
        new_session = create_session_with_message(
            db=db,
            title=title,
            content=content,
            tags=tags,
            model_name=model_name
        )
        console.print(f"[bold green]✓ 已添加新会话：[/bold green] {new_session.title} [dim](ID: {new_session.id[:8]}...)[/dim]")
    except Exception as e:
        console.print(f"[bold red]✗ 添加失败：[/bold red] {e}")
    finally:
        db.close()
    
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
    db = SessionLocal()
    try:
        sessions = get_recent_sessions(db, limit=limit, tag=tag, starred=starred)
        
        if not sessions:
            console.print("[yellow]当前没有任何会话记录，请使用 [bold]chatasset add[/bold] 添加或使用 [bold]chatasset import[/bold] 导入。[/yellow]")
            return

        table = Table(title="最近会话概览")
        table.add_column("ID", justify="left", style="cyan", no_wrap=True)
        table.add_column("标题", style="magenta")
        table.add_column("模型", style="blue")
        table.add_column("标签", style="yellow")
        table.add_column("创建时间", justify="right", style="green")
        
        for session in sessions:
            short_id = session.id[:8]
            display_tags = session.tags if session.tags else "-"
            display_model = session.model_name if session.model_name else "-"
            created_at = session.created_at.strftime("%Y-%m-%d %H:%M")
            
            title = f"⭐ {session.title}" if session.is_starred else session.title
            
            table.add_row(short_id, title, display_model, display_tags, created_at)
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]✗ 查询失败：[/bold red] {e}")
    finally:
        db.close()

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
