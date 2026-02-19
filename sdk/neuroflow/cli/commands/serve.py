"""
NeuroFlow CLI - Serve Command

启动 NeuroFlow 服务器
"""

import click
import uvicorn
from pathlib import Path


@click.command("serve", help="启动 NeuroFlow 服务器")
@click.option(
    "--host", "-h",
    default="127.0.0.1",
    show_default=True,
    help="服务器监听地址",
)
@click.option(
    "--port", "-p",
    default=8000,
    show_default=True,
    type=int,
    help="服务器端口",
)
@click.option(
    "--reload",
    is_flag=True,
    help="启用自动重载 (开发模式)",
)
@click.option(
    "--workers", "-w",
    default=None,
    type=int,
    help="工作进程数 (默认：CPU 核心数)",
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    help="配置文件路径",
)
@click.option(
    "--app", "-a",
    default="app:app",
    show_default=True,
    help="FastAPI 应用路径 (格式：module:app)",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    show_default=True,
    help="日志级别",
)
@click.pass_context
def serve_cmd(ctx, host, port, reload, workers, config, app, log_level):
    """
    启动 NeuroFlow 服务器

    \b
    ═══════════════════════════════════════════════════════════
    
    启动 FastAPI + Uvicorn Web 服务器，提供 HTTP API 接口

    \b
    示例:
        # 基本启动
        neuroflow serve
        
        # 自定义端口
        neuroflow serve --port 8080
        
        # 开发模式 (自动重载)
        neuroflow serve --reload
        
        # 生产模式 (多进程)
        neuroflow serve --workers 4
        
        # 完整配置
        neuroflow serve \\
            --host 0.0.0.0 \\
            --port 8000 \\
            --workers 4 \\
            --log-level info
    
    \b
    选项:
        -h, --host          服务器监听地址 (默认：127.0.0.1)
        -p, --port          服务器端口 (默认：8000)
        --reload            启用自动重载 (开发模式)
        -w, --workers       工作进程数
        -c, --config        配置文件路径
        -a, --app           FastAPI 应用路径
        --log-level         日志级别
    
    \b
    运行模式:
        
        开发模式:
            neuroflow serve --reload
            
            - 自动重载代码更改
            - 单进程运行
            - 详细日志
        
        生产模式:
            neuroflow serve --workers 4
            
            - 多进程运行
            - 性能优化
            - 稳定日志
    
    \b
    适用场景:
        ✓ 提供 HTTP API
        ✓ 生产环境部署
        ✓ Web 应用后端
        ✓ 多用户访问
        ✓ 需要持续运行的服务
    
    \b
    不适用场景:
        ✗ 一次性脚本 (使用 neuroflow run)
        ✗ 快速测试 (使用 neuroflow run)
        ✗ CLI 工具 (使用 neuroflow run)
    
    \b
    访问服务器:
        默认地址：http://127.0.0.1:8000
        API 文档：http://127.0.0.1:8000/docs
        ReDoc:    http://127.0.0.1:8000/redoc
    
    ═══════════════════════════════════════════════════════════
    """
    click.echo(f"\n{'='*60}")
    click.echo(f"🚀 NeuroFlow 服务器")
    click.echo(f"{'='*60}\n")
    
    # 显示配置
    click.echo(f"⚙️  配置:")
    click.echo(f"   主机：     {host}")
    click.echo(f"   端口：     {port}")
    click.echo(f"   应用：     {app}")
    click.echo(f"   日志级别： {log_level}")
    click.echo(f"   重载：     {'是' if reload else '否'}")
    
    if reload:
        click.echo(f"   进程数：   1 (重载模式下固定为 1)")
    elif workers:
        click.echo(f"   进程数：   {workers}")
    else:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        click.echo(f"   进程数：   {cpu_count} (CPU 核心数)")
    
    click.echo()
    
    # 查找应用
    if ":" in app:
        app_path = app
    else:
        app_path = find_app()
    
    if not app_path:
        click.echo(click.style("❌ 未找到 FastAPI 应用", fg="red"))
        click.echo("\n💡 提示:")
        click.echo("   1. 创建 app.py 文件并定义 FastAPI 应用")
        click.echo("   2. 或使用 --app 指定应用路径")
        click.echo("\n   示例 app.py:")
        click.echo("   ```python")
        click.echo("   from fastapi import FastAPI")
        click.echo("   app = FastAPI()")
        click.echo("   @app.get('/')")
        click.echo("   async def root(): return {'message': 'Hello'}")
        click.echo("   ```\n")
        return
    
    click.echo(f"📁 应用：{app_path}")
    click.echo()
    click.echo(f"🌐 服务器地址:")
    click.echo(f"   主地址：  http://{host}:{port}")
    click.echo(f"   API 文档：http://{host}:{port}/docs")
    click.echo(f"   ReDoc:    http://{host}:{port}/redoc")
    click.echo()
    click.echo(f"按 Ctrl+C 停止服务器\n")
    click.echo(f"{'='*60}\n")
    
    # 启动服务器
    try:
        # 确定工作进程数
        worker_count = workers
        if reload:
            worker_count = 1
        elif not worker_count:
            import multiprocessing
            worker_count = multiprocessing.cpu_count()
        
        uvicorn.run(
            app_path,
            host=host,
            port=port,
            reload=reload,
            workers=worker_count,
            log_level=log_level,
        )
    except Exception as e:
        click.echo(click.style(f"❌ 启动失败：{e}", fg="red"))
        raise SystemExit(1)


def find_app() -> str:
    """查找 FastAPI 应用"""
    # 可能的应用路径
    possible_paths = [
        "app.py",
        "main.py",
        "server.py",
        "api.py",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            module_name = Path(path).stem
            # 检查是否有 app 对象
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "app"):
                    return f"{module_name}:app"
            except Exception:
                pass
            
            # 默认返回
            return f"{module_name}:app"
    
    # 检查 agents 目录
    agents_dir = Path("agents")
    if agents_dir.exists():
        agents = list(agents_dir.glob("*.py"))
        if agents:
            agent_name = agents[0].stem
            return f"agents.{agent_name}:app"
    
    return None


__all__ = ["serve_cmd"]
