# Python SDK API 参考

NeuroFlow Python SDK 提供了简洁而强大的 API，用于构建 AI Agent。

## 核心类

### NeuroFlowSDK

主要的 SDK 类，提供统一的入口。

**导入**:
```python
from neuroflow import NeuroFlowSDK, SDKConfig
```

**构造方法**:
```python
def __init__(self, config: Optional[SDKConfig] = None)
```

**参数**:
- `config`: SDK 配置对象，使用默认值如果为 None

**方法**:

#### create(config) → NeuroFlowSDK

工厂方法，创建并初始化 SDK 实例。

```python
sdk = await NeuroFlowSDK.create()
```

**参数**:
- `config`: SDK 配置对象

**返回**:
- 已初始化的 SDK 实例

#### initialize() → None

显式初始化 SDK。

```python
sdk = NeuroFlowSDK()
await sdk.initialize()
```

**异常**:
- `RuntimeError`: 如果已经初始化过

#### execute_tool(tool_name, **kwargs) → Any

执行工具。

```python
result = await sdk.execute_tool("calculate", expression="2+2")
```

**参数**:
- `tool_name`: 工具名称
- `**kwargs`: 工具参数

**返回**:
- 工具执行结果

#### register_agent(name, agent_class) → None

注册 Agent 类。

```python
sdk.register_agent("my_agent", MyAgentClass)
```

**参数**:
- `name`: Agent 名称
- `agent_class`: Agent 类

#### get_agent(name) → Type[BaseAgent]

获取 Agent 类。

```python
agent_class = sdk.get_agent("my_agent")
```

**参数**:
- `name`: Agent 名称

**返回**:
- Agent 类

**异常**:
- `KeyError`: 如果 Agent 未找到

#### get_tool_manager() → ToolManager

获取工具管理器。

```python
tool_manager = sdk.get_tool_manager()
```

**返回**:
- 工具管理器实例

**异常**:
- `RuntimeError`: 如果 SDK 未初始化

#### get_context() → Context

获取上下文。

```python
context = sdk.get_context()
```

**返回**:
- 上下文实例

**异常**:
- `RuntimeError`: 如果 SDK 未初始化

#### shutdown() → None

关闭 SDK。

```python
await sdk.shutdown()
```

#### is_initialized → bool

检查 SDK 是否已初始化。

```python
if sdk.is_initialized:
    # 使用 SDK
```

---

### SDKConfig

SDK 配置类。

**导入**:
```python
from neuroflow import SDKConfig
```

**属性**:
```python
@dataclass
class SDKConfig:
    log_level: str = "info"              # 日志级别
    enable_tracing: bool = True          # 启用链路追踪
    enable_metrics: bool = True          # 启用指标收集
    server_url: str = "http://localhost:8080"  # 服务器地址
```

**用法**:
```python
config = SDKConfig(
    log_level="debug",
    enable_tracing=True,
    server_url="http://localhost:8080"
)

sdk = await NeuroFlowSDK.create(config)
```

---

### BaseAgent

Agent 基类。

**导入**:
```python
from neuroflow import BaseAgent
```

**构造方法**:
```python
def __init__(self, name: str, description: str = "")
```

**属性**:
- `name`: Agent 名称
- `description`: Agent 描述
- `tools`: 工具字典
- `context`: 上下文实例
- `a2a_communicator`: A2A 通信器
- `mcp_client`: MCP 客户端

**方法**:

#### handle(request: dict) → dict

处理请求的入口方法 (抽象方法，子类必须实现)。

```python
async def handle(self, request: dict) -> dict:
    # 实现处理逻辑
    return {"result": "success"}
```

**参数**:
- `request`: 请求字典

**返回**:
- 响应字典

#### execute_tool(tool_name: str, **kwargs) → Any

执行工具。

```python
result = await self.execute_tool("calculate", expression="2+2")
```

**参数**:
- `tool_name`: 工具名称
- `**kwargs`: 工具参数

**返回**:
- 工具执行结果

#### register_tool(func, name, description, parameters) → None

手动注册工具。

```python
def my_tool(param: str):
    pass

self.register_tool(my_tool, name="my_tool", description="My tool")
```

