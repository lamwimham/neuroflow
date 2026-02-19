"""
NeuroFlow CLI - Init Command

创建新的 NeuroFlow 项目
"""

import click
from pathlib import Path


@click.command("init", help="创建新的 NeuroFlow 项目")
@click.argument("project_name", type=str)
@click.option(
    "--template", "-t",
    type=click.Choice(["minimal", "standard", "full"]),
    default="minimal",
    help="项目模板类型 (默认：minimal)\n\n"
         "minimal: 最小项目结构，适合简单项目\n"
         "standard: 标准项目结构，包含示例代码\n"
         "full: 完整项目结构，包含所有目录和配置文件",
)
@click.option(
    "--name", "-n",
    default=None,
    help="项目名称 (默认使用 project_name)",
)
@click.option(
    "--description", "-d",
    default="NeuroFlow Project",
    help="项目描述",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="覆盖已存在的目录",
)
@click.pass_context
def init_cmd(ctx, project_name, template, name, description, force):
    """
    创建新的 NeuroFlow 项目

    \b
    ═══════════════════════════════════════════════════════════
    
    示例:
        # 创建最小项目
        neuroflow init my_project
        
        # 使用标准模板
        neuroflow init my_project --template standard
        
        # 使用完整模板并指定描述
        neuroflow init my_project \\
            --template full \\
            --name "My AI Assistant" \\
            --description "智能助手项目"
    
    \b
    模板说明:
        minimal   - 最小结构 (app.py, config, agents/, tools/)
        standard  - 标准结构 (包含示例 Agent 和 Tool)
        full      - 完整结构 (包含 Skills, tests, docs 等)
    
    \b
    创建的项目结构:
        my_project/
        ├── app.py              # 主应用入口
        ├── neuroflow.toml      # 配置文件
        ├── requirements.txt    # Python 依赖
        ├── README.md          # 项目说明
        ├── agents/            # Agent 定义
        ├── tools/             # Tool 定义
        ├── skills/            # Skill 定义 (full 模板)
        └── tests/             # 测试文件 (full 模板)
    
    ═══════════════════════════════════════════════════════════
    """
    project_dir = Path(project_name)
    
    if project_dir.exists() and project_dir.is_dir():
        if not force:
            click.echo(click.style(
                f"❌ 目录 '{project_name}' 已存在", 
                fg="red"
            ))
            click.echo(click.style(
                "   使用 --force 选项覆盖已存在的目录", 
                fg="yellow"
            ))
            return
        else:
            click.echo(click.style(
                f"⚠️  覆盖已存在的目录：{project_name}", 
                fg="yellow"
            ))
    
    # 创建项目
    click.echo(f"\n📦 创建 NeuroFlow 项目：{project_name}")
    click.echo(f"   模板：{template}")
    click.echo(f"   描述：{description}\n")
    
    # 创建目录结构
    _create_project_structure(project_dir, template)
    
    # 创建配置文件
    _create_config(project_dir, name or project_name, description)
    
    # 创建示例文件
    _create_app_file(project_dir, template)
    _create_readme(project_dir, name or project_name, description)
    _create_requirements(project_dir)
    
    # 显示完成信息
    click.echo(click.style("\n✅ 项目创建成功!", fg="green"))
    click.echo(f"\n📁 项目位置：{project_dir.absolute()}")
    click.echo(f"\n📝 下一步:")
    click.echo(f"   cd {project_name}")
    click.echo(f"   pip install -r requirements.txt")
    click.echo(f"   neuroflow agent create assistant --description='智能助手'")
    click.echo(f"   neuroflow run app.py\n")


