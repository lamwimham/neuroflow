# 常见问题 (FAQ)

本页面收录了 NeuroFlow 使用中的常见问题和解决方案。

## 安装问题

### Q: pip install neuroflow 失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement neuroflow
```

**解决方案**:

1. **检查 Python 版本**
```bash
python --version  # 需要 3.9+
```

如果版本过低，请升级 Python:
```bash
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11
```

2. **升级 pip**
```bash
pip install --upgrade pip
```

3. **使用源码安装**
```bash
git clone https://github.com/lamWimHam/neuroflow.git
cd neuroflow/sdk
pip install -e .
```

### Q: neuroflow 命令找不到

**错误信息**:
```
bash: neuroflow: command not found
```

**解决方案**:

1. **检查虚拟环境**
```bash
# 确保虚拟环境已激活
which python  # 应该指向 venv 目录
```

2. **重新安装**
```bash
pip install -e .
```

3. **检查 PATH**
```bash
# macOS/Linux
export PATH=$PATH:~/.local/bin

# Windows (PowerShell)
$env:Path += ";$env:APPDATA\Python\Python311\Scripts"
```

### Q: 依赖冲突

**错误信息**:
```
ERROR: Cannot install neuroflow and neuroflow-sdk because these package versions have conflicting dependencies.
```

**解决方案**:

```bash
# 创建新的虚拟环境
python -m venv venv-clean
source venv-clean/bin/activate

# 安装 neuroflow
pip install neuroflow

# 如果还有问题，尝试升级基础依赖
pip install --upgrade setuptools wheel
```

## 运行问题

### Q: Agent 无法启动

**错误信息**:
```
RuntimeError: SDK not initialized
```

**解决方案**:

1. **确保正确初始化**
```python
# ✅ 正确方式
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()
# 或
sdk = NeuroFlowSDK()
await sdk.initialize()

# ❌ 错误方式
from neuroflow import sdk  # 不要这样用
```

2. **检查异步上下文**
```python
# 确保在异步函数中调用
async def main():
    sdk = await NeuroFlowSDK.create()
    # 使用 SDK

asyncio.run(main())
```

### Q: 工具执行失败

**错误信息**:
```
ToolNotFoundError: Tool 'my_tool' not found
```

**解决方案**:

1. **检查工具名称**
```python
@tool(name="my_tool")  # 确保名称正确
async def my_function():
    pass
```

2. **确认工具已注册**
```python
# 列出所有工具
tool_manager = sdk.get_tool_manager()
tools = tool_manager.list_tools()
print(f"Available tools: {tools}")
```

3. **检查 SDK 初始化顺序**
```python
# 先初始化 SDK
sdk = await NeuroFlowSDK.create()

# 再注册工具
@tool(name="my_tool")
async def my_tool():
    pass

# 或者手动注册
tool_manager.register_function(my_tool, name="my_tool")
```

### Q: Agent 执行超时

**错误信息**:
```
TimeoutError: Operation timed out after 30 seconds
```

**解决方案**:

1. **增加超时时间**
```python
result = await asyncio.wait_for(
    agent.handle(request),
    timeout=60  # 增加到 60 秒
)
```

2. **优化 Agent 性能**
```python
@agent(name="optimized_agent")
class OptimizedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 使用并发
        results = await asyncio.gather(
            self.task1(),
            self.task2(),
            self.task3()
        )
        return {"results": results}
```

3. **检查死锁**
```python
# 避免循环依赖
# Agent A → Agent B → Agent A (死锁)
```

## 内存和性能问题

### Q: 内存占用过高

**症状**: 程序运行一段时间后内存占用持续增长

**解决方案**:

1. **清理记忆**
```python
# 定期清理短期记忆
self.context.memory.clear_type(MemoryType.SHORT_TERM)
```

2. **使用 TTL**
```python
# 设置记忆过期时间
self.store_memory(
    key="temp_data",
    value=data,
    memory_type="short_term",
    ttl_seconds=3600  # 1 小时后自动过期
)
```

3. **限制缓存大小**
```python
from functools import lru_cache

@lru_cache(maxsize=100)  # 限制缓存数量
async def expensive_operation(param: str):
    pass
```

### Q: 性能缓慢

**症状**: 请求响应时间过长

**解决方案**:

1. **使用并发**
```python
# ❌ 串行执行
result1 = await tool1()
result2 = await tool2()
result3 = await tool3()

# ✅ 并行执行
results = await asyncio.gather(
    tool1(),
    tool2(),
    tool3()
)
```

2. **缓存结果**
```python
@tool(name="cached_operation")
@lru_cache(maxsize=100)
async def cached_op(param: str):
    # 耗时操作
    return result
