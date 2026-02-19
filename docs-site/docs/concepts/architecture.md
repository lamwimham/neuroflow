# 架构概览

NeuroFlow 采用 **Rust 内核 + Python 沙箱** 的双层架构设计，实现了高性能基础设施与灵活业务逻辑的完美分离。

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                  应用层 (Application Layer)              │
│  • Python Agents                                        │
│  • 业务逻辑                                             │
│  • MCP 服务集成                                          │
├─────────────────────────────────────────────────────────┤
│              Python SDK (业务逻辑层)                     │
│  • @agent 装饰器                                        │
│  • @tool 装饰器                                         │
│  • NeuroFlowSDK                                         │
│  • A2A 通信器                                            │
│  • MCP 客户端                                            │
├─────────────────────────────────────────────────────────┤
│              Rust Kernel (基础设施层)                    │
│  • HTTP/gRPC 网关 (Axum + Tokio)                        │
│  • Python 进程沙箱                                       │
│  • WASM 沙箱 (开发中)                                    │
│  • 资源调度器                                           │
│  • 可观测性 (OpenTelemetry)                             │
├─────────────────────────────────────────────────────────┤
│                  系统层 (System Layer)                   │
│  • Linux/macOS/Windows                                  │
│  • 网络栈                                               │
│  • 文件系统                                             │
└─────────────────────────────────────────────────────────┘
```

## 核心设计原则

### 1. 关注点分离 (Separation of Concerns)

**Rust 内核** 专注于:
- 🔧 基础设施服务 (HTTP 网关、沙箱运行时)
- 📊 资源管理和调度
- 🔒 安全隔离和权限控制
- 📈 可观测性 (追踪、指标、日志)

**Python SDK** 专注于:
- 🤖 Agent 业务逻辑
- 🛠️ 工具开发和组合
- 🔌 外部服务集成 (MCP)
- 💬 Agent 间通信 (A2A)

### 2. 显式初始化 (Explicit Initialization)

NeuroFlow 采用显式初始化模式，避免异步初始化陷阱:

```python
# ❌ 避免：模块加载时的隐式初始化
from neuroflow import sdk  # 不推荐

# ✅ 推荐：显式初始化
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()
# 或者
sdk = NeuroFlowSDK()
await sdk.initialize()
```

**优势**:
- 🎯 初始化时机可控
- 🐛 避免异步竞态条件
- 📝 代码意图更清晰
- 🔍 更容易调试

### 3. 最小配置 (Minimal Configuration)

NeuroFlow 只保留 5 个核心配置项:

```python
from neuroflow import SDKConfig

config = SDKConfig(
    log_level="info",          # 日志级别
    enable_tracing=True,       # 启用链路追踪
    enable_metrics=True,       # 启用指标收集
    server_url="http://localhost:8080"  # 服务器地址
)

sdk = await NeuroFlowSDK.create(config)
```

### 4. 性能优先 (Performance First)

| 组件 | 技术选型 | 性能目标 |
|------|---------|---------|
| HTTP 网关 | Axum + Tokio | P50 < 10ms, P99 < 20ms |
| 沙箱隔离 | 进程/WASM | 启动 < 50ms, 内存 < 30MB |
| 并发模型 | Async/Await | 10+ 并发沙箱 |
| 序列化 | Protobuf | 比 JSON 快 3-5 倍 |

## 核心组件

### Python SDK 组件

#### 1. NeuroFlowSDK

统一的 SDK 入口，提供:

```python
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()

# 执行工具
result = await sdk.execute_tool("calculate", expression="2+2")

# 注册 Agent
sdk.register_agent("my_agent", MyAgentClass)

# 获取上下文
ctx = sdk.get_context()

# 关闭 SDK
await sdk.shutdown()
```

#### 2. Agent 系统

Agent 是业务逻辑的基本单元:

```python
from neuroflow import agent, tool, BaseAgent

@agent(name="weather_agent", description="天气查询 Agent")
class WeatherAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        city = request.get("city", "Beijing")
        weather = await self.execute_tool("get_weather", city=city)
        return {"weather": weather}
```

**Agent 生命周期**:
1. **创建**: 使用 `@agent` 装饰器
2. **注册**: 自动注册到全局注册表
3. **初始化**: 创建实例并初始化上下文
4. **执行**: 调用 `handle()` 处理请求
5. **销毁**: 清理资源和上下文

#### 3. 工具系统

工具是可复用的功能单元:

```python
from neuroflow import tool

@tool(name="get_weather", description="获取天气信息")
async def get_weather(city: str) -> str:
    # 实现天气查询逻辑
    return f"Sunny in {city}"
```

**工具特性**:
- ✅ 自动类型检查
- ✅ 支持异步执行
- ✅ 权限控制
- ✅ 元数据注册
- ✅ 分类管理

#### 4. A2A 通信器

Agent 间通信 (Agent-to-Agent):

```python
# 请求其他 Agent 协助
result = await agent.request_assistance(
    target_agent="data_agent",
    task="analyze_data",
    params={"data": [...]}
)
```

#### 5. MCP 客户端

模型上下文协议 (Model Context Protocol) 客户端:

```python
# 获取文本嵌入
embeddings = await agent.get_embeddings(["text1", "text2"])

# 生成文本
text = await agent.generate_text(prompt="Write a poem")
```

#### 6. 上下文和记忆系统

```python
# 存储记忆
agent.store_memory(
    key="user_preference",
    value={"theme": "dark"},
    memory_type="long_term",
    tags=["user", "preference"],
    importance=0.8
)

