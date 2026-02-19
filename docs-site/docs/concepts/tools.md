# 工具系统

工具 (Tool) 是 NeuroFlow 中可复用的功能单元，是 Agent 执行具体任务的基本能力。

## 什么是工具？

工具是一个独立的函数或方法，具有以下特征:

- 🔄 **可复用**: 可以被多个 Agent 调用
- 📦 **自包含**: 完成特定的功能
- 🔍 **可发现**: 通过元数据描述功能和参数
- 🔒 **权限控制**: 支持不同级别的访问控制
- ⚡ **异步支持**: 支持同步和异步执行

## 工具 vs Agent

| 特性 | 工具 | Agent |
|------|------|-------|
| **职责** | 单一功能 | 复杂业务逻辑 |
| **状态** | 无状态 | 有状态 (记忆) |
| **通信** | 被动调用 | 主动通信 (A2A) |
| **复杂度** | 低 | 高 |
| **组合** | 被组合 | 组合工具 |

## 创建工具

### 基础示例

```python
from neuroflow import tool

@tool(name="greet", description="问候某人")
async def greet(name: str) -> str:
    """问候工具"""
    return f"Hello, {name}!"
```

### 带参数的工具

```python
from neuroflow import tool

@tool(
    name="calculate_bmi",
    description="计算 BMI 指数",
    category="health"
)
async def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    计算身体质量指数 (BMI)
    
    Args:
        weight_kg: 体重 (千克)
        height_m: 身高 (米)
    
    Returns:
        BMI 值
    """
    return weight_kg / (height_m ** 2)
```

### 带权限的工具

```python
from neuroflow import tool, PermissionLevel

@tool(
    name="delete_user",
    description="删除用户账户",
    category="admin",
    permissions=[PermissionLevel.ADMIN]
)
async def delete_user(user_id: str) -> bool:
    """删除用户 (仅管理员)"""
    # 实现删除逻辑
    return True
```

### 同步工具

```python
from neuroflow import tool

@tool(name="get_current_time", description="获取当前时间")
def get_current_time() -> str:
    """获取当前系统时间"""
    from datetime import datetime
    return datetime.now().isoformat()
```

## 工具装饰器参数

### name (必需)

工具的唯一标识符:

```python
@tool(name="my_unique_tool_name")
async def my_tool():
    pass
```

### description (推荐)

工具的功能描述:

```python
@tool(
    name="translate_text",
    description="将文本从一种语言翻译成另一种语言"
)
async def translate(text: str, target_lang: str) -> str:
    pass
```

### category (可选)

工具分类，用于组织和搜索:

```python
@tool(name="send_email", category="communication")
@tool(name="send_sms", category="communication")
@tool(name="calculate_tax", category="finance")
```

**常用分类**:
- `utility`: 通用工具
- `communication`: 通信工具
- `finance`: 金融工具
- `data`: 数据处理
- `ai`: AI 相关
- `admin`: 管理工具

### permissions (可选)

权限控制:

```python
from neuroflow import PermissionLevel

# 只读权限
@tool(permissions=[PermissionLevel.READ])
async def read_data():
    pass

# 写入权限
@tool(permissions=[PermissionLevel.WRITE])
async def write_data():
    pass

# 执行权限
@tool(permissions=[PermissionLevel.EXECUTE])
async def execute_task():
    pass

# 管理员权限
@tool(permissions=[PermissionLevel.ADMIN])
async def admin_operation():
    pass
```

### parameters (可选)

参数 schema 定义:

```python
@tool(
    name="search",
    description="搜索文档",
    parameters={
        "query": {
            "type": "string",
            "description": "搜索关键词",
            "required": True
        },
        "limit": {
            "type": "integer",
            "description": "返回结果数量",
            "default": 10
        }
    }
)
async def search(query: str, limit: int = 10) -> list:
    pass
```

### version (可选)

工具版本号:

```python
@tool(name="api_call", version="2.0.0")
async def api_call():
    pass
```

### author (可选)

工具作者:

```python
@tool(name="custom_tool", author="your_name @company.com")
async def custom_tool():
    pass
```

## 在 Agent 中使用工具

### 方式 1: 调用全局工具

```python
from neuroflow import agent, BaseAgent, tool

# 定义全局工具
@tool(name="calculator", description="计算器")
async def calculator(expression: str) -> float:
    return eval(expression)

# 在 Agent 中使用
@agent(name="math_agent")
class MathAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        result = await self.execute_tool("calculator", expression="2+2")
        return {"result": result}
```

