# 性能优化

NeuroFlow 性能优化指南。

## 性能指标

### 目标值

| 指标 | 目标 | 说明 |
|------|------|------|
| 网关延迟 (P50) | < 10ms | HTTP 请求处理时间 |
| 网关延迟 (P99) | < 20ms | 99% 请求的处理时间 |
| 工具调用延迟 | < 50ms | 工具执行时间 |
| Agent 启动时间 | < 100ms | Agent 初始化时间 |
| 并发 Agent 数 | > 100 | 同时运行的 Agent 数量 |

## 优化策略

### 1. 工具调用优化

```python
# 使用并行调用
async def process_data(data):
    # 并行执行多个工具调用
    results = await asyncio.gather(
        tool1.execute(data),
        tool2.execute(data),
        tool3.execute(data),
    )
    return results
```

### 2. 记忆系统优化

```python
from neuroflow import VectorMemoryStore

# 设置合理的最大记忆数
store = VectorMemoryStore(max_memories=1000)

# 使用标签索引
await store.store(
    key="user_preference",
    value="喜欢简洁的回答",
    tags=["user", "preference"],  # 添加标签
    memory_type=MemoryType.LONG_TERM,
)

# 使用标签搜索而非语义搜索（更快）
memories = await store.search_by_tags(["user"])
```

### 3. Agent 优化

```python
# 复用 Agent 实例
class AgentPool:
    def __init__(self, size=10):
        self.agents = [create_agent() for _ in range(size)]
    
    async def get_agent(self):
        # 从池中获取 Agent
        pass
```

### 4. LLM 调用优化

```python
# 缓存 LLM 响应
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_llm_call(prompt_hash, prompt):
    return llm.complete(prompt)
```

## 性能监控

### 使用 OpenTelemetry

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("tool_execution")
async def execute_tool(tool_name, args):
    # 执行工具
    pass
```

### 指标收集

```python
# 记录性能指标
from prometheus_client import Histogram

TOOL_EXECUTION_TIME = Histogram(
    'tool_execution_seconds',
    'Tool execution time',
    ['tool_name']
)

@TOOL_EXECUTION_TIME.labels(tool_name='calculator').time()
async def calculate(expression):
    return eval(expression)
```

## 最佳实践

1. **减少不必要的工具调用**
2. **使用并行执行**
3. **缓存常用结果**
4. **合理设置超时**
5. **监控性能指标**

---

**相关文档**: [Agent 设计](agent-design.md) | [调试技巧](../guides/debugging.md)
