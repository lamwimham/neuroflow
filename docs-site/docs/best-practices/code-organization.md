# 代码组织

NeuroFlow 项目代码组织最佳实践。

## 项目结构

### 推荐结构

```
my_project/
├── agents/                 # Agent 定义
│   ├── __init__.py
│   ├── assistant.py       # 助手 Agent
│   ├── analyst.py         # 分析 Agent
│   └── support.py         # 客服 Agent
├── tools/                  # 工具定义
│   ├── __init__.py
│   ├── calculator.py      # 计算工具
│   ├── search.py          # 搜索工具
│   └── database.py        # 数据库工具
├── skills/                 # 技能定义
│   ├── __init__.py
│   └── nlp.py            # NLP 技能
├── config/                 # 配置文件
│   ├── neuroflow.toml     # 主配置
│   └── environments/      # 环境配置
│       ├── dev.toml
│       └── prod.toml
├── tests/                  # 测试文件
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_tools.py
├── scripts/                # 脚本文件
│   ├── setup.sh
│   └── deploy.sh
├── app.py                  # 应用入口
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明
```

## Agent 组织

### 按功能分组

```
agents/
├── __init__.py
├── customer_service/       # 客服相关
│   ├── __init__.py
│   ├── support_agent.py
│   └── sales_agent.py
├── data/                   # 数据相关
│   ├── __init__.py
│   ├── analyst_agent.py
│   └── report_agent.py
└── utils/                  # 工具 Agent
    ├── __init__.py
    └── scheduler_agent.py
```

### Agent 基类

```python
# agents/base.py
from neuroflow import AINativeAgent, AINativeAgentConfig

class BaseAgent(AINativeAgent):
    """所有 Agent 的基类"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(
            AINativeAgentConfig(
                name=name,
                description=description,
            )
        )
    
    async def handle_request(self, request: dict) -> dict:
        """处理请求的模板方法"""
        try:
            return await self._process(request)
        except Exception as e:
            return {"error": str(e)}
    
    async def _process(self, request: dict) -> dict:
        """子类实现"""
        raise NotImplementedError
```

## 工具组织

### 按类别分组

```
tools/
├── __init__.py
├── computation/            # 计算类
│   ├── __init__.py
│   ├── calculator.py
│   └── converter.py
├── communication/          # 通信类
│   ├── __init__.py
│   ├── email.py
│   └── sms.py
├── data/                   # 数据类
│   ├── __init__.py
│   ├── database.py
│   └── cache.py
└── external/               # 外部服务
    ├── __init__.py
    ├── weather.py
    └── search.py
```

### 工具注册

```python
# tools/__init__.py
from .computation.calculator import CalculatorTool
from .data.database import DatabaseTool

__all__ = [
    'CalculatorTool',
    'DatabaseTool',
]

def register_all_tools(agent):
    """注册所有工具到 Agent"""
    agent.tool_registry.register_tool(CalculatorTool())
    agent.tool_registry.register_tool(DatabaseTool())
```

## 配置管理

### 分层配置

```python
# config/loader.py
import toml
from pathlib import Path

def load_config(environment: str = "dev"):
    """加载配置"""
    base = Path(__file__).parent.parent
    
    # 基础配置
    config = toml.load(base / "config" / "neuroflow.toml")
    
    # 环境配置（覆盖基础配置）
    env_config = base / "config" / "environments" / f"{environment}.toml"
    if env_config.exists():
        config.update(toml.load(env_config))
    
    return config
```

## 测试组织

### 测试结构

```
tests/
├── __init__.py
├── conftest.py            # pytest 配置
├── unit/                  # 单元测试
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_tools.py
├── integration/           # 集成测试
│   ├── __init__.py
│   └── test_workflow.py
└── e2e/                   # 端到端测试
    ├── __init__.py
    └── test_full_flow.py
```

### 测试夹具

```python
# tests/conftest.py
import pytest
from neuroflow import AINativeAgent, AINativeAgentConfig

@pytest.fixture
def agent():
    """创建测试 Agent"""
    return AINativeAgent(
        AINativeAgentConfig(
            name="test_agent",
            description="Test Agent",
        )
    )

@pytest.fixture
def mock_llm():
    """模拟 LLM"""
    # 返回模拟的 LLM 客户端
    pass
```

## 日志组织

```python
# utils/logging.py
import logging

def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    
    # 设置特定模块的日志级别
    logging.getLogger('neuroflow').setLevel('DEBUG')
    logging.getLogger('httpx').setLevel('WARNING')
```

## 命名规范

### 文件命名

- 小写字母
- 下划线分隔
- 描述性名称

```
✓ good_agent.py
✓ calculator_tool.py
✗ GoodAgent.py
✗ calc.py  # 不够描述性
```

### 类命名

- 大驼峰
- 以 Agent/Tool 结尾

```python
✓ class CustomerSupportAgent
✓ class CalculatorTool
✗ class customerSupport
✗ class calc
```

### 函数命名

- 小写字母
- 下划线分隔
- 动词开头

```python
✓ async def process_request()
✓ async def calculate_sum()
✗ async def ProcessRequest()
✗ async def calc()
```

---

**相关文档**: [Agent 设计](agent-design.md) | [测试方法](../guides/testing.md)