```

3. **批量处理**
```python
# ❌ 逐个处理
for item in items:
    await process_item(item)

# ✅ 批量处理
await process_batch(items)
```

## A2A 通信问题

### Q: Agent 间通信失败

**错误信息**:
```
RuntimeError: Failed to send A2A message
```

**解决方案**:

1. **检查端点配置**
```python
# 确保端点正确
agent = MyAgent()
agent.a2a_communicator.endpoint = "http://localhost:8080/a2a"
```

2. **验证目标 Agent 可用**
```python
# 检查目标 Agent 是否注册
if target_agent in sdk._agent_registry:
    # 发送请求
    result = await agent.request_assistance(...)
```

3. **使用上下文管理器**
```python
# ✅ 正确使用
async with agent.a2a_communicator as communicator:
    result = await communicator.send_message(message)

# ❌ 错误使用
communicator = agent.a2a_communicator
result = await communicator.send_message(message)  # 未初始化
```

## MCP 集成问题

### Q: MCP 服务连接失败

**错误信息**:
```
ConnectionError: Cannot connect to MCP server
```

**解决方案**:

1. **检查 MCP 服务状态**
```bash
# 确认服务运行
curl http://localhost:8081/mcp/health
```

2. **验证端点配置**
```python
# 使用正确的端点
mcp_client = MCPClient(endpoint="http://localhost:8081/mcp")
```

3. **添加重试逻辑**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def call_mcp_with_retry():
    return await self.generate_text(prompt="...")
```

### Q: 嵌入向量生成失败

**错误信息**:
```
RuntimeError: Failed to get embeddings
```

**解决方案**:

1. **检查文本长度**
```python
# 分割长文本
texts = [long_text[i:i+512] for i in range(0, len(long_text), 512)]
embeddings = await self.get_embeddings(texts)
```

2. **验证模型可用性**
```python
# 使用可用的模型
embeddings = await self.get_embeddings(
    texts=["test"],
    model="sentence-transformers/all-MiniLM-L6-v2"
)
```

## 调试技巧

### 1. 启用详细日志

```bash
# 设置环境变量
export NEUROFLOW_LOG_LEVEL=debug

# 或在代码中设置
sdk = await NeuroFlowSDK.create(
    SDKConfig(log_level="debug")
)
```

### 2. 使用调试器

```bash
# 启动调试模式
neuroflow debug
```

```python
# 在 REPL 中测试
>>> from neuroflow import get_sdk
>>> sdk = await get_sdk()
>>> result = await sdk.execute_tool("my_tool", param="test")
>>> print(result)
```

### 3. 查看追踪

```python
# 获取追踪 ID
trace_id = sdk.get_context().trace_id

# 在 Jaeger/Zipkin 中查看
print(f"Trace ID: {trace_id}")
```

### 4. 性能分析

```python
import time
import asyncio

async def profile_operation(operation, *args):
    start = time.time()
    result = await operation(*args)
    elapsed = time.time() - start
    print(f"{operation.__name__} took {elapsed:.3f}s")
    return result

# 使用
await profile_operation(agent.handle, request)
```

## 最佳实践

### 1. 错误处理

```python
@agent(name="robust_agent")
class RobustAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            result = await self.execute_tool("operation")
            return {"success": True, "result": result}
        except Exception as e:
            self.context.logger.error(f"Error: {e}")
            return {"success": False, "error": str(e)}
```

### 2. 资源清理

```python
async def main():
    sdk = await NeuroFlowSDK.create()
    
    try:
        # 使用 SDK
        result = await sdk.execute_tool("test")
    finally:
        # 确保清理
        await sdk.shutdown()
```

### 3. 配置管理

```python
# 使用环境变量
import os

config = SDKConfig(
    log_level=os.getenv("NEUROFLOW_LOG_LEVEL", "info"),
    server_url=os.getenv("NEUROFLOW_SERVER_URL", "http://localhost:8080")
)
```

## 获取帮助

如果以上方案都无法解决问题:

1. **查看日志**
```bash
# 检查完整日志
tail -f neuroflow.log
```

2. **搜索 Issue**
```
https://github.com/lamWimHam/neuroflow/issues
```

3. **提交 Issue**
```
https://github.com/lamWimHam/neuroflow/issues/new
```

提供以下信息:
- 错误信息和堆栈追踪
- NeuroFlow 版本
- Python 版本
- 操作系统
- 最小复现代码

4. **加入社区**
- Discord: https://discord.gg/neuroflow
- GitHub Discussions: https://github.com/lamWimHam/neuroflow/discussions

---

**相关文档**:
- [安装指南](getting-started/installation.md)
- [调试技巧](debugging.md)
- [性能优化](../best-practices/performance.md)
