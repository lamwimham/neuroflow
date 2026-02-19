"""
NeuroFlow CLI - Tool Commands

管理 NeuroFlow Tools
"""

import click
from pathlib import Path
import asyncio


@click.group("tool", help="Tool 管理命令")
def tool_cmd():
    """
    Tool 管理命令组

    \b
    管理 NeuroFlow Tools - 创建、列出、测试 Tool
    """
    pass


@tool_cmd.command("create", help="创建新的 Tool")
@click.argument("tool_name", type=str)
@click.option(
    "--description", "-d",
    default="工具函数",
    help="Tool 描述 (默认：工具函数)",
)
@click.option(
    "--output-dir", "-o",
    default="tools",
    help="输出目录 (默认：tools)",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="覆盖已存在的 Tool",
)
@click.pass_context
def create(ctx, tool_name, description, output_dir, force):
    """
    创建新的 Tool

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 创建基本 Tool
        neuroflow tool create calculator
        
        # 指定描述
        neuroflow tool create web_search \\
            --description="网络搜索工具"
        
        # 指定输出目录
        neuroflow tool create my_tool --output-dir custom_tools
    
    \b
    创建的 Tool 文件:
        tools/
        └── <tool_name>.py    # Tool 定义文件
    
    \b
    文件内容:
        - 工具函数定义
        - 参数说明
        - 使用示例
        - 测试代码
    
    ═══════════════════════════════════════════════════════════
    """
    tools_dir = Path(output_dir)
    tool_file = tools_dir / f"{tool_name}.py"
    
    # 检查是否已存在
    if tool_file.exists():
        if not force:
            click.echo(click.style(
                f"❌ Tool '{tool_name}' 已存在", 
                fg="red"
            ))
            click.echo(click.style(
                f"   文件：{tool_file}", 
                fg="yellow"
            ))
            click.echo(click.style(
                "   使用 --force 选项覆盖", 
                fg="yellow"
            ))
            return
        else:
            click.echo(click.style(
                f"⚠️  覆盖已存在的 Tool: {tool_name}", 
                fg="yellow"
            ))
    
    # 创建 tools 目录
    tools_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 Tool 文件
    content = _generate_tool_code(tool_name, description)
    tool_file.write_text(content)
    
    # 显示完成信息
    click.echo(click.style(f"\n✅ Tool '{tool_name}' 创建成功!", fg="green"))
    click.echo(f"\n📁 位置：{tool_file}")
    click.echo(f"\n📝 下一步:")
    click.echo(f"   1. 编辑 {tool_file} 实现工具逻辑")
    click.echo(f"   2. 测试工具：neuroflow tool test {tool_name}")
    click.echo(f"   3. 在 Agent 中使用\n")


def _generate_tool_code(name: str, description: str) -> str:
    """生成 Tool 代码"""
    return f'''\"\"\"
{name} Tool

{description}

用法:
    from tools.{name} import {name}
    result = await {name}(param1="value")
\"\"\"
import asyncio
from typing import Any, Dict, Optional


async def {name}(*args, **kwargs) -> Any:
    \"\"\"
    {description}
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
            - param1: 参数 1 说明
            - param2: 参数 2 说明
    
    Returns:
        工具执行结果
        
    Example:
        >>> result = await {name}(param1="value")
        >>> print(result)
    \"\"\"
    # TODO: 实现工具逻辑
    return {{"status": "success", "message": "TODO: 实现逻辑"}}


async def _test():
    \"\"\"测试函数\"\"\"
    print(f"测试：{name}")
    print("=" * 50)
    
    # TODO: 添加测试代码
    result = await {name}(param1="test")
    print(f"结果：{{result}}")


if __name__ == "__main__":
    asyncio.run(_test())
'''


