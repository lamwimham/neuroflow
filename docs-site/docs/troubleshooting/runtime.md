# 运行错误

NeuroFlow 运行时的错误排查指南。

## 常见问题

### Q1: ModuleNotFoundError

**错误信息**:
```
ModuleNotFoundError: No module named 'neuroflow'
```

**原因**: neuroflow 未安装或虚拟环境未激活

**解决方案**:

```bash
# 检查是否安装
pip list | grep neuroflow

# 如果未安装
pip install neuroflow

# 检查虚拟环境
which python  # Windows: where python

# 激活虚拟环境
source venv/bin/activate  # Windows: .\venv\Scripts\Activate
```

### Q2: OPENAI_API_KEY 未设置

**错误信息**:
```
ValueError: OPENAI_API_KEY not found
```

**解决方案**:

```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key"

# 或添加到 ~/.bashrc 或 ~/.zshrc
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key"
```

### Q3: Agent 初始化失败

**错误信息**:
```
TypeError: AINativeAgent.__init__() got an unexpected keyword argument 'name'
```

**原因**: AINativeAgent 需要使用配置对象初始化

**解决方案**:

```python
# 错误用法
agent = AINativeAgent(name="assistant")

# 正确用法
from neuroflow import AINativeAgent, AINativeAgentConfig

agent = AINativeAgent(
    AINativeAgentConfig(
        name="assistant",
        description="智能助手",
    )
)
```

### Q4: 工具注册失败

**错误信息**:
```
ValueError: Tool 'xxx' already registered
```

**原因**: 工具名称重复

**解决方案**:

```python
# 使用唯一的工具名称
@agent.tool(name="unique_tool_name", description="...")
async def my_tool():
    pass

# 或检查已注册的工具
print(agent.list_available_tools())
```

### Q5: 异步函数错误

**错误信息**:
```
TypeError: object coroutine can't be used in 'await' expression
```

**原因**: 在同步函数中使用了 await

**解决方案**:

```python
# 错误用法
def handle():
    result = await some_async_function()

# 正确用法
async def handle():
    result = await some_async_function()

# 或在顶层运行
import asyncio
asyncio.run(handle())
```

### Q6: 内存不足

**错误信息**:
```
MemoryError: Unable to allocate memory
```

**解决方案**:

```python
# 限制记忆数量
from neuroflow import AINativeAgentConfig

agent = AINativeAgent(
    AINativeAgentConfig(
        name="assistant",
        max_memory_items=100,  # 限制记忆数量
    )
)

# 定期清理记忆
agent.clear_memory()
```

### Q7: 超时错误

**错误信息**:
```
asyncio.exceptions.TimeoutError
```

**解决方案**:

```python
# 增加超时时间
from neuroflow.tools import ToolCall

call = ToolCall(
    tool_id="tool_1",
    tool_name="my_tool",
    arguments={},
    timeout_ms=60000,  # 增加到 60 秒
)

# 或使用异步等待
try:
    result = await asyncio.wait_for(
        some_function(),
        timeout=30.0
    )
except asyncio.TimeoutError:
    print("操作超时")
```

### Q8: LLM API 错误

**错误信息**:
```
openai.APIError: Rate limit reached
```

**解决方案**:

```python
# 添加重试逻辑
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_llm(prompt):
    return await llm.complete(prompt)

# 或降低请求频率
import asyncio
await asyncio.sleep(1)  # 请求间等待 1 秒
```

## 调试技巧

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 使用调试器

```python
import pdb; pdb.set_trace()
```

### 3. 打印中间状态

```python
print(f"Debug: {variable}")
```

## 获取帮助

1. **查看详细错误信息**
2. **搜索错误信息**
3. **查看 GitHub Issues**
4. **提交 Issue（附带错误日志）**

---

**相关文档**: [常见问题](faq.md) | [调试技巧](../guides/debugging.md)
