# NeuroFlow Rust 运行时能力总结

**版本**: v0.5.0  
**日期**: 2026-03-20

本文档总结 NeuroFlow Rust 内核实现的所有功能，以及如何通过 Python SDK 使用这些能力。

---

## 📊 功能总览

```
NeuroFlow Rust Kernel
├── 🛡️ 沙箱隔离系统 (Sandbox)
│   ├── Python 进程沙箱
│   ├── Linux Namespace 隔离
│   └── WASM 沙箱
├── 🧠 记忆系统 (Memory)
│   ├── 短期记忆
│   ├── 长期记忆
│   └── 语义搜索
├── 🤝 A2A 协作 (Agent-to-Agent)
│   ├── Agent 注册
│   ├── 协作编排
│   └── HTTP/gRPC 通信
├── 🔌 MCP 集成 (Model Context Protocol)
│   ├── MCP 服务器管理
│   ├── 工具发现
│   └── 工具执行
├── 📊 可观测性 (Observability)
│   ├── 链路追踪
│   ├── 指标收集
│   └── 结构化日志
└── 🔒 安全系统 (Security)
    ├── 权限控制
    └── 审计日志
```

---

## 🛡️ 1. 沙箱隔离系统

### 实现位置
- `kernel/src/sandbox/mod.rs` - 统一接口
- `kernel/src/sandbox/namespace.rs` - Linux Namespace
- `kernel/src/sandbox/wasm.rs` - WASM 沙箱
- `kernel/src/sandbox/python/` - Python 进程沙箱

### 功能特性

| 沙箱类型 | 隔离级别 | 平台 | 启动时间 | 内存占用 |
|---------|---------|------|---------|---------|
| **Python 进程** | ⭐⭐⭐ | 全平台 | ~80ms | ~15MB |
| **Linux Namespace** | ⭐⭐⭐⭐ | Linux | ~100ms | ~20MB |
| **WASM** | ⭐⭐⭐⭐⭐ | 全平台 | ~10ms | ~5MB |

### Python SDK 使用

```python
from neuroflow.sandbox import (
    SandboxIsolator,      # Python 进程沙箱
    NamespaceIsolator,    # Linux Namespace
    WasmSandbox,          # WASM 沙箱
    SandboxConfig,
    WasmSandboxConfig,
)

# ========== 方式 1: Python 进程沙箱 ==========
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
)

isolator = SandboxIsolator(config)
result = await isolator.execute("python3", ["script.py"])
print(f"退出码：{result.exit_code}")

# ========== 方式 2: Linux Namespace 沙箱 ==========
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    enable_network=False,  # 禁用网络
    enable_seccomp=True,   # 系统调用过滤
)

isolator = NamespaceIsolator(config)
result = isolator.execute("python3", ["script.py"])

# ========== 方式 3: WASM 沙箱 ==========
config = WasmSandboxConfig(
    max_memory_bytes=64 * 1024 * 1024,
    timeout_seconds=30,
    max_fuel=1_000_000,
)

async with WasmSandbox(config) as sandbox:
    with open("module.wasm", "rb") as f:
        result = await sandbox.execute(f.read())
    print(f"执行时间：{result.execution_time_ms}ms")
```

### 适用场景

- **Python 进程沙箱**: 内部可信代码，快速原型
- **Linux Namespace**: 半可信第三方代码，生产环境
- **WASM**: 不可信代码，跨平台部署

---

## 🧠 2. 记忆系统

### 实现位置
- `kernel/src/memory/mod.rs` - 记忆管理

### 功能特性

- ✅ 短期记忆（HashMap 存储）
- ✅ 长期记忆（可持久化）
- ✅ 记忆过期自动清理
- ✅ 标签分类和搜索
- ✅ 重要性评分

### Python SDK 使用

```python
from neuroflow.memory import MemoryManager, MemoryConfig

# 创建记忆管理器
config = MemoryConfig(
    max_entries=10000,
    gc_interval_seconds=300,
)

manager = MemoryManager(config)

# 存储记忆
await manager.store_memory(
    agent_id="user-123",
    key="preference:theme",
    value={"theme": "dark", "lang": "zh"},
    tags=["preference", "ui"],
    importance=0.8,
)

# 检索记忆
memory = await manager.retrieve_memory(
    agent_id="user-123",
    key="preference:theme",
)
print(f"记忆内容：{memory.value}")

# 搜索记忆
memories = await manager.search_memories(
    agent_id="user-123",
    tags=["preference"],
    min_importance=0.5,
    limit=10,
)

# 删除记忆
await manager.delete_memory(
    agent_id="user-123",
    key="preference:theme",
)
```

### 适用场景

