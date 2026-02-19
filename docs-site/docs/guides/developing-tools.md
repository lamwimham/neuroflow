# 开发工具

本指南介绍如何创建、测试和部署实用的工具。

## 工具开发基础

### 第一个工具

```python
from neuroflow import tool

@tool(name="hello", description="简单的问候工具")
async def hello(name: str) -> str:
    """
    问候某人
    
    Args:
        name: 人名
    
    Returns:
        问候语
    """
    return f"Hello, {name}!"
```

### 测试工具

```python
import pytest

@pytest.mark.asyncio
async def test_hello():
    result = await hello("Alice")
    assert result == "Hello, Alice!"

@pytest.mark.asyncio
async def test_hello_default():
    result = await hello(name="World")
    assert result == "Hello, World!"
```

## 实用工具示例

### 1. 数学计算工具

```python
from neuroflow import tool, PermissionLevel
from typing import Union

@tool(
    name="advanced_calculator",
    description="高级数学计算器",
    category="utility",
    permissions=[PermissionLevel.EXECUTE]
)
async def advanced_calculator(
    expression: str,
    precision: int = 2
) -> Union[float, str]:
    """
    高级计算器
    
    Args:
        expression: 数学表达式
        precision: 小数精度
    
    Returns:
        计算结果
    
    Raises:
        ValueError: 当表达式无效时
    """
    import re
    
    # 验证表达式
    allowed_pattern = r'^[\d+\-*/().\s]+$'
    if not re.match(allowed_pattern, expression):
        raise ValueError("Invalid characters in expression")
    
    try:
        # 安全计算
        result = eval(expression, {"__builtins__": {}}, {})
        return round(float(result), precision)
    except Exception as e:
        return f"Calculation error: {str(e)}"
```

### 2. 数据处理工具

```python
from neuroflow import tool
from typing import List, Dict, Any
import json

@tool(name="data_transformer", description="数据转换工具", category="data")
async def data_transformer(
    data: List[Dict[str, Any]],
    operation: str,
    field: str = None
) -> List[Dict[str, Any]]:
    """
    数据转换
    
    Args:
        data: 输入数据列表
        operation: 操作类型 (sort, filter, map)
        field: 操作字段
    
    Returns:
        转换后的数据
    """
    if operation == "sort":
        return sorted(data, key=lambda x: x.get(field, ""))
    
    elif operation == "filter":
        return [item for item in data if item.get(field)]
    
    elif operation == "map":
        return [{**item, f"{field}_processed": str(item.get(field, ""))} 
                for item in data]
    
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

### 3. 文本处理工具

```python
from neuroflow import tool
import re

@tool(name="text_analyzer", description="文本分析工具", category="nlp")
async def text_analyzer(text: str) -> Dict[str, Any]:
    """
    文本分析
    
    Args:
        text: 输入文本
    
    Returns:
        分析结果
    """
    # 基本统计
    char_count = len(text)
    word_count = len(text.split())
    sentence_count = len(re.split(r'[.!?]+', text))
    
    # 词频统计
    words = text.lower().split()
    word_freq = {}
    for word in words:
        word = re.sub(r'[^\w]', '', word)
        if word:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 最常见词汇
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_word_length": char_count / word_count if word_count > 0 else 0,
        "top_words": dict(top_words)
    }
```

### 4. API 调用工具

```python
from neuroflow import tool
import aiohttp
from typing import Optional, Dict, Any

@tool(name="http_client", description="HTTP 客户端工具", category="network")
async def http_client(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    HTTP 客户端
    
    Args:
        url: 请求 URL
        method: HTTP 方法
        headers: 请求头
        params: 查询参数
        data: 请求体
        timeout: 超时时间 (秒)
    
    Returns:
        响应数据
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": await response.json()
                }
        except Exception as e:
            return {
                "error": str(e),
                "status": 0
            }
```

### 5. 文件操作工具

```python
from neuroflow import tool
import os
import json
from pathlib import Path
from typing import List, Dict, Any