### 方式 2: 定义 Agent 专属工具

```python
from neuroflow import agent, BaseAgent, tool

@agent(name="weather_agent")
class WeatherAgent(BaseAgent):
    @tool(name="get_weather", description="获取天气")
    async def get_weather(self, city: str) -> str:
        # 实现天气查询
        return f"Sunny in {city}"
    
    async def handle(self, request: dict) -> dict:
        city = request.get("city")
        weather = await self.execute_tool("get_weather", city=city)
        return {"weather": weather}
```

### 方式 3: 组合多个工具

```python
from neuroflow import agent, BaseAgent

@agent(name="data_processor")
class DataProcessorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data = request.get("data")
        
        # 组合多个工具
        cleaned = await self.execute_tool("clean_data", data=data)
        analyzed = await self.execute_tool("analyze_data", data=cleaned)
        report = await self.execute_tool("generate_report", analysis=analyzed)
        
        return {"report": report}
```

## 工具管理

### 列出所有工具

```python
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()
tool_manager = sdk.get_tool_manager()

# 列出所有工具
all_tools = tool_manager.list_tools()
print(f"Available tools: {all_tools}")

# 按类别列出
tools_by_category = tool_manager.list_tools(category="utility")
print(f"Utility tools: {tools_by_category}")
```

### 获取工具信息

```python
# 获取工具详细信息
tool_info = tool_manager.get_tool_info("calculate")
print(f"Tool info: {tool_info}")
print(f"Description: {tool_info.description}")
print(f"Category: {tool_info.category}")
print(f"Permissions: {tool_info.permissions}")
```

### 搜索工具

```python
# 关键词搜索
results = tool_manager.search_tools("calculate")
print(f"Search results: {results}")

# 正则匹配
results = tool_manager.get_tools_by_pattern(r"^calc.*")
print(f"Pattern match: {results}")
```

### 启用/禁用工具

```python
# 禁用工具
tool_manager.disable_tool("old_tool")

# 启用工具
tool_manager.enable_tool("old_tool")

# 更新工具信息
tool_manager.update_tool(
    "existing_tool",
    description="Updated description"
)
```

### 权限检查

```python
from neuroflow import PermissionLevel

# 检查用户权限
user_perms = [PermissionLevel.READ, PermissionLevel.EXECUTE]

has_access = tool_manager.has_permission("admin_tool", user_perms)
print(f"Has access: {has_access}")  # False

has_access = tool_manager.has_permission("read_tool", user_perms)
print(f"Has access: {has_access}")  # True
```

## 内置工具

NeuroFlow SDK 提供以下内置工具:

### calculate

数学计算器:

```python
result = await sdk.execute_tool("calculate", expression="2+2")
print(result)  # 4.0
```

### echo

回显输入:

```python
result = await sdk.execute_tool("echo", message="Hello")
print(result)  # "Hello"
```

### builtin_math_calculator

增强版计算器:

```python
result = await sdk.execute_tool(
    "builtin_math_calculator",
    expression="(10 + 5) * 2"
)
print(result)  # 30.0
```

### builtin_string_utils

字符串处理:

```python
# 转大写
result = await sdk.execute_tool(
    "builtin_string_utils",
    text="hello",
    operation="upper"
)
print(result)  # "HELLO"

# 反转
result = await sdk.execute_tool(
    "builtin_string_utils",
    text="hello",
    operation="reverse"
)
print(result)  # "olleh"

# 词数统计
result = await sdk.execute_tool(
    "builtin_string_utils",
    text="Hello World",
    operation="words"
)
print(result)  # "2"
```

## 高级用法

### 工具链 (Tool Chaining)

```python
from neuroflow import agent, BaseAgent

@agent(name="pipeline_agent")
class PipelineAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 工具链：数据 → 清洗 → 分析 → 报告
        data = request.get("data")
        
        step1 = await self.execute_tool("clean", data=data)
        step2 = await self.execute_tool("analyze", data=step1)
        step3 = await self.execute_tool("report", analysis=step2)
        
        return {"final_result": step3}
```

### 并行执行工具

```python
import asyncio

@agent(name="parallel_agent")
class ParallelAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 并行执行多个工具
        results = await asyncio.gather(
            self.execute_tool("task1", param=request.get("param1")),
            self.execute_tool("task2", param=request.get("param2")),
            self.execute_tool("task3", param=request.get("param3"))
        )
        
        return {
            "result1": results[0],
            "result2": results[1],
            "result3": results[2]
        }
```