@tool_cmd.command("list", help="列出所有 Tool")
@click.option(
    "--output-dir", "-o",
    default="tools",
    help="Tool 目录 (默认：tools)",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="输出格式 (默认：table)",
)
def list_tools(output_dir, format):
    """
    列出所有 Tool

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 列出所有 Tool
        neuroflow tool list
        
        # 指定目录
        neuroflow tool list --output-dir custom_tools
        
        # 简单格式
        neuroflow tool list --format simple
        
        # JSON 格式
        neuroflow tool list --format json
    
    \b
    输出格式:
        table   - 表格格式 (默认)
        simple  - 简单列表
        json    - JSON 格式
    
    ═══════════════════════════════════════════════════════════
    """
    tools_dir = Path(output_dir)
    
    if not tools_dir.exists():
        click.echo(click.style("❌ 未找到 tools 目录", fg="red"))
        click.echo(f"   位置：{tools_dir}")
        click.echo(click.style("   使用 'neuroflow tool create' 创建第一个 Tool", fg="yellow"))
        return
    
    # 查找所有 Tool 文件
    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if f.name != "__init__.py"]
    
    if not tool_files:
        click.echo("📭 未找到任何 Tool")
        click.echo(f"\n💡 提示：使用 'neuroflow tool create <name>' 创建第一个 Tool")
        return
    
    # 解析 Tool 信息
    tools = []
    for tool_file in tool_files:
        name = tool_file.stem
        description = "未设置"
        
        try:
            content = tool_file.read_text()
            # 简单解析描述
            if '"""' in content:
                parts = content.split('"""')
                if len(parts) > 1:
                    docstring = parts[1].strip()
                    description = docstring.split('\n')[0] or "未设置"
        except Exception:
            pass
        
        tools.append({
            "name": name,
            "description": description,
            "file": str(tool_file),
        })
    
    # 显示列表
    click.echo(f"\n📦 找到 {len(tools)} 个 Tool:\n")
    
    if format == "json":
        import json
        click.echo(json.dumps(tools, indent=2, ensure_ascii=False))
    elif format == "simple":
        for tool in tools:
            click.echo(f"  • {tool['name']} - {tool['description']}")
    else:  # table
        click.echo(f"{'名称':<25} {'描述':<40}")
        click.echo("─" * 65)
        for tool in tools:
            desc = tool['description'][:37] + "..." if len(tool['description']) > 40 else tool['description']
            click.echo(f"{tool['name']:<25} {desc:<40}")
    
    click.echo()


@tool_cmd.command("test", help="测试 Tool")
@click.argument("tool_name", type=str)
@click.option(
    "--output-dir", "-o",
    default="tools",
    help="Tool 目录 (默认：tools)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="启用详细模式",
)
def test_tool(tool_name, output_dir, verbose):
    """
    测试 Tool

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 测试 Tool
        neuroflow tool test calculator
        
        # 指定目录
        neuroflow tool test calculator --output-dir custom_tools
        
        # 详细模式
        neuroflow tool test calculator --verbose
    
    \b
    测试流程:
        1. 加载 Tool 文件
        2. 导入工具函数
        3. 执行测试代码
        4. 显示结果
    
    ═══════════════════════════════════════════════════════════
    """
    tools_dir = Path(output_dir)
    tool_file = tools_dir / f"{tool_name}.py"
    
    if not tool_file.exists():
        click.echo(click.style(f"❌ Tool '{tool_name}' 未找到", fg="red"))
        click.echo(f"   位置：{tool_file}")
        click.echo(click.style("   使用 'neuroflow tool list' 查看所有 Tool", fg="yellow"))
        return
    
    click.echo(f"\n🛠️  测试 Tool: {tool_name}")
    click.echo(f"📁 文件：{tool_file}\n")
    
    # 导入并运行 Tool
    import sys
    import importlib.util
    
    sys.path.insert(0, str(tools_dir))
    
    try:
        spec = importlib.util.spec_from_file_location(tool_name, tool_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找并运行测试函数
        if hasattr(module, "_test"):
            asyncio.run(module._test())
        else:
            click.echo(click.style("⚠️  未找到 _test() 测试函数", fg="yellow"))
            click.echo("💡 提示：在 Tool 文件中添加 async def _test(): 函数")
    
    except Exception as e:
        click.echo(click.style(f"❌ 测试失败：{e}", fg="red"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


__all__ = ["tool_cmd"]