- Agent 对话历史存储
- 用户偏好记忆
- 上下文信息管理
- 知识积累

---

## 🤝 3. A2A 协作系统

### 实现位置
- `kernel/src/a2a/mod.rs` - Agent 间协作

### 功能特性

- ✅ Agent 注册和发现
- ✅ 协作编排器
- ✅ HTTP/gRPC 通信协议
- ✅ 深度限制（防止无限递归）
- ✅ 超时控制

### Python SDK 使用

```python
from neuroflow.a2a import (
    AgentRegistryService,
    AgentRegistration,
    CollaborativeOrchestratorV2,
    CollaborationContext,
)

# ========== Agent 注册 ==========
registry = AgentRegistryService(backend="memory")
await registry.start()

# 注册 Agent
agent = AgentRegistration(
    id="researcher",
    name="Research Agent",
    description="专业研究助手",
    endpoint="http://localhost:8081",
    capabilities=["web_search", "research"],
)
await registry.register(agent)

# 发现 Agent
researchers = await registry.discover_by_capability("web_search")
print(f"找到 {len(researchers)} 个研究 Agent")

# ========== 协作编排 ==========
orchestrator = CollaborativeOrchestratorV2(
    llm_orchestrator=llm_orchestrator,
    agent_registry_service=registry,
    max_depth=5,  # 最大协作深度
    timeout_ms=30000,
)

# 执行协作任务
result = await orchestrator.execute_with_collaboration(
    user_message="研究 AI 发展趋势并生成报告",
)

print(f"参与 Agent: {result.collaborating_agents}")
print(f"最终回复：{result.response}")
```

### 适用场景

- 多 Agent 协作任务
- 专业 Agent 分工
- 复杂工作流编排

---

## 🔌 4. MCP 集成

### 实现位置
- `kernel/src/mcp/mod.rs` - MCP 服务器管理

### 功能特性

- ✅ MCP 服务器连接管理
- ✅ 工具发现和注册
- ✅ 工具执行
- ✅ 健康检查
- ✅ 连接池管理

### Python SDK 使用

```python
from neuroflow.mcp import (
    MCPServerManager,
    MCPConfigParser,
    RealMCPExecutor,
    MCPHealthMonitor,
)

# ========== 方式 1: 使用服务器管理器 ==========
parser = MCPConfigParser()
config = parser.parse_from_file("config.yaml")

manager = MCPServerManager()
await manager.start_from_config(config)

# 检查服务器状态
statuses = manager.get_all_statuses()
for name, status in statuses.items():
    print(f"{name}: {'✅' if status.connected else '❌'}")

# 执行工具
result = await manager.execute_tool(
    server_name="filesystem",
    tool_name="read_file",
    arguments={"path": "/tmp/test.txt"},
)
print(f"文件内容：{result['result']}")

# ========== 方式 2: 直接使用执行器 ==========
executor = RealMCPExecutor()

# 启动 MCP 服务器
await executor.start_server(
    name="filesystem",
    server_type="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
)

# 执行工具
result = await executor.execute_tool(
    server_name="filesystem",
    tool_name="write_file",
    arguments={"path": "/tmp/test.txt", "content": "Hello"},
)

# 健康监控
monitor = MCPHealthMonitor()
await monitor.start_monitoring(executor)

stats = monitor.get_statistics()
print(f"健康服务器：{stats['healthy']}")
```

### 适用场景

- 连接外部工具服务器
- 文件系统操作
- 记忆存储
- 网络搜索

---

## 📊 5. 可观测性系统

### 实现位置
- `kernel/src/observability/mod.rs` - 追踪和指标
- `kernel/src/observability/tracer.rs` - 链路追踪
- `kernel/src/observability/metrics.rs` - 指标收集

### 功能特性

- ✅ OpenTelemetry 集成
- ✅ 分布式链路追踪
- ✅ 指标收集（请求数、延迟、错误率）
- ✅ 结构化日志
- ✅ 支持 Jaeger/Prometheus 后端

### Python SDK 使用

```python
from neuroflow.observability import (
    TracingService,
    MetricsCollector,
    StructuredLogger,
    SpanKind,
)

# ========== 链路追踪 ==========
tracing = TracingService(
    service_name="my-agent",
    exporter_endpoint="http://localhost:4317",  # Jaeger
)
await tracing.start()

# 创建 span
with tracing.span("tool_execution", kind=SpanKind.CLIENT) as span:
    span.set_attribute("tool_name", "search")
    result = await execute_tool()
    span.set_attribute("result.success", True)

await tracing.stop()

# ========== 指标收集 ==========
metrics = MetricsCollector()

# 计数器
metrics.increment("tool_invocations", tags={"tool": "search"})

# 仪表
metrics.gauge("active_connections", 42)

# 直方图
metrics.histogram("request_latency", 123.45, tags={"endpoint": "/api"})

# 获取统计
stats = metrics.get_summary()
print(f"工具调用次数：{stats['counters']['tool_invocations']}")

# ========== 结构化日志 ==========
logger = StructuredLogger("neuroflow")

logger.info("Request received", request_id="123", method="GET")
logger.error("Request failed", exc_info=e, request_id="123")
```