### 工具缓存

```python
from functools import lru_cache

@tool(name="expensive_operation")
@lru_cache(maxsize=100)
async def expensive_op(param: str) -> str:
    # 耗时操作，结果会被缓存
    import time
    time.sleep(5)  # 模拟耗时
    return f"Result for {param}"

# 第二次调用会立即返回
result1 = await expensive_op("test")  # 5 秒
result2 = await expensive_op("test")  # 立即返回
```

### 工具重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@tool(name="unreliable_api")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def unreliable_api():
    # 可能失败的 API 调用
    import random
    if random.random() < 0.5:
        raise Exception("API error")
    return "Success"
```

### 工具超时

```python
import asyncio

@tool(name="timeout_operation")
async def timeout_op(duration: int) -> str:
    try:
        result = await asyncio.wait_for(
            some_async_operation(),
            timeout=5.0  # 5 秒超时
        )
        return result
    except asyncio.TimeoutError:
        return "Operation timed out"
```

## 工具开发最佳实践

### 1. 保持单一职责

```python
# ❌ 避免：多功能工具
@tool(name="do_everything")
async def do_everything(action: str, data: any):
    if action == "clean":
        # 清洗逻辑
        pass
    elif action == "analyze":
        # 分析逻辑
        pass

# ✅ 推荐：单一功能工具
@tool(name="clean_data")
async def clean_data(data: any):
    pass

@tool(name="analyze_data")
async def analyze_data(data: any):
    pass
```

### 2. 提供清晰的文档

```python
@tool(
    name="process_payment",
    description="处理支付请求",
    parameters={
        "amount": {"type": "number", "description": "支付金额"},
        "currency": {"type": "string", "description": "货币类型"},
        "user_id": {"type": "string", "description": "用户 ID"}
    }
)
async def process_payment(amount: float, currency: str, user_id: str) -> dict:
    """
    处理支付请求
    
    Args:
        amount: 支付金额
        currency: 货币类型 (USD, EUR, CNY)
        user_id: 用户 ID
    
    Returns:
        支付结果字典
    
    Raises:
        ValueError: 当金额无效时
        PaymentError: 当支付失败时
    """
    pass
```

### 3. 错误处理

```python
@tool(name="safe_divide")
async def safe_divide(a: float, b: float) -> float:
    """安全除法"""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
```

### 4. 类型注解

```python
from typing import List, Dict, Optional

@tool(name="process_items")
async def process_items(
    items: List[str],
    options: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """处理物品列表"""
    pass
```

### 5. 日志记录

```python
import logging

@tool(name="logged_operation")
async def logged_operation(data: str) -> str:
    """带日志的操作"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing: {data}")
    
    try:
        result = await process(data)
        logger.info(f"Success: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise
```

## 调试工具

### 1. 打印调试

```python
@tool(name="debug_tool")
async def debug_tool(param: str) -> str:
    print(f"Input: {param}")
    result = f"Processed: {param}"
    print(f"Output: {result}")
    return result
```

### 2. 使用 SDK 调试

```bash
# 启动调试模式
neuroflow debug
```

```python
# 在 REPL 中测试工具
>>> from neuroflow import get_sdk
>>> sdk = await get_sdk()
>>> result = await sdk.execute_tool("my_tool", param="test")
>>> print(result)
```

### 3. 查看工具信息

```bash
# 列出所有工具
neuroflow tools list

# 查看工具详情
neuroflow tools info my_tool
```

## 测试工具

```python
import pytest
from neuroflow import tool

@tool(name="add")
async def add(a: int, b: int) -> int:
    return a + b

@pytest.mark.asyncio
async def test_add():
    result = await add(2, 3)
    assert result == 5

@pytest.mark.asyncio
async def test_add_negative():
    result = await add(-1, -1)
    assert result == -2
```

## 下一步

- 🤖 **[构建 Agent](../guides/building-agents.md)** - 使用工具创建 Agent
- 🔧 **[开发工具](../guides/developing-tools.md)** - 工具开发实战
- 🔒 **[权限管理](../best-practices/security.md)** - 权限控制最佳实践
- 📖 **[API 参考](../api-reference/python/index.md)** - 完整 API 文档

---

**参考资源**:
- [NeuroFlow SDK 源码](https://github.com/lamwimham/neuroflow/tree/main/sdk)
- [示例工具](../examples/basic.md#tools)
- [故障排除](../troubleshooting/faq.md)