@tool(name="file_manager", description="文件管理工具", category="system")
async def file_manager(
    operation: str,
    path: str,
    content: str = None,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    文件管理
    
    Args:
        operation: 操作类型 (read, write, list, delete)
        path: 文件路径
        content: 写入内容
        recursive: 是否递归
    
    Returns:
        操作结果
    """
    try:
        if operation == "read":
            with open(path, 'r', encoding='utf-8') as f:
                return {"content": f.read()}
        
        elif operation == "write":
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content or "")
            return {"success": True, "path": str(path)}
        
        elif operation == "list":
            path_obj = Path(path)
            items = []
            pattern = "**/*" if recursive else "*"
            
            for item in path_obj.glob(pattern):
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {"items": items}
        
        elif operation == "delete":
            path_obj = Path(path)
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir() and recursive:
                import shutil
                shutil.rmtree(path_obj)
            return {"success": True}
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    except Exception as e:
        return {"error": str(e)}
```

### 6. 数据库工具

```python
from neuroflow import tool
import sqlite3
from typing import List, Dict, Any, Optional

@tool(name="sqlite_manager", description="SQLite 数据库管理", category="database")
async def sqlite_manager(
    db_path: str,
    query: str,
    params: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    SQLite 数据库操作
    
    Args:
        db_path: 数据库文件路径
        query: SQL 查询
        params: 查询参数
    
    Returns:
        查询结果
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 判断查询类型
        query_upper = query.strip().upper()
        
        if query_upper.startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return {"data": result, "count": len(result)}
        
        elif query_upper.startswith(("INSERT", "UPDATE", "DELETE")):
            conn.commit()
            return {
                "success": True,
                "rows_affected": cursor.rowcount
            }
        
        else:
            return {"error": "Unsupported query type"}
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'conn' in locals():
            conn.close()
```

## 工具组合模式

### 工具链

```python
from neuroflow import agent, BaseAgent

@agent(name="data_pipeline_agent")
class DataPipelineAgent(BaseAgent):
    """数据处理管道 Agent"""
    
    async def handle(self, request: dict) -> dict:
        data = request.get("data")
        
        # 工具链：清洗 → 转换 → 分析
        cleaned = await self.execute_tool("data_cleaner", data=data)
        transformed = await self.execute_tool("data_transformer", data=cleaned)
        analyzed = await self.execute_tool("data_analyzer", data=transformed)
        
        return {
            "original": data,
            "cleaned": cleaned,
            "transformed": transformed,
            "analysis": analyzed
        }
```

### 条件工具调用

```python
@agent(name="smart_processor")
class SmartProcessorAgent(BaseAgent):
    """智能处理 Agent"""
    
    async def handle(self, request: dict) -> dict:
        data_type = request.get("type")
        data = request.get("data")
        
        # 根据类型选择工具
        if data_type == "text":
            result = await self.execute_tool("text_analyzer", text=data)
        elif data_type == "image":
            result = await self.execute_tool("image_analyzer", image=data)
        elif data_type == "audio":
            result = await self.execute_tool("audio_analyzer", audio=data)
        else:
            result = await self.execute_tool("generic_analyzer", data=data)
        
        return {"type": data_type, "analysis": result}
```

### 并行工具执行

```python
import asyncio

@agent(name="parallel_processor")
class ParallelProcessorAgent(BaseAgent):
    """并行处理 Agent"""
    
    async def handle(self, request: dict) -> dict:
        tasks = request.get("tasks", [])
        
        # 并行执行多个工具
        results = await asyncio.gather(*[
            self.execute_tool(task["name"], **task["params"])
            for task in tasks
        ])
        
        return {
            "results": results,
            "count": len(results)
        }
```

## 工具测试

### 单元测试

```python
import pytest
from neuroflow import tool

@tool(name="add")
async def add(a: int, b: int) -> int:
    return a + b

@tool(name="divide")
async def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

class TestMathTools:
    @pytest.mark.asyncio
    async def test_add_positive(self):
        assert await add(2, 3) == 5
    
    @pytest.mark.asyncio
    async def test_add_negative(self):
        assert await add(-1, -1) == -2
    
    @pytest.mark.asyncio
    async def test_divide_normal(self):
        assert await divide(10, 2) == 5.0
    
    @pytest.mark.asyncio
    async def test_divide_by_zero(self):
        with pytest.raises(ValueError):
            await divide(10, 0)
```

### 集成测试

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_tools_integration():
    sdk = await NeuroFlowSDK.create()
    
    # 测试工具注册
    tool_manager = sdk.get_tool_manager()
    
    # 列出所有工具
    tools = tool_manager.list_tools()
    assert len(tools) > 0
    
    # 执行工具
    result = await sdk.execute_tool("add", a=5, b=3)
    assert result == 8
    
    # 获取工具信息
    info = tool_manager.get_tool_info("add")
    assert info is not None
    assert info.name == "add"
    
    await sdk.shutdown()
```

### 性能测试

```python
import pytest
import time
from neuroflow import tool

@tool(name="slow_operation")
async def slow_operation(duration: float) -> str:
    import asyncio
    await asyncio.sleep(duration)
    return "Done"

@pytest.mark.asyncio
async def test_performance():
    start = time.time()
    result = await slow_operation(0.1)
    elapsed = time.time() - start
    
    assert result == "Done"
    assert elapsed < 0.2  # 应该在 0.2 秒内完成

@pytest.mark.asyncio
async def test_concurrent_execution():
    import asyncio
    
    start = time.time()
    
    # 并发执行 10 个任务
    tasks = [slow_operation(0.1) for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    
    assert len(results) == 10
    assert elapsed < 0.2  # 并发执行应该很快完成
```

## 工具部署

### 打包工具

```python
# tools/__init__.py
from .math_tools import advanced_calculator
from .text_tools import text_analyzer
from .http_tools import http_client

__all__ = [
    "advanced_calculator",
    "text_analyzer",
    "http_client"
]

__version__ = "1.0.0"
```

### 加载外部工具

```python
from neuroflow import NeuroFlowSDK, ToolManager
import importlib

async def load_tools_from_module(module_name: str, tool_manager: ToolManager):
    """从模块加载工具"""
    module = importlib.import_module(module_name)
    
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        
        # 检查是否有工具元数据
        if hasattr(attr, 'tool_metadata'):
            meta = attr.tool_metadata
            tool_manager.register_function(
                func=attr,
                name=meta.name,
                description=meta.description,
                category=meta.category
            )

# 使用示例
sdk = await NeuroFlowSDK.create()
await load_tools_from_module("my_custom_tools", sdk.get_tool_manager())
```

## 最佳实践

### 1. 单一职责

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

### 2. 清晰的文档

```python
@tool(
    name="process_payment",
    description="处理支付请求",
    parameters={
        "amount": {"type": "number", "description": "支付金额", "required": True},
        "currency": {"type": "string", "description": "货币类型", "default": "USD"},
        "user_id": {"type": "string", "description": "用户 ID", "required": True}
    }
)
async def process_payment(amount: float, currency: str = "USD", user_id: str = "") -> dict:
    """
    处理支付请求
    
    Args:
        amount: 支付金额
        currency: 货币类型 (USD, EUR, CNY)
        user_id: 用户 ID
    
    Returns:
        支付结果：{"success": bool, "transaction_id": str}
    
    Raises:
        ValueError: 当金额无效时
        PaymentError: 当支付失败时
    """
    pass
```

### 3. 错误处理

```python
@tool(name="safe_operation")
async def safe_operation(param: str) -> str:
    """安全操作"""
    try:
        # 验证输入
        if not param:
            raise ValueError("Parameter cannot be empty")
        
        # 执行操作
        result = await perform_operation(param)
        
        # 验证结果
        if result is None:
            raise RuntimeError("Operation returned None")
        
        return result
    
    except ValueError as e:
        # 用户错误
        raise e
    
    except Exception as e:
        # 系统错误
        raise RuntimeError(f"System error: {str(e)}")
```

### 4. 类型安全

```python
from typing import List, Dict, Optional, Union

@tool(name="type_safe_tool")
async def type_safe_tool(
    items: List[str],
    options: Optional[Dict[str, any]] = None,
    limit: int = 10
) -> Dict[str, Union[List[str], int]]:
    """类型安全的工具"""
    options = options or {}
    
    processed_items = items[:limit]
    
    return {
        "items": processed_items,
        "count": len(processed_items)
    }
```

## 下一步

- 🤖 **[使用工具构建 Agent](building-agents.md)** - 组合工具创建 Agent
- 🔒 **[权限管理](../best-practices/security.md)** - 权限控制
- 📖 **[API 参考](../api-reference/python/index.md)** - 完整 API
- 🧪 **[测试方法](testing.md)** - 测试策略

---

**参考资源**:
- [工具示例](../examples/basic.md#tools)
- [SDK 源码](https://github.com/lamwimham/neuroflow/tree/main/sdk)
- [故障排除](../troubleshooting/faq.md)
