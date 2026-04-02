import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint
from pathlib import Path

from chatarch.db.database import init_db, SessionLocal
from chatarch.core.session import create_session_with_message, get_recent_sessions, search_sessions_fts, get_session_by_id
from chatarch.core.parser import get_parser
from chatarch.core.exporter import get_exporter
from rich.panel import Panel
from rich.markdown import Markdown

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
    format: str = typer.Option("openai", "--format", "-f", help="导入格式: openai, markdown, txt"),
    tags: str = typer.Option("", "--tags", help="附加标签 (逗号分隔)")
):
    """
    从外部文件或目录导入聊天记录
    """
    source_path = Path(source)
    if not source_path.exists():
        console.print(f"[bold red]✗ 错误：[/bold red] 找不到路径 {source}")
        raise typer.Exit(1)

    console.print(f"正在准备从 [cyan]{source}[/cyan] 导入数据 (格式: {format})...")
    
    db = SessionLocal()
    try:
        parser = get_parser(format)
        sessions = parser.parse(source_path, default_tags=tags)
        
        if not sessions:
            console.print("[yellow]未在文件中找到任何有效的会话记录。[/yellow]")
            return

        console.print(f"解析成功，共找到 [bold green]{len(sessions)}[/bold green] 条会话，开始写入数据库...")
        
        # 批量保存到数据库，使用 Rich 进度条
        for session in track(sessions, description="正在入库..."):
            db.add(session)
        
        db.commit()
        console.print("[bold green]✓ 导入完成！[/bold green]")
        
    except ValueError as e:
        console.print(f"[bold red]✗ 解析错误：[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]✗ 导入过程中发生未知错误：[/bold red] {e}")
        db.rollback()
    finally:
        db.close()


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
    console.print(f"🔍 搜索关键词: [bold]{query}[/bold] (Role: {role or 'All'})")
    
    db = SessionLocal()
    try:
        results = search_sessions_fts(db, query, role=role)
        
        if not results:
            console.print("[yellow]未找到任何匹配的结果。[/yellow]")
            return
            
        table = Table(title=f"'{query}' 的搜索结果")
        table.add_column("ID", justify="left", style="cyan", no_wrap=True)
        table.add_column("标题", style="magenta")
        table.add_column("匹配上下文", style="green")
        
        for session, snippet in results:
            table.add_row(session.id[:8], session.title, snippet)
            
        console.print(table)
        console.print(f"\n💡 提示: 使用 [bold cyan]chatasset show <ID>[/bold cyan] 查看完整会话内容。")
        
    except Exception as e:
        console.print(f"[bold red]✗ 搜索时发生错误：[/bold red] {e}")
    finally:
        db.close()

@app.command(name="show")
def show_session(
    session_id: str = typer.Argument(..., help="会话的短 ID 或完整 ID"),
    limit: int = typer.Option(None, "--limit", "-l", help="最多显示几条消息")
):
    """
    查看具体会话详情与对话流
    """
    db = SessionLocal()
    try:
        session = get_session_by_id(db, session_id)
        
        if not session:
            console.print(f"[bold red]✗ 找不到 ID 为 {session_id} 的会话。[/bold red]")
            raise typer.Exit(1)
            
        # 打印元数据
        meta_table = Table(show_header=False, box=None)
        meta_table.add_row("[bold cyan]会话 ID:[/bold cyan]", session.id)
        meta_table.add_row("[bold cyan]标    题:[/bold cyan]", f"[bold magenta]{session.title}[/bold magenta]")
        meta_table.add_row("[bold cyan]平    台:[/bold cyan]", str(session.model_platform))
        meta_table.add_row("[bold cyan]标    签:[/bold cyan]", str(session.tags))
        meta_table.add_row("[bold cyan]创建时间:[/bold cyan]", session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(Panel(meta_table, title="会话信息", border_style="blue"))
        console.print("\n")
        
        # 打印消息
        messages = session.messages
        if limit:
            messages = messages[-limit:]
            
        for msg in messages:
            # 根据角色定义样式
            role_style = "green" if msg.role == "user" else "magenta"
            icon = "🧑" if msg.role == "user" else "🤖"
            
            # 使用 Rich 的 Markdown 渲染
            md = Markdown(msg.content)
            
            console.print(f"{icon} [bold {role_style}]{msg.role.capitalize()}[/bold {role_style}] [dim]({msg.timestamp.strftime('%H:%M:%S')})[/dim]")
            console.print(Panel(md, border_style=role_style))
            console.print()
            
    except Exception as e:
        console.print(f"[bold red]✗ 查询失败：[/bold red] {e}")
    finally:
        db.close()

@app.command(name="export")
def export_sessions(
    session_id: str = typer.Option(None, "--id", "-i", help="要导出的会话短 ID 或完整 ID"),
    tag: str = typer.Option(None, "--tag", "-t", help="按标签批量导出"),
    format: str = typer.Option("markdown", "--format", "-f", help="导出格式: markdown, md, jsonl"),
    output: str = typer.Option(..., "--output", "-o", help="导出的目标文件路径")
):
    """
    按格式将会话导出到文件
    """
    if not session_id and not tag:
        console.print("[bold red]✗ 必须指定 --id 或 --tag 中的一项以确定导出范围。[/bold red]")
        raise typer.Exit(1)
        
    db = SessionLocal()
    try:
        sessions = []
        if session_id:
            session = get_session_by_id(db, session_id)
            if not session:
                console.print(f"[bold red]✗ 找不到 ID 为 {session_id} 的会话。[/bold red]")
                raise typer.Exit(1)
            sessions.append(session)
        elif tag:
            sessions = get_recent_sessions(db, limit=1000, tag=tag) # V1 默认取前1000条
            if not sessions:
                console.print(f"[yellow]找不到带有标签 '{tag}' 的任何会话。[/yellow]")
                return
                
        output_path = Path(output)
        
        # 获取对应格式的导出器
        exporter = get_exporter(format)
        
        console.print(f"正在导出 [bold green]{len(sessions)}[/bold green] 条会话到 [cyan]{output_path}[/cyan] (格式: {format})...")
        exporter.export(sessions, output_path)
        
        console.print("[bold green]✓ 导出成功！[/bold green]")
        
    except ValueError as e:
        console.print(f"[bold red]✗ 格式错误：[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]✗ 导出失败：[/bold red] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    app()

