"""
neuroflow debug - 调试工具
"""
import click
import code
import asyncio
from pathlib import Path


def start_debugger(target: str = None, profile: bool = False, memory: bool = False):
    """启动调试器"""
    click.echo("🔍 NeuroFlow 调试器")
    click.echo(f"目标：{target or '交互式环境'}")
    click.echo("")
    
    if profile:
        click.echo("性能分析：启用")
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()
    
    if memory:
        click.echo("内存分析：启用")
        import tracemalloc
        tracemalloc.start()
    
    # 导入 NeuroFlow
    try:
        from neuroflow import NeuroFlowSDK, get_sdk
        click.echo("✓ NeuroFlow SDK 已加载")
    except ImportError as e:
        click.echo(f"✗ NeuroFlow SDK 加载失败：{e}")
        return
    
    # 创建交互式环境
    click.echo("")
    click.echo("调试命令:")
    click.echo("  sdk          - SDK 实例")
    click.echo("  run(code)    - 执行代码")
    click.echo("  tools        - 列出工具")
    click.echo("  agents       - 列出 Agent")
    click.echo("  exit()       - 退出调试器")
    click.echo("")
    
    # 准备上下文
    context = {
        'sdk': None,
        'run': lambda code: exec(code),
        'tools': lambda: click.echo("Tools: (暂无)"),
        'agents': lambda: click.echo("Agents: (暂无)"),
    }
    
    # 异步初始化 SDK
    async def init_sdk():
        context['sdk'] = await get_sdk()
    
    asyncio.run(init_sdk())
    
    # 启动 REPL
    code.interact(
        banner="NeuroFlow Debug Shell",
        local=context
    )
    
    # 清理
    if profile:
        profiler.disable()
        profiler.print_stats(sort='cumulative')
    
    if memory:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        click.echo(f"\n内存使用:")
        click.echo(f"  当前：{current / 1024 / 1024:.2f} MB")
        click.echo(f"  峰值：{peak / 1024 / 1024:.2f} MB")


@click.command()
@click.argument('target', required=False)
@click.option('--profile',
              is_flag=True,
              help='启用性能分析')
@click.option('--memory',
              is_flag=True,
              help='启用内存分析')
def cmd_debug(target, profile, memory):
    """调试 Agent 或工具"""
    start_debugger(target, profile, memory)
