# 调试技巧

本指南介绍如何高效调试 NeuroFlow Agent 和工具。

## 日志记录

### 设置日志级别

```bash
# 环境变量
export NEUROFLOW_LOG_LEVEL=debug

# 或在代码中设置
from neuroflow import SDKConfig, NeuroFlowSDK

sdk = await NeuroFlowSDK.create(
    SDKConfig(log_level="debug")
)
```

### 结构化日志

```python
@agent(name="logged_agent")
class LoggedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 记录请求
        self.context.logger.info(
            "Request received",
            extra={
                "agent": self.name,
                "request_id": request.get("request_id"),
            }
        )
        
        # 记录处理步骤
        self.context.logger.debug("Processing step 1")
        self.context.logger.debug("Processing step 2")
        
        result = await self.process(request)
        
        # 记录结果
        self.context.logger.info(
            "Request processed",
            extra={"result_size": len(str(result))}
        )
        
        return result
```

## 交互式调试

### 使用调试模式

```bash
# 启动调试模式
neuroflow debug
```

在 Python REPL 中测试:

```python
>>> from neuroflow import get_sdk
>>> sdk = await get_sdk()

# 测试工具
>>> result = await sdk.execute_tool("calculate", expression="2+2")
>>> print(result)
4.0

# 测试 Agent
>>> agent = MyAgent()
>>> result = await agent.handle({"input": "test"})
>>> print(result)

# 查看日志
>>> import logging
>>> logging.getLogger("neuroflow").setLevel(logging.DEBUG)
```

### 使用断点

```python
@agent(name="debug_agent")
class DebugAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 设置断点
        breakpoint()
        
        result = await self.process(request)
        return result
```

运行:

```bash
# Python 会进入调试模式
python my_agent.py
```

在调试器中:

```python
(Pdb) print(request)  # 查看变量
(Pdb) n  # 执行下一行
(Pdb) c  # 继续执行
(Pdb) q  # 退出调试
```

## 性能分析

### 时间统计

```python
import time
from functools import wraps

def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = time.time() - start
            print(f"{func.__name__} took {elapsed:.3f}s")
    return wrapper

@agent(name="profiled_agent")
class ProfiledAgent(BaseAgent):
    @timed
    async def handle(self, request: dict) -> dict:
        return await self.process(request)
```

### 使用 cProfile

```python
import cProfile
import pstats
from pstats import SortKey

@agent(name="profiling_agent")
class ProfilingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = await self.process(request)
        
        profiler.disable()
        
        # 打印统计
        stats = pstats.Stats(profiler)
        stats.sort_stats(SortKey.TIME)
        stats.print_stats(10)  # 打印前 10 个耗时函数
        
        return result
```

## 追踪和监控

### 查看追踪 ID

```python
@agent(name="traced_agent")
class TracedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        trace_id = self.context.trace_id
        self.context.logger.info(f"Trace ID: {trace_id}")
        
        result = await self.process(request)
        
        return {
            "trace_id": trace_id,
            "result": result
        }
```

### 使用 Jaeger/Zipkin

```bash
# 启动 Jaeger
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:1.36

# 访问 UI
open http://localhost:16686
```

## 常见错误排查

### 工具未找到

```python
# 问题：ToolNotFoundError
# 解决：检查工具名称和注册

tool_manager = sdk.get_tool_manager()
tools = tool_manager.list_tools()
print(f"Available tools: {tools}")

# 确认工具已注册
if "my_tool" not in tools:
    print("Tool not registered!")
```

### 权限错误

```python
# 问题：ToolPermissionError
# 解决：检查权限设置

from neuroflow import PermissionLevel

user_perms = [PermissionLevel.READ]
has_access = tool_manager.has_permission("admin_tool", user_perms)
print(f"Has access: {has_access}")
```

### 异步初始化问题

```python
# 问题：SDK not initialized
# 解决：确保正确初始化

# ❌ 错误
sdk = NeuroFlowSDK()
result = sdk.execute_tool("test")  # RuntimeError

# ✅ 正确
sdk = await NeuroFlowSDK.create()
result = await sdk.execute_tool("test")
```

## 调试工具

### 列出工具

```bash
# CLI 命令
neuroflow tools list

# 查看工具详情
neuroflow tools info my_tool
```

### 列出 Agent

```bash
# CLI 命令
neuroflow agents list

# 查看 Agent 详情
neuroflow agents info my_agent
```

### 测试执行

```bash
# 测试工具执行
neuroflow tools execute my_tool --param value

# 测试 Agent 执行
neuroflow agents execute my_agent --payload '{"key": "value"}'
```

## 内存调试

### 查看记忆

```python
@agent(name="memory_debugger")
class MemoryDebuggerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 列出所有记忆
        all_memories = self.context.memory.search_by_type("long_term")
        
        return {
            "memory_count": len(all_memories),
            "memories": [str(m) for m in all_memories[:10]]  # 只显示前 10 个
        }
```

### 内存泄漏检测

```python
import tracemalloc

tracemalloc.start()

# 运行代码
for i in range(100):
    await agent.handle({"input": "test"})

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

## 下一步

- 🧪 **[测试方法](testing.md)** - 测试策略
- 📊 **[性能优化](../best-practices/performance.md)** - 性能调优
- ❓ **[常见问题](faq.md)** - FAQ

---

**参考资源**:
- [Python 调试文档](https://docs.python.org/3/library/debug.html)
- [logging 模块](https://docs.python.org/3/library/logging.html)
- [cProfile 文档](https://docs.python.org/3/library/profile.html)