def _create_project_structure(project_dir: Path, template: str):
    """创建项目目录结构"""
    click.echo("📁 创建目录结构...")
    
    # 基础目录
    (project_dir / "agents").mkdir(parents=True, exist_ok=True)
    (project_dir / "tools").mkdir(parents=True, exist_ok=True)
    
    # 根据模板创建额外目录
    if template in ["standard", "full"]:
        (project_dir / "skills").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
    
    if template == "full":
        (project_dir / "docs").mkdir(parents=True, exist_ok=True)
        (project_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (project_dir / "config").mkdir(parents=True, exist_ok=True)
    
    # 创建 .gitkeep 文件
    for dir_path in project_dir.rglob("*"):
        if dir_path.is_dir() and dir_path.name not in [".git", "__pycache__"]:
            (dir_path / ".gitkeep").touch()


def _create_config(project_dir: Path, name: str, description: str):
    """创建配置文件"""
    click.echo("📄 创建配置文件...")
    
    config_content = f"""# NeuroFlow 项目配置

[project]
name = "{name}"
description = "{description}"
version = "0.1.0"

[agent]
default_name = "assistant"
llm_provider = "openai"  # openai, anthropic, ollama
llm_model = "gpt-4"

[tool]
max_execution_time_ms = 30000
max_parallel_calls = 5

[skill]
auto_load = true
skills_directory = "skills"

[server]
host = "127.0.0.1"
port = 8000
reload = true

[observability]
logs_level = "INFO"
tracing_enabled = true
metrics_enabled = true
"""
    (project_dir / "neuroflow.toml").write_text(config_content)


def _create_app_file(project_dir: Path, template: str):
    """创建主应用文件"""
    click.echo("📄 创建应用文件...")
    
    if template == "minimal":
        content = """\"\"\"
NeuroFlow 应用 - 最小模板
\"\"\"
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


async def main():
    # 创建 Agent
    agent = AINativeAgent(
        AINativeAgentConfig(
            name="assistant",
            llm_config=LLMConfig(
                provider="openai",
                model="gpt-4",
            ),
        )
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}!"
    
    # 处理请求
    result = await agent.handle("帮我问候张三")
    print(f"响应：{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
"""
    else:
        content = """\"\"\"
NeuroFlow 应用 - 标准模板
\"\"\"
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


async def main():
    \"\"\"主函数\"\"\"
    # 创建 Agent
    agent = AINativeAgent(
        AINativeAgentConfig(
            name="assistant",
            description="智能助手",
            llm_config=LLMConfig(
                provider="openai",
                model="gpt-4",
            ),
        )
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}!"
    
    @agent.tool(name="calculate", description="数学计算")
    async def calculate(expression: str) -> float:
        \"\"\"计算数学表达式\"\"\"
        allowed = set('0123456789+-*/(). ')
        if not all(c in allowed for c in expression):
            raise ValueError("无效的字符")
        return float(eval(expression, {"__builtins__": {}}, {}))
    
    # 测试 Agent
    print("=" * 50)
    print("测试 1: 问候")
    print("=" * 50)
    result = await agent.handle("帮我问候张三")
    print(f"响应：{result['response']}")
    
    print("\n" + "=" * 50)
    print("测试 2: 计算")
    print("=" * 50)
    result = await agent.handle("计算 123 + 456")
    print(f"响应：{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
"""
    
    (project_dir / "app.py").write_text(content)


def _create_readme(project_dir: Path, name: str, description: str):
    """创建 README 文件"""
    readme_content = f"""# {name}

{description}

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
```

### 3. 运行应用

```bash
# 运行脚本
neuroflow run app.py

# 或启动服务器
neuroflow serve --reload
```

## 项目结构

```
.
├── app.py              # 主应用入口
├── neuroflow.toml      # 配置文件
├── requirements.txt    # Python 依赖
├── agents/            # Agent 定义
├── tools/             # Tool 定义
└── skills/            # Skill 定义
```

## 常用命令

```bash
# 创建 Agent
neuroflow agent create assistant --description="智能助手"

# 创建 Skill
neuroflow skill create data-analysis \\
    --description="数据分析框架" \\
    --category data-analysis

# 创建 Tool
neuroflow tool create calculator --description="计算器"

# 运行应用
neuroflow run app.py

# 启动服务器
neuroflow serve --reload
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest

# 代码格式化
black .
isort .
```

## 许可证

MIT License
"""
    (project_dir / "README.md").write_text(readme_content)


def _create_requirements(project_dir: Path):
    """创建 requirements.txt"""
    requirements = """# NeuroFlow 核心依赖
neuroflow-sdk>=0.4.0

# LLM 提供商
openai>=1.0.0
anthropic>=0.18.0

# HTTP 客户端
aiohttp>=3.8.0

# Web 框架 (用于 serve 命令)
fastapi>=0.100.0
uvicorn>=0.20.0

# 配置和工具
pyyaml>=6.0
click>=8.0.0
pydantic>=2.0.0

# 开发依赖 (可选)
# pytest>=7.0.0
# black>=23.0.0
# isort>=5.0.0
"""
    (project_dir / "requirements.txt").write_text(requirements)