### 适用场景

- 性能监控
- 故障排查
- 链路追踪
- 运营分析

---

## 🔒 6. 安全系统

### 实现位置
- `kernel/src/security/mod.rs` - 安全控制
- `kernel/src/security/guard.rs` - 安全守卫

### 功能特性

- ✅ 权限控制
- ✅ 审计日志
- ✅ 命令白名单
- ✅ 资源限制

### Python SDK 使用

```python
from neuroflow.sandbox import SandboxConfig, SandboxSecurityLevel

# 安全级别配置
config = SandboxConfig(
    security_level=SandboxSecurityLevel.STRICT,
    allowed_commands=["python3", "pip", "ls"],
    enable_seccomp=True,
    enable_network=False,
)

# 审计日志
from neuroflow.security import AuditLogger

logger = AuditLogger(output_file="/var/log/neuroflow/audit.log")

await logger.log_event(
    event_type="command_execution",
    agent_id="agent-1",
    details={"command": "python3 script.py"},
    result="success",
)
```

### 适用场景

- 生产环境安全
- 合规审计
- 权限管理

---

## 🎯 完整使用示例

### 示例：构建智能研究 Agent

```python
from neuroflow import AINativeAgent, LLMConfig
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig
from neuroflow.memory import MemoryManager
from neuroflow.mcp import MCPServerManager
from neuroflow.observability import TracingService

# 1. 创建 Agent
agent = AINativeAgent(
    name="researcher",
    llm_config=LLMConfig(provider="openai", model="gpt-4"),
)

# 2. 配置沙箱（安全执行）
sandbox_config = WasmSandboxConfig(
    max_memory_bytes=128 * 1024 * 1024,
    timeout_seconds=60,
)
sandbox = WasmSandbox(sandbox_config)

# 3. 配置记忆（上下文管理）
memory = MemoryManager()

# 4. 配置 MCP（工具集成）
mcp_manager = MCPServerManager()
await mcp_manager.start_from_config("config.yaml")

# 5. 配置追踪（可观测性）
tracing = TracingService(service_name="researcher")
await tracing.start()

# 6. 注册工具
@agent.tool(name="research")
async def research(topic: str) -> str:
    """研究某个主题"""
    with tracing.span("research_tool") as span:
        # 在沙箱中执行研究代码
        with open("research.wasm", "rb") as f:
            result = await sandbox.execute(f.read())
        
        # 存储结果到记忆
        await memory.store_memory(
            agent_id="researcher",
            key=f"research:{topic}",
            value={"result": result.output},
            tags=["research"],
        )
        
        span.set_attribute("topic", topic)
        return result.output.decode()

# 7. 执行研究任务
result = await agent.handle("研究 AI 发展趋势")
print(result["response"])

# 8. 清理
await tracing.stop()
await mcp_manager.stop_all()
```

---

## 📊 能力对比表

| 功能模块 | Rust 实现 | Python SDK | 状态 |
|---------|---------|----------|------|
| **沙箱隔离** | ✅ 完整 | ✅ 完整 | 生产就绪 |
| **记忆系统** | ✅ 完整 | ✅ 完整 | 生产就绪 |
| **A2A 协作** | ✅ 完整 | ✅ 完整 | 生产就绪 |
| **MCP 集成** | ✅ 完整 | ✅ 完整 | 生产就绪 |
| **可观测性** | ✅ 完整 | ✅ 完整 | 生产就绪 |
| **安全系统** | ✅ 完整 | ✅ 完整 | 生产就绪 |

---

## 🚀 快速开始

```bash
# 1. 安装 SDK
cd sdk
pip install -e .

# 2. 构建 Rust 内核
cd ../kernel
cargo build --release

# 3. 运行示例
cd ../sdk
python examples/agent_with_memory.py
```

---

## 📚 相关文档

- [沙箱使用指南](../docs-site/docs/guides/sandbox-usage.md)
- [记忆系统](../docs-site/docs/concepts/memory.md)
- [A2A 协作](../docs-site/docs/guides/a2a-collaboration.md)
- [MCP 集成](../docs-site/docs/guides/using-mcp.md)
- [可观测性](../docs-site/docs/guides/observability.md)

---

**最后更新**: 2026-03-20  
**版本**: v0.5.0