#### get_tool_metadata(tool_name: str) → Optional[ToolMetadata]

获取工具元数据。

```python
meta = self.get_tool_metadata("my_tool")
```

#### list_tools() → List[str]

列出所有可用的工具。

```python
tools = self.list_tools()
```

#### store_memory(key, value, memory_type, tags, importance, ttl_seconds) → None

存储记忆。

```python
self.store_memory(
    key="user_pref",
    value={"theme": "dark"},
    memory_type="long_term",
    tags=["user", "preference"],
    importance=0.8
)
```

**参数**:
- `key`: 记忆键
- `value`: 记忆值
- `memory_type`: 记忆类型 (short_term, long_term, working)
- `tags`: 标签列表
- `importance`: 重要程度 (0.0-1.0)
- `ttl_seconds`: 过期时间 (仅用于短期记忆)

#### retrieve_memory(key: str) → Optional[Any]

检索记忆。

```python
value = self.retrieve_memory("user_pref")
```

#### search_memories_by_tags(tags: List[str]) → List[Any]

根据标签搜索记忆。

```python
memories = self.search_memories_by_tags(["user"])
```

#### search_memories_by_type(memory_type: str) → List[Any]

根据类型搜索记忆。

```python
memories = self.search_memories_by_type("long_term")
```

#### request_assistance(target_agent: str, task: str, params: dict) → dict

请求其他 Agent 协助。

```python
result = await self.request_assistance(
    target_agent="data_agent",
    task="analyze_data",
    params={"data": [...]}
)
```

#### get_embeddings(texts: List[str], model: str) → List[List[float]]

获取文本嵌入向量。

```python
embeddings = await self.get_embeddings(
    texts=["text1", "text2"],
    model="sentence-transformers/all-MiniLM-L6-v2"
)
```

#### generate_text(prompt: str, model: str, params: dict) → str

生成文本。

```python
response = await self.generate_text(
    prompt="Write a poem",
    model="gpt-3.5-turbo",
    params={"temperature": 0.7}
)
```

#### learn_new_skill(skill_description: str, examples: list) → str

学习新技能。

```python
skill_id = await self.learn_new_skill(
    skill_description="Translate Chinese to English",
    examples=[
        {"input": "你好", "expected_output": "Hello"}
    ]
)
```

#### adapt_to_context(context_description: str) → List[str]

根据上下文自适应，推荐技能。

```python
recommended = await self.adapt_to_context("math calculation")
```

#### improve_existing_skill(skill_name: str, feedback: dict) → bool

改进现有技能。

```python
success = await self.improve_existing_skill(
    skill_name="translation",
    feedback={"quality": "good"}
)
```

---

### ToolManager

工具管理器。

**导入**:
```python
from neuroflow import ToolManager
```

**方法**:

#### register_tool(name, description, category, permissions, parameters, version, author) → decorator

注册工具的装饰器。

```python
@tool_manager.register_tool(
    name="my_tool",
    description="My tool",
    category="utility"
)
async def my_tool(param: str):
    pass
```

#### register_function(func, name, description, category, permissions, parameters, version, author) → None

直接注册函数作为工具。

```python
tool_manager.register_function(
    func=my_tool,
    name="my_tool",
    description="My tool"
)
```

#### get_tool(name, user_permissions) → Callable

获取工具函数 (带权限检查)。

```python
tool_func = tool_manager.get_tool("my_tool")
```

#### execute_tool_async(name, *args, user_permissions, **kwargs) → Any

异步执行工具。

```python
result = await tool_manager.execute_tool_async("my_tool", param="value")
```

#### get_tool_info(name: str) → Optional[ToolInfo]

获取工具信息。

```python
info = tool_manager.get_tool_info("my_tool")
```

#### list_tools(category: str = None, enabled_only: bool = True) → List[str]

列出工具。

```python
all_tools = tool_manager.list_tools()
utility_tools = tool_manager.list_tools(category="utility")
```

#### search_tools(query: str) → List[str]

搜索工具。

```python
results = tool_manager.search_tools("calculate")
```

#### disable_tool(name: str) → bool

禁用工具。

```python
tool_manager.disable_tool("old_tool")
```

