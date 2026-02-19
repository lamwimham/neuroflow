"""
neuroflow new - 创建新项目
"""
import click
import shutil
from pathlib import Path
import json


# 项目模板
TEMPLATES = {
    'basic': {
        'description': '基础 Agent 项目',
        'files': {
            'agents/__init__.py': '''"""Agents 模块"""
''',
            'agents/hello_agent.py': '''"""问候 Agent 示例"""
from neuroflow import agent, tool

@tool(name="greet", description="问候某人")
async def greet(name: str) -> str:
    """问候工具"""
    return f"Hello, {name}!"

@agent(name="hello_agent", description="简单的问候 Agent")
class HelloAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求"""
        from neuroflow import NeuroFlowSDK
        sdk = await NeuroFlowSDK.create()
        
        name = request.get("name", "World")
        greeting = await sdk.execute_tool("greet", name=name)
        
        await sdk.shutdown()
        return {"greeting": greeting}
''',
            'tools/__init__.py': '''"""Tools 模块"""
''',
            'tools/basic_tools.py': '''"""基础工具示例"""
from neuroflow import tool

@tool(name="calculate", description="数学计算器")
async def calculate(expression: str) -> float:
    """计算数学表达式"""
    # 安全检查
    allowed = set('0123456789+-*/(). ')
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters")
    return float(eval(expression, {"__builtins__": {}}, {}))

@tool(name="echo", description="回显工具")
async def echo(message: str) -> str:
    """回显消息"""
    return message
''',
            'config/neuroflow.yaml': '''# NeuroFlow 配置文件

server:
  port: 8080
  host: 127.0.0.1

sandbox:
  max_instances: 10
  memory_limit_mb: 256
  timeout_ms: 30000

observability:
  tracing_enabled: true
  metrics_enabled: true
  log_level: info
''',
            'tests/__init__.py': '''"""Tests 模块"""
''',
            'tests/test_agents.py': '''"""Agent 测试"""
import pytest
import asyncio
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_hello_agent():
    """测试问候 Agent"""
    from agents.hello_agent import HelloAgent
    
    sdk = await NeuroFlowSDK.create()
    agent = HelloAgent()
    
    result = await agent.handle({"name": "Test"})
    
    assert "greeting" in result
    assert "Hello" in result["greeting"]
    
    await sdk.shutdown()
''',
            'requirements.txt': '''neuroflow>=0.3.0
pytest>=7.0.0
pytest-asyncio>=0.20.0
''',
            'README.md': '''# {{project_name}}

使用 NeuroFlow 创建的 AI Agent 项目

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行 Agent

```bash
neuroflow run
```

### 3. 测试

```bash
pytest
```

## 项目结构

```
{{project_name}}/
├── agents/          # Agent 定义
├── tools/           # 工具定义
├── config/          # 配置文件
├── tests/           # 测试文件
└── README.md
```

## 开发

编辑 `agents/hello_agent.py` 添加你的 Agent 逻辑。

## 许可证

MIT
''',
            '.gitignore': '''__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
''',
        }
    },
    
    'trading': {
        'description': '交易 Agent 项目',
        'files': {
            'agents/trading_agent.py': '''"""交易 Agent 示例"""
from neuroflow import agent

@agent(name="trading_agent", description="交易 Agent")
class TradingAgent:
    async def handle(self, request: dict) -> dict:
        """处理交易请求"""
        action = request.get("action")
        symbol = request.get("symbol")
        amount = request.get("amount")
        
        if action == "buy":
            return await self.buy(symbol, amount)
        elif action == "sell":
            return await self.sell(symbol, amount)
        else:
            return {"error": "Unknown action"}
    
    async def buy(self, symbol: str, amount: float) -> dict:
        """买入逻辑"""
        return {
            "action": "buy",
            "symbol": symbol,
            "amount": amount,
            "status": "executed"
        }
    
    async def sell(self, symbol: str, amount: float) -> dict:
        """卖出逻辑"""
        return {
            "action": "sell",
            "symbol": symbol,
            "amount": amount,
            "status": "executed"
        }
''',
            # 其他文件同 basic 模板...
        }
    },
    
    'data-processing': {
        'description': '数据处理 Agent 项目',
        'files': {
            'agents/data_agent.py': '''"""数据处理 Agent 示例"""
from neuroflow import agent, tool

@tool(name="process_data", description="处理数据")
async def process_data(data: list) -> list:
    """处理数据列表"""
    return [item * 2 for item in data]

@agent(name="data_agent", description="数据处理 Agent")
class DataAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求"""
        from neuroflow import NeuroFlowSDK
        sdk = await NeuroFlowSDK.create()
        
        data = request.get("data", [1, 2, 3])
        result = await sdk.execute_tool("process_data", data=data)
        
        await sdk.shutdown()
        return {"result": result}
''',
            # 其他文件同 basic 模板...
        }
    }
}


def create_project(project_name: str, template: str, dest: str = None):
    """创建项目"""
    # 确定目标目录
    if dest:
        target_dir = Path(dest)
    else:
        target_dir = Path.cwd() / project_name
    
    # 检查目录是否存在
    if target_dir.exists():
        click.echo(f"❌ 目录已存在：{target_dir}")
        return False
    
    # 创建目录
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取模板
    tpl = TEMPLATES.get(template, TEMPLATES['basic'])
    
    # 创建文件
    for file_path, content in tpl['files'].items():
        full_path = target_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 替换模板变量
        content = content.replace('{{project_name}}', project_name)
        
        full_path.write_text(content, encoding='utf-8')
    
    # 显示成功消息
    click.echo(f"✅ 项目创建成功：{target_dir}")
    click.echo("")
    click.echo("下一步:")
    click.echo(f"  cd {target_dir}")
    click.echo("  pip install -r requirements.txt")
    click.echo("  neuroflow run")
    click.echo("")
    
    return True


@click.command()
@click.argument('project_name')
@click.option('--template', '-t',
              type=click.Choice(['basic', 'trading', 'data-processing']),
              default='basic',
              help='项目模板')
@click.option('--dest', '-d',
              type=click.Path(),
              default=None,
              help='目标目录')
def cmd_new(project_name, template, dest):
    """创建新的 NeuroFlow 项目"""
    import click
    
    click.echo(f"🚀 创建 NeuroFlow 项目：{project_name}")
    click.echo(f"模板：{template}")
    click.echo("")
    
    success = create_project(project_name, template, dest)
    
    if not success:
        import sys
        sys.exit(1)
