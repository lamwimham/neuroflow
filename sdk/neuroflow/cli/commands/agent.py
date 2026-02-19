"""
NeuroFlow CLI - Agent Commands

管理 NeuroFlow Agents
"""

import click
from pathlib import Path
import asyncio
from neuroflow.templates.template_renderer import TemplateRenderer


@click.group("agent", help="Agent 管理命令")
def agent_cmd():
    """
    Agent 管理命令组

    \b
    管理 NeuroFlow Agents - 创建、列出、运行 Agent
    """
    pass


@agent_cmd.command("create", help="创建新的 Agent")
@click.argument("agent_name", type=str)
@click.option(
    "--description", "-d",
    default="智能助手",
    help="Agent 描述 (默认：智能助手)",
)
@click.option(
    "--template", "-t",
    type=click.Choice(["basic", "standard", "advanced"]),
    default="standard",
    help="Agent 模板类型 (默认：standard)",
)
@click.option(
    "--llm-provider",
    type=click.Choice([
        "openai", "anthropic", "ollama",  # 国际厂商
        "deepseek", "zhipu", "baichuan",  # 国产大模型
        "qwen", "moonshot", "minimax",    # 国产大模型
    ]),
    default="openai",
    help="LLM 提供商 (默认：openai)",
)
@click.option(
    "--model", "-m",
    default=None,
    help="LLM 模型 (默认根据 provider 自动选择)",
)
@click.option(
    "--output-dir", "-o",
    default="agents",
    help="输出目录 (默认：agents)",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="覆盖已存在的 Agent",
)
@click.pass_context
def create(ctx, agent_name, description, template, llm_provider, model, output_dir, force):
    """
    创建新的 Agent

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 创建基本 Agent
        neuroflow agent create assistant
        
        # 指定描述和 LLM 提供商
        neuroflow agent create analyst \\
            --description="数据分析专家" \\
            --llm-provider anthropic
        
        # 指定模型
        neuroflow agent create coder \\
            --description="代码专家" \\
            --llm-provider openai \\
            --model "gpt-4"
    
    \b
    LLM 提供商:
        国际厂商:
            openai     - OpenAI (GPT-3.5, GPT-4, GPT-4o)
            anthropic  - Anthropic (Claude 2, Claude 3)
            ollama     - Ollama (本地模型)
        
        国产大模型:
            deepseek   - 深度求索 (DeepSeek)
            zhipu      - 智谱 AI (GLM-4)
            baichuan   - 百川智能 (Baichuan)
            qwen       - 阿里云 (通义千问)
            moonshot   - 月之暗面 (Kimi)
            minimax    - MiniMax (ABAB)

    \b
    默认模型:
        openai     - gpt-3.5-turbo
        anthropic  - claude-3-sonnet-20240229
        ollama     - llama2
        deepseek   - deepseek-chat
        zhipu      - glm-4
        baichuan   - Baichuan4
        qwen       - qwen-max
        moonshot   - moonshot-v1-8k
        minimax    - abab6.5s

    \b
    创建的 Agent 目录:
        agents/
        └── <agent_name>/
            ├── <agent_name>.py    # Agent 主文件
            ├── AGENT.md           # Agent 文档
            ├── config.yaml        # 配置文件
            ├── requirements.txt   # 依赖列表
            ├── scripts/           # 脚本目录
            └── workspace/         # 工作空间

    ═══════════════════════════════════════════════════════════
    """
    agents_dir = Path(output_dir)
    agent_dir = agents_dir / agent_name

    # 检查是否已存在
    if agent_dir.exists():
        if not force:
            click.echo(click.style(
                f"❌ Agent '{agent_name}' 已存在",
                fg="red"
            ))
            click.echo(click.style(
                f"   目录：{agent_dir}",
                fg="yellow"
            ))
            click.echo(click.style(
                "   使用 --force 选项覆盖",
                fg="yellow"
            ))
            return
        else:
            click.echo(click.style(
                f"⚠️  覆盖已存在的 Agent: {agent_name}",
                fg="yellow"
            ))

    # 创建 agents 目录
    agents_dir.mkdir(parents=True, exist_ok=True)

    # 选择默认模型
    if not model:
        models = {
            # 国际厂商
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229",
            "ollama": "llama2",
            # 国产大模型
            "deepseek": "deepseek-chat",
            "zhipu": "glm-4",
            "baichuan": "Baichuan4",
            "qwen": "qwen-max",
            "moonshot": "moonshot-v1-8k",
            "minimax": "abab6.5s",
        }
        model = models.get(llm_provider, "gpt-3.5-turbo")

    # 使用模板系统创建 Agent 目录结构
    try:
        renderer = TemplateRenderer(template_name=template)
        renderer.render(
            output_dir=agent_dir,
            variables={
                "agent_name": agent_name,
                "agent_class_name": agent_name.replace("-", "_").title().replace("_", ""),
                "description": description,
                "llm_provider": llm_provider,
                "llm_model": model,
            },
            overwrite=force,
        )
    except Exception as e:
        click.echo(click.style(f"❌ 创建 Agent 失败：{e}", fg="red"))
        return

    # 显示完成信息
    click.echo(click.style(f"\n✅ Agent '{agent_name}' 创建成功!", fg="green"))
    click.echo(f"\n📁 位置：{agent_dir}")
    click.echo(f"\n📂 目录结构:")
    click.echo(f"   {agent_name}/")
    click.echo(f"   ├── {agent_name}.py      # Agent 主文件")
    click.echo(f"   ├── AGENT.md            # Agent 文档")
    click.echo(f"   ├── config.yaml         # 配置文件")
    click.echo(f"   ├── requirements.txt    # 依赖列表")
    click.echo(f"   ├── scripts/            # 脚本目录")
    click.echo(f"   └── workspace/          # 工作空间")
    click.echo(f"\n📝 下一步:")
    click.echo(f"   1. cd {agent_dir}")
    click.echo(f"   2. 编辑 {agent_name}.py 添加自定义工具")
    click.echo(f"   3. pip install -r requirements.txt")
    click.echo(f"   4. 设置环境变量：export {llm_provider.upper()}_API_KEY=your-key")
    click.echo(f"   5. python {agent_name}.py\n")


