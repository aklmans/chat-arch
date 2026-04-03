import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint
from pathlib import Path

from chatarch.db.database import init_db, SessionLocal
from chatarch.db.models import Session as DBSession, Message as DBMessage
from chatarch.core.session import (
    create_session_with_message, 
    get_recent_sessions, 
    search_sessions_fts, 
    get_session_by_id,
    update_session_from_text
)
from chatarch.core.parser import get_parser
from chatarch.core.exporter import get_exporter
from chatarch.core.stats import (
    get_basic_stats,
    get_platform_distribution,
    get_tag_distribution,
    get_daily_trend
)
from chatarch.core.config import load_config, save_config, CONFIG_PATH
from chatarch.core.enrich import enrich_session
from rich.panel import Panel
from rich.markdown import Markdown
from rich.columns import Columns
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import box
from rich.syntax import Syntax
from sqlalchemy import func

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
    format: str = typer.Option("openai", "--format", "-f", help="导入格式: openai, claude, markdown, txt"),
    tags: str = typer.Option("", "--tags", help="附加标签 (逗号分隔)")
):
    """
    从外部文件或目录批量导入聊天记录
    """
    source_path = Path(source)
    if not source_path.exists():
        console.print(f"[bold red]✗ 错误：[/bold red] 找不到路径 {source}")
        raise typer.Exit(1)

    console.print(f"正在准备从 [cyan]{source}[/cyan] 导入数据 (格式: {format})...")
    
    db = SessionLocal()
    try:
        parser = get_parser(format)
        
        # 收集需要处理的文件列表
        files_to_process = []
        if source_path.is_file():
            files_to_process.append(source_path)
            console.print(f"检测到单个文件，准备解析...")
        elif source_path.is_dir():
            # 根据格式推断后缀
            ext_map = {"openai": "*.json", "markdown": "*.md", "md": "*.md", "txt": "*.txt"}
            ext = ext_map.get(format.lower(), "*.*")
            files_to_process = list(source_path.rglob(ext))
            if not files_to_process:
                 console.print(f"[yellow]在目录中未找到符合格式 ({ext}) 的文件。[/yellow]")
                 return
            console.print(f"扫描到目录中 [bold cyan]{len(files_to_process)}[/bold cyan] 个待处理文件。")
            
        all_sessions = []
        for file_path in track(files_to_process, description="正在解析文件..."):
            try:
                sessions = parser.parse(file_path, default_tags=tags)
                all_sessions.extend(sessions)
            except Exception as e:
                console.print(f"[yellow]⚠ 解析文件 {file_path.name} 时跳过: {e}[/yellow]")
        
        if not all_sessions:
            console.print("[yellow]未在文件中找到任何有效的会话记录。[/yellow]")
            return

        console.print(f"解析成功，共提取到 [bold green]{len(all_sessions)}[/bold green] 条会话，开始写入数据库...")
        
        # 批量保存到数据库
        for session in track(all_sessions, description="正在入库..."):
            db.add(session)
        
        db.commit()
        console.print(f"[bold green]✓ 导入完成！成功入库 {len(all_sessions)} 条会话。[/bold green]")
        
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

@app.command(name="edit")
def edit_session(
    session_id: str = typer.Argument(..., help="要编辑的会话短 ID 或完整 ID")
):
    """
    调用系统默认编辑器修改现有会话 (脱敏、删减废话)
    """
    db = SessionLocal()
    try:
        session = get_session_by_id(db, session_id)
        if not session:
            console.print(f"[bold red]✗ 找不到 ID 为 {session_id} 的会话。[/bold red]")
            raise typer.Exit(1)
            
        # 构建初始的 Markdown 内容以供编辑
        lines = []
        lines.append(f"# {session.title or '未命名会话'}\n")
        
        for msg in session.messages:
            lines.append(f"### {msg.role.capitalize()}\n")
            lines.append(f"{msg.content}\n")
            
        initial_text = "\n".join(lines)
        
        console.print("[cyan]正在启动系统编辑器 (请保存并关闭文件以完成修改)...[/cyan]")
        
        import click
        edited_text = click.edit(text=initial_text, extension=".md")
        
        if edited_text is None or edited_text.strip() == initial_text.strip():
            console.print("[yellow]文本未发生任何更改，取消保存。[/yellow]")
            return
            
        # 使用 Markdown 解析器重新提取内容并覆盖更新
        update_session_from_text(db, session, edited_text)
        
        console.print(f"[bold green]✓ 修改已保存！当前版本为 v{session.version}[/bold green]")
        
    except ValueError as e:
         console.print(f"[bold red]✗ 保存失败（数据格式错误）：[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]✗ 发生未知错误：[/bold red] {e}")
    finally:
        db.close()