#### enable_tool(name: str) → bool

启用工具。

```python
tool_manager.enable_tool("old_tool")
```

#### has_permission(tool_name: str, user_permissions: List[PermissionLevel]) → bool

检查权限。

```python
has_access = tool_manager.has_permission(
    "admin_tool",
    [PermissionLevel.ADMIN]
)
```

---

### ToolInfo

工具信息类。

**导入**:
```python
from neuroflow import ToolInfo
```

**属性**:
```python
@dataclass
class ToolInfo:
    name: str                      # 工具名称
    description: str               # 描述
    category: str                  # 分类
    permissions: List[PermissionLevel]  # 权限
    parameters: Dict[str, Any]     # 参数
    version: str                   # 版本
    author: str                    # 作者
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间
    enabled: bool = True           # 是否启用
```

---

### PermissionLevel

权限等级枚举。

**导入**:
```python
from neuroflow import PermissionLevel
```

**成员**:
- `READ`: 读权限
- `WRITE`: 写权限
- `EXECUTE`: 执行权限
- `ADMIN`: 管理员权限

**用法**:
```python
@tool(permissions=[PermissionLevel.ADMIN])
async def admin_operation():
    pass
```

---

### Context

上下文类。

**导入**:
```python
from neuroflow import Context, get_context
```

**获取上下文**:
```python
context = get_context()
```

**属性**:
- `memory`: 记忆管理器
- `logger`: 日志记录器
- `trace_id`: 追踪 ID

**用法**:
```python
context = get_context()

# 记录日志
context.logger.info("Processing request")

# 获取追踪 ID
trace_id = context.trace_id

# 访问记忆
context.memory.store("key", "value")
```

---

## 装饰器

### @agent

注册 Agent 类。

**导入**:
```python
from neuroflow import agent
```

**参数**:
- `name`: Agent 名称 (可选，默认使用类名)
- `description`: Agent 描述

**用法**:
```python
@agent(name="my_agent", description="My Agent")
class MyAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return {"result": "success"}
```

---

### @tool

注册工具函数。

**导入**:
```python
from neuroflow import tool
```

**参数**:
- `name`: 工具名称 (可选，默认使用函数名)
- `description`: 工具描述
- `category`: 工具分类

**用法**:
```python
@tool(name="greet", description="Greet someone", category="utility")
async def greet(name: str) -> str:
    return f"Hello, {name}!"
```

---

## 便捷函数

### get_sdk(config) → NeuroFlowSDK

获取全局 SDK 实例。

**导入**:
```python
from neuroflow import get_sdk
```

**参数**:
- `config`: SDK 配置 (仅在首次创建时使用)

**用法**:
```python
sdk = await get_sdk()
```

---

## 异常类

### ToolNotFoundError

工具未找到错误。

```python
from neuroflow import ToolNotFoundError

try:
    result = await sdk.execute_tool("nonexistent_tool")
except ToolNotFoundError as e:
    print(f"Tool not found: {e}")
```

### ToolPermissionError

工具权限错误。

```python
from neuroflow import ToolPermissionError

try:
    result = await sdk.execute_tool("admin_tool")
except ToolPermissionError as e:
    print(f"Permission denied: {e}")
```

---

## 完整示例

```python
import asyncio
from neuroflow import NeuroFlowSDK, agent, BaseAgent, tool

# 定义工具
@tool(name="calculate", description="Calculate expression")
async def calculate(expression: str) -> float:
    return eval(expression)

# 定义 Agent
@agent(name="math_agent", description="Math Agent")
class MathAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        expression = request.get("expression")
        result = await self.execute_tool("calculate", expression=expression)
        return {"result": result}

async def main():
    # 创建 SDK
    sdk = await NeuroFlowSDK.create()
    
    # 注册 Agent
    sdk.register_agent("math_agent", MathAgent)
    
    # 执行工具
    result = await sdk.execute_tool("calculate", expression="2+2")
    print(f"Result: {result}")
    
    # 关闭 SDK
    await sdk.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

---

**相关文档**:
- [Rust Kernel API](rust/index.md)
- [概念指南](../concepts/architecture.md)
- [开发指南](../guides/building-agents.md)