def _generate_agent_code(name: str, description: str, provider: str, model: str) -> str:
    """生成 Agent 代码"""
    return f'''\"\"\"
{name} Agent

{description}
\"\"\"
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


class {name.replace("-", "_").title().replace("_", "")}Agent(AINativeAgent):
    """
    {description}
    """
    
    def __init__(self):
        super().__init__(
            AINativeAgentConfig(
                name="{name}",
                description="{description}",
                llm_config=LLMConfig(
                    provider="{provider}",
                    model="{model}",
                ),
            )
        )
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            """问候用户"""
            return f"你好，{{name}}! 我是{name}，很高兴为你服务。"
    
    async def handle_request(self, user_message: str) -> dict:
        """
        处理用户请求
        
        Args:
            user_message: 用户消息
            
        Returns:
            响应字典
        """
        return await self.handle(user_message)


async def main():
    """测试 Agent"""
    agent = {name.replace("-", "_").title().replace("_", "")}Agent()
    
    # 测试
    print("=" * 50)
    print(f"测试：{{agent.config.description}}")
    print("=" * 50)
    
    result = await agent.handle_request("你好")
    print(f"响应：{{result['response']}}")


if __name__ == "__main__":
    asyncio.run(main())
'''


@agent_cmd.command("list", help="列出所有 Agent")
@click.option(
    "--output-dir", "-o",
    default="agents",
    help="Agent 目录 (默认：agents)",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="输出格式 (默认：table)",
)
def list_agents(output_dir, format):
    """
    列出所有 Agent

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 列出所有 Agent
        neuroflow agent list
        
        # 指定目录
        neuroflow agent list --output-dir custom_agents
        
        # 简单格式输出
        neuroflow agent list --format simple
        
        # JSON 格式输出
        neuroflow agent list --format json
    
    \b
    输出格式:
        table   - 表格格式 (默认)
        simple  - 简单列表
        json    - JSON 格式
    
    ═══════════════════════════════════════════════════════════
    """
    agents_dir = Path(output_dir)
    
    if not agents_dir.exists():
        click.echo(click.style("❌ 未找到 agents 目录", fg="red"))
        click.echo(f"   位置：{agents_dir}")
        click.echo(click.style("   使用 'neuroflow agent create' 创建第一个 Agent", fg="yellow"))
        return
    
    # 查找所有 Agent 文件
    agent_files = list(agents_dir.glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        click.echo("📭 未找到任何 Agent")
        click.echo(f"\n💡 提示：使用 'neuroflow agent create <name>' 创建第一个 Agent")
        return
    
    # 解析 Agent 信息
    agents = []
    for agent_file in agent_files:
        try:
            content = agent_file.read_text()
            # 简单解析
            name = agent_file.stem
            description = "未设置"
            
            # 尝试从 docstring 或描述中提取
            if 'description="' in content:
                desc_start = content.find('description="') + len('description="')
                desc_end = content.find('"', desc_start)
                if desc_end > desc_start:
                    description = content[desc_start:desc_end]
            
            agents.append({
                "name": name,
                "description": description,
                "file": str(agent_file),
            })
        except Exception as e:
            click.echo(click.style(f"⚠️  读取 {agent_file} 失败：{e}", fg="yellow"))
    
    # 显示列表
    click.echo(f"\n📦 找到 {len(agents)} 个 Agent:\n")
    
    if format == "json":
        import json
        click.echo(json.dumps(agents, indent=2, ensure_ascii=False))
    elif format == "simple":
        for agent in agents:
            click.echo(f"  • {agent['name']} - {agent['description']}")
    else:  # table
        click.echo(f"{'名称':<25} {'描述':<40}")
        click.echo("─" * 65)
        for agent in agents:
            desc = agent['description'][:37] + "..." if len(agent['description']) > 40 else agent['description']
            click.echo(f"{agent['name']:<25} {desc:<40}")
    
    click.echo()


@agent_cmd.command("run", help="运行 Agent")
@click.argument("agent_name", type=str)
@click.argument("message", type=str, default="你好")
@click.option(
    "--output-dir", "-o",
    default="agents",
    help="Agent 目录 (默认：agents)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="启用详细模式",
)
def run_agent(agent_name, message, output_dir, verbose):
    """
    运行 Agent

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 运行 Agent 并发送消息
        neuroflow agent run assistant "你好"
        
        # 运行指定目录的 Agent
        neuroflow agent run assistant "你好" --output-dir custom_agents
        
        # 详细模式
        neuroflow agent run assistant "分析这个数据" --verbose
    
    \b
    参数说明:
        agent_name  - Agent 名称 (文件名，不含 .py)
        message     - 发送给 Agent 的消息 (默认："你好")
    
    \b
    运行流程:
        1. 加载 Agent 文件
        2. 实例化 Agent
        3. 调用 agent.handle(message)
        4. 显示结果
    
    ═══════════════════════════════════════════════════════════
    """
    agents_dir = Path(output_dir)
    agent_file = agents_dir / f"{agent_name}.py"
    
    if not agent_file.exists():
        click.echo(click.style(f"❌ Agent '{agent_name}' 未找到", fg="red"))
        click.echo(f"   位置：{agent_file}")
        click.echo(click.style("   使用 'neuroflow agent list' 查看所有 Agent", fg="yellow"))
        return
    
    click.echo(f"\n🤖 运行 Agent: {agent_name}")
    click.echo(f"💬 消息：{message}")
    click.echo(f"📁 文件：{agent_file}\n")
    
    # 导入并运行 Agent
    import sys
    import importlib.util
    
    sys.path.insert(0, str(agents_dir))
    
    try:
        spec = importlib.util.spec_from_file_location(agent_name, agent_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找 Agent 类
        agent_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and "Agent" in name and name != "AINativeAgent":
                agent_class = obj
                break
        
        if not agent_class:
            click.echo(click.style("❌ 未找到 Agent 类", fg="red"))
            return
        
        # 创建 Agent 实例
        agent = agent_class()
        
        # 运行
        async def run():
            result = await agent.handle(message)
            
            click.echo("\n" + "=" * 50)
            click.echo("响应:")
            click.echo("=" * 50)
            click.echo(result.get("response", "无响应"))
            
            if result.get("tool_results"):
                click.echo(f"\n🛠️  使用的工具：{len(result['tool_results'])} 个")
                for tool_result in result["tool_results"]:
                    status = "✅" if tool_result.get("success") else "❌"
                    click.echo(f"   {status} {tool_result.get('tool', 'unknown')}")
            
            if verbose and result.get("turns_taken"):
                click.echo(f"\n📊 统计:")
                click.echo(f"   轮数：{result['turns_taken']}")
        
        asyncio.run(run())
        
    except Exception as e:
        click.echo(click.style(f"❌ 运行失败：{e}", fg="red"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@agent_cmd.command("show", help="显示 Agent 详情")
@click.argument("agent_name", type=str)
@click.option(
    "--output-dir", "-o",
    default="agents",
    help="Agent 目录 (默认：agents)",
)
def show_agent(agent_name, output_dir):
    """
    显示 Agent 详情

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 显示 Agent 详情
        neuroflow agent show assistant
        
        # 显示指定目录的 Agent
        neuroflow agent show assistant --output-dir custom_agents
    
    \b
    显示内容:
        - Agent 名称
        - 描述
        - LLM 配置
        - 注册的工具
        - 文件位置
    
    ═══════════════════════════════════════════════════════════
    """
    agents_dir = Path(output_dir)
    agent_file = agents_dir / f"{agent_name}.py"
    
    if not agent_file.exists():
        click.echo(click.style(f"❌ Agent '{agent_name}' 未找到", fg="red"))
        return
    
    content = agent_file.read_text()
    
    # 解析信息
    info = {
        "name": agent_name,
        "file": str(agent_file),
        "description": "未设置",
        "provider": "unknown",
        "model": "unknown",
        "tools": [],
    }
    
    # 简单解析
    if 'description="' in content:
        desc_start = content.find('description="') + len('description="')
        desc_end = content.find('"', desc_start)
        if desc_end > desc_start:
            info["description"] = content[desc_start:desc_end]
    
    if 'provider="' in content:
        prov_start = content.find('provider="') + len('provider="')
        prov_end = content.find('"', prov_start)
        if prov_end > prov_start:
            info["provider"] = content[prov_start:prov_end]
    
    if 'model="' in content:
        model_start = content.find('model="') + len('model="')
        model_end = content.find('"', model_start)
        if model_end > model_start:
            info["model"] = content[model_start:model_end]
    
    # 查找工具
    import re
    tool_matches = re.findall(r'@self\.tool\(name="([^"]+)", description="([^"]+)"\)', content)
    info["tools"] = tool_matches
    
    # 显示详情
    click.echo(f"\n{'='*60}")
    click.echo(f"Agent: {info['name']}")
    click.echo(f"{'='*60}\n")
    
    click.echo(f"📝 描述：    {info['description']}")
    click.echo(f"🤖 提供商：  {info['provider']}")
    click.echo(f"🧠 模型：    {info['model']}")
    click.echo(f"📁 文件：    {info['file']}")
    
    if info["tools"]:
        click.echo(f"\n🛠️  工具 ({len(info['tools'])} 个):")
        for tool_name, tool_desc in info["tools"]:
            click.echo(f"   • {tool_name} - {tool_desc}")
    
    click.echo()


__all__ = ["agent_cmd"]
