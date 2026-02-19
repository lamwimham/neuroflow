# 性能问题

NeuroFlow 性能问题的故障排除指南。

## 常见问题

### Q1: 响应速度慢

**症状**: Agent 响应时间超过 5 秒

**可能原因**:
1. LLM API 调用慢
2. 工具执行慢
3. 网络延迟

**解决方案**:

```python
# 1. 使用缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_llm_call(prompt_hash):
    return llm.complete(prompt)

# 2. 并行执行工具
async def process_multiple_tools():
    results = await asyncio.gather(
        tool1.execute(),
        tool2.execute(),
        tool3.execute(),
    )

# 3. 设置超时
from neuroflow.tools import ToolCall
call = ToolCall(
    tool_id="tool_1",
    tool_name="my_tool",
    arguments={},
    timeout_ms=5000,  # 5 秒超时
)
```

### Q2: 内存占用高

**症状**: 内存使用持续增长

**解决方案**:

```python
# 1. 限制记忆数量
agent = AINativeAgent(
    AINativeAgentConfig(
        name="assistant",
        max_memory_items=100,
    )
)

# 2. 定期清理
agent.clear_memory()

# 3. 使用弱引用
import weakref
cache = weakref.WeakValueDictionary()
```

### Q3: CPU 使用率高

**症状**: CPU 持续 100%

**解决方案**:

```python
# 1. 使用异步 IO
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 2. 限制并发数
semaphore = asyncio.Semaphore(10)

async def limited_task():
    async with semaphore:
        await process()

# 3. 添加延迟
await asyncio.sleep(0.1)
```

### Q4: 工具调用失败率高

**症状**: 工具调用经常超时或失败

**解决方案**:

```python
# 1. 添加重试逻辑
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def call_tool():
    return await tool.execute()

# 2. 使用熔断器
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def protected_call():
    return await tool.execute()

# 3. 设置合理的超时
call = ToolCall(
    tool_id="tool_1",
    timeout_ms=30000,  # 30 秒
)
```

## 性能监控

### 使用 OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("agent_handle")
async def handle_request(request):
    with tracer.start_as_current_span("tool_execution"):
        result = await tool.execute()
    return result
```

### 性能指标

```python
from prometheus_client import Counter, Histogram

# 定义指标
REQUEST_COUNT = Counter('agent_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('agent_request_duration_seconds', 'Request duration')

@REQUEST_DURATION.time()
async def handle_request(request):
    REQUEST_COUNT.inc()
    return await agent.handle(request)
```

## 优化建议

### 1. 减少不必要的 LLM 调用

```python
# 使用规则过滤简单请求
def is_simple_request(request):
    return request.get("type") == "greeting"

if is_simple_request(request):
    return {"response": "Hello!"}
else:
    return await llm.handle(request)
```

### 2. 批量处理

```python
# 批量处理工具调用
async def batch_process(items):
    batch_size = 10
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        results = await asyncio.gather(*[process(item) for item in batch])
```

### 3. 使用连接池

```python
import aiohttp

# 创建会话池
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100),
    timeout=aiohttp.ClientTimeout(total=30),
)

# 复用会话
async with session.get(url) as response:
    data = await response.json()
```

## 基准测试

```python
import time
import asyncio

async def benchmark(func, iterations=100):
    start = time.time()
    for _ in range(iterations):
        await func()
    elapsed = time.time() - start
    print(f"Average: {elapsed/iterations*1000:.2f}ms")

# 运行基准测试
await benchmark(agent.handle)
```

---

**相关文档**: [性能优化](../best-practices/performance.md) | [调试技巧](../guides/debugging.md)