@app.command(name="stats")
def show_stats():
    """
    查看知识库的资产统计看板
    """
    db = SessionLocal()
    try:
        basic_stats = get_basic_stats(db)
        if basic_stats["total_sessions"] == 0:
            console.print(Panel("当前数据库为空，没有可统计的数据。快去导入一些聊天记录吧！", style="yellow", border_style="yellow"))
            return
            
        # --- 头部标题 ---
        title = Text("📊 ChatArch 资产统计看板", style="bold white on blue", justify="center")
        console.print(Panel(title, box=box.DOUBLE_EDGE, border_style="blue"))
        console.print()

        # --- 1. 基础信息面板 (并排显示) ---
        # 获取 Token 估算值
        token_count = db.query(func.sum(DBSession.token_count)).scalar() or 0
        # 获取消息表的 token 总和（如果需要合并的话），这里简单估算会话字数
        
        p1 = Panel(Align.center(Text(str(basic_stats['total_sessions']), style="bold green", justify="center")), title="[b]总会话数[/b]", border_style="green", padding=(1, 5))
        p2 = Panel(Align.center(Text(str(basic_stats['total_messages']), style="bold cyan", justify="center")), title="[b]总消息数[/b]", border_style="cyan", padding=(1, 5))
        p3 = Panel(Align.center(Text(str(token_count), style="bold yellow", justify="center")), title="[b]预估 Token[/b]", border_style="yellow", padding=(1, 5))

        console.print(Columns([p1, p2, p3], expand=True))
        console.print()

        # --- 2. 中间布局：平台分布与热门标签 ---
        platforms = get_platform_distribution(db)
        plat_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAD, expand=True)
        plat_table.add_column("平台", style="cyan")
        plat_table.add_column("数量", justify="right", style="bold green")
        for plat, count in platforms:
            pct = (count / basic_stats['total_sessions']) * 100
            plat_table.add_row(f"🌍 {plat}", f"{count} [dim]({pct:.1f}%)[/dim]")
            
        tags = get_tag_distribution(db, limit=10)
        tag_table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE_HEAD, expand=True)
        tag_table.add_column("标签", style="cyan")
        tag_table.add_column("引用数", justify="right", style="bold green")
        for tag, count in tags:
            tag_table.add_row(f"🏷️ {tag}", str(count))

        p_plat = Panel(plat_table, title="[b]来源平台分布[/b]", border_style="magenta", padding=(1, 2))
        p_tag = Panel(tag_table, title="[b]热门标签 TOP 10[/b]", border_style="yellow", padding=(1, 2))
        
        console.print(Columns([p_plat, p_tag], expand=True))
        console.print()
        
        # --- 3. 底部布局：近期活跃趋势 ---
        trend = get_daily_trend(db, days=14)
        if trend:
            trend_table = Table(show_header=False, box=None, padding=(0, 2))
            trend_table.add_column("日期", style="dim", width=12)
            trend_table.add_column("柱状图", width=40)
            trend_table.add_column("新增量", justify="right", style="bold green")
            
            max_count = max(count for _, count in trend)
            
            for day, count in trend:
                # 渐变柱状图效果
                bar_len = int((count / max_count) * 30) if max_count > 0 else 0
                bar_str = "█" * bar_len
                
                # 根据高度动态着色
                if bar_len > 20:
                    bar_style = "bold green"
                elif bar_len > 10:
                    bar_style = "bold yellow"
                else:
                    bar_style = "bold red"
                
                bar_text = Text(bar_str, style=bar_style)
                trend_table.add_row(day, bar_text, str(count))
                
            console.print(Panel(trend_table, title="[b]📈 近 14 天资产入库活跃度[/b]", border_style="cyan", padding=(1, 2)))
        
    except Exception as e:
        console.print(f"[bold red]✗ 统计失败：[/bold red] {e}")
    finally:
        db.close()

@app.command(name="enrich")
def enrich_session_cmd(
    session_id: str = typer.Argument(..., help="要提炼的会话 ID"),
    provider: str = typer.Option(None, "--provider", "-p", help="指定 LLM 提供商 (如: kimi, claude-code, ollama)")
):
    """
    🧠 AI 智能提炼：自动为会话生成摘要和推荐标签
    """
    db = SessionLocal()
    try:
        session = get_session_by_id(db, session_id)
        if not session:
            console.print(f"[bold red]✗ 找不到 ID 为 {session_id} 的会话。[/bold red]")
            raise typer.Exit(1)
            
        console.print(f"正在调用 [bold cyan]{provider or '默认'}[/bold cyan] AI 引擎对会话 [magenta]'{session.title}'[/magenta] 进行提炼...")
        
        # 实时获取 AI 生成的摘要和标签
        result = enrich_session(session, provider_name=provider)
        
        new_summary = result.get("summary")
        new_tags = result.get("tags", [])
        
        # 更新数据库中的会话
        session.summary = new_summary
        
        # 合并旧标签和新推荐的标签（去重）
        existing_tags = set([t.strip() for t in session.tags.split(",") if t.strip()]) if session.tags else set()
        updated_tags = existing_tags.union(set(new_tags))
        session.tags = ", ".join(sorted(list(updated_tags)))
        
        db.commit()
        
        # 结果展示
        console.print(Panel(f"[bold green]摘要:[/bold green]\n{new_summary}\n\n[bold yellow]推荐标签:[/bold yellow]\n{', '.join(new_tags)}", title="✨ AI 提炼结果", border_style="green"))
        console.print(f"[dim]已更新入库。当前所有标签: {session.tags}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]✗ AI 提炼失败：[/bold red] {e}")
    finally:
        db.close()

@app.command(name="config")
def config_cmd(
    edit: bool = typer.Option(False, "--edit", "-e", help="直接调用编辑器修改配置"),
    show: bool = typer.Option(True, "--show", help="在终端显示当前配置")
):
    """
    ⚙️ 管理 ChatArch 配置文件 (LLM 提供商、API Key 等)
    """
    if edit:
        import click
        click.launch(str(CONFIG_PATH))
        console.print(f"[green]已尝试打开配置文件: {CONFIG_PATH}[/green]")
        return
        
    config = load_config()
    if show:
        import yaml
        yaml_str = yaml.dump(config, allow_unicode=True, sort_keys=False)
        console.print(Panel(Syntax(yaml_str, "yaml", theme="monokai"), title=f"配置文件: {CONFIG_PATH}", border_style="blue"))
        console.print("\n💡 提示: 使用 [bold cyan]chatasset config --edit[/bold cyan] 快速修改 API Key。")

if __name__ == "__main__":
    app()

