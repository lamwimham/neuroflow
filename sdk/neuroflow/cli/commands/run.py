"""
NeuroFlow CLI - Run Command

运行 NeuroFlow 应用
"""

import click
import asyncio
import sys
from pathlib import Path


@click.command("run", help="运行 NeuroFlow 应用")
@click.argument("script", type=click.Path(exists=True))
@click.option(
    "--args", "-a",
    multiple=True,
    help="传递给脚本的参数 (可多次使用)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="启用详细模式，显示调试信息和堆栈跟踪",
)
@click.option(
    "--python-path", "-p",
    default=None,
    help="额外的 Python 路径 (多个路径用冒号分隔)",
)
@click.pass_context
def run_cmd(ctx, script, args, verbose, python_path):
    """
    运行 NeuroFlow 应用

    \b
    ═══════════════════════════════════════════════════════════
    
    运行 Python 脚本，自动执行 main() 或 async main() 函数

    \b
    示例:
        # 运行脚本
        neuroflow run app.py
        
        # 运行并传递参数
        neuroflow run script.py -a arg1 -a arg2
        
        # 详细模式
        neuroflow run app.py --verbose
        
        # 指定额外 Python 路径
        neuroflow run app.py --python-path /path/to/libs
    
    \b
    参数说明:
        script      - 要运行的 Python 脚本路径
    
    \b
    选项:
        -a, --args      传递给脚本的参数
        -v, --verbose   启用详细模式
        -p, --python-path 额外的 Python 路径
    
    \b
    运行流程:
        1. 加载指定的 Python 文件
        2. 执行模块代码
        3. 查找 main() 或 async main() 函数
        4. 运行找到的函数
        5. 显示结果或错误信息
    
    \b
    适用场景:
        ✓ 测试单个 Agent
        ✓ 运行一次性任务
        ✓ 开发和调试
        ✓ CLI 工具
        ✓ 脚本自动化
    
    \b
    不适用场景:
        ✗ 提供 HTTP API (使用 neuroflow serve)
        ✗ 持久化服务 (使用 neuroflow serve)
        ✗ 多用户访问 (使用 neuroflow serve)
    
    ═══════════════════════════════════════════════════════════
    """
    script_path = Path(script).resolve()
    
    if not script_path.exists():
        click.echo(click.style(
            f"❌ 脚本 '{script}' 未找到", 
            fg="red"
        ))
        return
    
    click.echo(f"\n🚀 运行：{script_path}")
    if args:
        click.echo(f"📝 参数：{', '.join(args)}")
    if verbose:
        click.echo(f"🔍 详细模式：已启用")
    click.echo()
    
    # 添加当前目录到 Python 路径
    sys.path.insert(0, str(script_path.parent))
    
    # 添加额外的 Python 路径
    if python_path:
        for path in python_path.split(":"):
            sys.path.insert(0, path)
    
    # 设置环境变量
    if verbose:
        import os
        os.environ["NEUROFLOW_VERBOSE"] = "1"
    
    # 导入并运行脚本
    import importlib.util
    
    try:
        spec = importlib.util.spec_from_file_location("app", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 如果有 main 函数，运行它
        if hasattr(module, "main"):
            main_func = getattr(module, "main")
            
            click.echo("⚙️  执行 main() 函数...\n")
            
            if asyncio.iscoroutinefunction(main_func):
                asyncio.run(main_func())
            else:
                main_func()
        else:
            click.echo(click.style(
                "⚠️  警告：未找到 main() 函数", 
                fg="yellow"
            ))
            click.echo("💡 提示：在脚本中添加 async def main(): 函数")
    
    except Exception as e:
        click.echo(click.style(f"❌ 运行错误：{e}", fg="red"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
