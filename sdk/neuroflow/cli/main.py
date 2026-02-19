"""
NeuroFlow CLI - 命令行工具

完整的 AI Native Agent 开发工具集
"""

import asyncio
import click
import os
import sys
from pathlib import Path

from .commands import init, agent, tool, skill, run, serve


@click.group()
@click.version_option(version="0.4.0", prog_name="neuroflow")
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="启用详细模式，显示更多调试信息",
)
@click.pass_context
def cli(ctx, verbose):
    """
    NeuroFlow CLI - AI Native Agent 开发工具

    \b
    ═══════════════════════════════════════════════════════════
    
    快速开始:
        # 1. 创建新项目
        neuroflow init my_project
        cd my_project
        
        # 2. 创建 Agent
        neuroflow agent create assistant --description="智能助手"
        
        # 3. 创建 Skill
        neuroflow skill create data-analysis \\
            --description="数据分析框架。触发词：数据分析、统计" \\
            --category data-analysis \\
            --with-scripts \\
            --assign-to assistant
        
        # 4. 创建 Tool
        neuroflow tool create calculator --description="计算器"
        
        # 5. 运行应用
        neuroflow run app.py
        
        # 6. 启动服务器
        neuroflow serve --reload
    
    \b
    常用命令:
        neuroflow --help           显示帮助信息
        neuroflow <command> --help 显示命令帮助
        neuroflow agent list       列出所有 Agent
        neuroflow skill list       列出所有 Skills
        neuroflow skill validate   验证 Skill 格式

    \b
    在线文档:
        https://github.com/lamwimham/neuroflow/docs

    ═══════════════════════════════════════════════════════════
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# 注册命令
cli.add_command(init.init_cmd)
cli.add_command(agent.agent_cmd)
cli.add_command(skill.skill_cmd)
cli.add_command(tool.tool_cmd)
cli.add_command(run.run_cmd)
cli.add_command(serve.serve_cmd)


def main():
    """CLI 入口点"""
    cli()


if __name__ == "__main__":
    main()