# 检索记忆
preference = agent.retrieve_memory("user_preference")

# 搜索记忆
memories = agent.search_memories_by_tags(["user"])
```

### Rust 内核组件

#### 1. HTTP 网关

基于 Axum + Tokio 的高性能网关:

```rust
// kernel/src/gateway.rs
use axum::{Router, routing::post};

pub fn create_router() -> Router {
    Router::new()
        .route("/invoke", post(invoke_agent))
        .route("/health", get(health_check))
}
```

**特性**:
- ⚡ 异步非阻塞 I/O
- 🔒 请求验证和限流
- 📊 内置指标收集
- 🔄 自动重试和熔断

#### 2. Python 进程沙箱

提供进程级隔离:

```rust
// kernel/src/sandbox/python_process.rs
pub struct PythonProcessSandbox {
    process: Child,
    resource_limits: ResourceLimits,
}

impl Sandbox for PythonProcessSandbox {
    async fn execute(&mut self, code: &str) -> Result<ExecutionResult> {
        // 在隔离进程中执行 Python 代码
    }
}
```

**安全特性**:
- 🔒 文件系统隔离
- 📉 CPU/内存限制
- 🚫 网络访问控制
- ⏱️ 执行超时

#### 3. 可观测性

基于 OpenTelemetry 的完整可观测性:

```python
# 自动追踪所有工具调用
sdk = await NeuroFlowSDK.create(
    SDKConfig(enable_tracing=True, enable_metrics=True)
)

# 在 Jaeger/Zipkin 中查看追踪
# 在 Prometheus 中查看指标
```

**追踪内容**:
- 📍 Agent 调用链
- 🛠️ 工具执行时间
- 🌐 A2A 通信延迟
- 💾 记忆操作

## 数据流

### 典型请求流程

```
用户请求
   │
   ▼
┌─────────────────┐
│  HTTP 网关      │ ← 鉴权、限流
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 调度器    │ ← 选择目标 Agent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Python 沙箱    │ ← 隔离执行
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  工具执行       │ ← 调用工具/MCP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  响应返回       │ ← 序列化结果
└─────────────────┘
```

### A2A 通信流程

```
Agent A
   │
   │ 1. 发送协助请求
   ▼
┌─────────────────┐
│  A2A 路由器      │
└────────┬────────┘
         │
         ▼
Agent B
   │
   │ 2. 执行任务
   ▼
   │ 3. 返回结果
   ▼
Agent A
```

## 部署架构

### 开发环境

```
┌──────────────────┐
│  开发机器        │
│  ┌────────────┐  │
│  │ Python SDK │  │
│  └────────────┘  │
│  ┌────────────┐  │
│  │ Rust Kernel│  │
│  └────────────┘  │
└──────────────────┘
```

### 生产环境

```
┌─────────────────────────────────┐
│         负载均衡器              │
└────────────┬────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Node 1 │ │ Node 2 │ │ Node 3 │
│ ┌────┐ │ │ ┌────┐ │ │ ┌────┐ │
│ │网关│ │ │ │网关│ │ │ │网关│ │
│ └────┘ │ │ └────┘ │ │ └────┘ │
└────────┘ └────────┘ └────────┘
```

## 性能优化策略

### 1. 连接池化

```python
# SDK 内部使用连接池
sdk = await NeuroFlowSDK.create(
    SDKConfig(server_url="http://localhost:8080")
)
# 自动复用 HTTP 连接
```

### 2. 批量执行

```python
# 批量执行工具 (减少网络往返)
results = await sdk.batch_execute([
    ("tool1", {"arg": "value1"}),
    ("tool2", {"arg": "value2"}),
])
```

### 3. 缓存策略

```python
# 工具结果缓存
@tool(name="expensive_operation", cache_ttl=300)
async def expensive_op(param: str) -> str:
    # 5 分钟内相同参数直接返回缓存
```

## 安全模型

### 沙箱隔离

```
┌─────────────────────────────────┐
│         Host System             │
│  ┌───────────────────────────┐  │
│  │   Python Process Sandbox  │  │
│  │  ┌─────────────────────┐  │  │
│  │  │   Agent Code        │  │  │
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### 权限控制

```python
from neuroflow import PermissionLevel, tool

@tool(
    name="admin_operation",
    permissions=[PermissionLevel.ADMIN]
)
async def admin_op():
    # 仅管理员可执行
```

## 扩展性

### 插件系统 (计划中)

```python
# 加载插件
await sdk.load_plugin("neuroflow-plugin-redis")
await sdk.load_plugin("neuroflow-plugin-ollama")
```

### 自定义沙箱

```rust
// 实现自定义沙箱
impl Sandbox for CustomSandbox {
    async fn execute(&mut self, code: &str) -> Result<ExecutionResult> {
        // 自定义执行逻辑
    }
}
```

## 下一步

- 📖 **[Agent 基础](agents.md)** - 深入理解 Agent
- 🛠️ **[工具系统](tools.md)** - 学习工具开发
- 🔒 **[沙箱模型](sandbox.md)** - 了解隔离机制
- ⚙️ **[配置管理](configuration.md)** - 配置选项详解

---

**参考资源**:
- [NeuroFlow GitHub](https://github.com/lamWimHam/neuroflow)
- [Rust 内核源码](https://github.com/lamWimHam/neuroflow/tree/main/kernel)
- [Python SDK 源码](https://github.com/lamWimHam/neuroflow/tree/main/sdk)
