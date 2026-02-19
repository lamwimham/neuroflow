# NeuroFlow 架构设计说明书 (更新版)

| 文档版本 | v1.1 |
| :--- | :--- |
| **状态** | 已更新 (Updated) |
| **适用对象** | 后端工程师 (Rust/Python)、架构师 |
| **核心决策** | Rust 内核 + Python 沙箱 + WASM 隔离 + gRPC 通信 |

## 1. 系统概述 (System Overview)

NeuroFlow 是一个 AI Native 应用运行时框架。系统采用 **双层架构**：
1.  **控制面 (Control Plane)**：由 Rust 实现的内核，负责高并发网关、资源调度、沙箱生命周期管理。
2.  **数据面 (Data Plane)**：由 Python 实现的 Agent 运行环境，运行在 WASM 隔离环境中，负责业务逻辑执行。

**设计目标**：
*   **高性能**：网关延迟 < 5ms，支持高并发。
*   **强隔离**：Agent 代码运行在 WASM 沙箱中，故障不影响内核。
*   **易扩展**：支持 Agent 代码热更新，无需重启服务。
*   **可观测**：内置 OpenTelemetry 支持，完整链路追踪。

## 2. 总体架构 (High-Level Architecture)

```mermaid
graph TD
    Client[客户端 HTTP/gRPC] --> Gateway[Rust HTTP 网关]
    Gateway --> Router[语义路由模块]
    Router --> Scheduler[沙箱调度器]
    Scheduler -->|gRPC over UDS| Sandbox1[WASM 沙箱 1]
    Scheduler -->|gRPC over UDS| Sandbox2[WASM 沙箱 2]
    Sandbox1 --> Agent1[用户 Agent 代码]
    Sandbox2 --> Agent2[用户 Agent 代码]
    Gateway --> Obs[可观测性模块 (OTel)]
    Router --> Vector[向量索引与匹配]
    Vector --> Model[SBERT 模型加载器]
    Obs -->|OTLP| Collector[OTel 收集器]
    Collector -->|Export| Jaeger[Jaeger]
    Collector -->|Export| Prometheus[Prometheus]
```

## 3. 核心模块设计 (Core Modules)

### 3.1 Rust 内核 (Kernel)
*   **技术栈**: `Tokio`, `Axum` (HTTP), `Tonic` (gRPC), `Wasmtime` (WASM), `Notify` (文件监听).
*   **职责**:
    *   **Gateway**: 接收外部请求，鉴权，限流，路由。
    *   **Router**: 基于向量相似度的语义路由。
    *   **Scheduler**: 维护沙箱池，分配请求到空闲沙箱。
    *   **Sandbox Manager**: 启动/管理 WASM 沙箱，管理资源配额。
    *   **Observability**: 集成 OpenTelemetry，提供指标、追踪、日志。

### 3.2 Python SDK & Runtime
*   **技术栈**: `Asyncio`, `Pydantic`, `grpcio`, `Sentence-Transformers`, `FAISS`.
*   **职责**:
    *   **SDK**: 提供 `@agent`, `@tool` 装饰器，屏蔽底层通信细节。
    *   **Runtime**: WASM 环境中的 Python 运行时。
    *   **Vector Engine**: 集成 SBERT 模型和 FAISS 索引，实现语义匹配。

### 3.3 通信协议 (Protocol)
*   **协议**: gRPC over Protobuf (内部通信)。
*   **传输**:
    *   **生产环境**: Unix Domain Socket (高性能)。
    *   **开发环境**: TCP (localhost)。
*   **定义文件**: `proto/runtime.proto`.

## 4. 关键接口定义 (Key Interfaces)

### 4.1 内部通信协议 (runtime.proto)
```protobuf
syntax = "proto3";
package neuroflow.runtime.v1;

// 内核 -> 沙箱：调用请求
message InvokeRequest {
  string trace_id = 1;
  string agent_id = 2;
  string skill_name = 3;
  bytes payload = 4; // JSON encoded
  Context context = 5;
}

// 沙箱 -> 内核：响应
message InvokeResponse {
  bool success = 1;
  bytes data = 2;
  string error_message = 3;
  Metrics metrics = 4;
}

// 内核 -> 沙箱：健康检查
message HealthCheckRequest {}
message HealthCheckResponse {
  bool healthy = 1;
  string version = 2;
}
```

### 4.2 沙箱管理接口 (Rust Trait)
```rust
pub trait SandboxProvider: Send + Sync {
    // 启动沙箱
    async fn spawn(&self, config: SandboxConfig) -> Result<SandboxInstance>;
    // 调用执行
    async fn invoke(&self, instance: &SandboxInstance, req: InvokeRequest) -> Result<InvokeResponse>;
    // 销毁沙箱
    async fn destroy(&self, instance: &SandboxInstance) -> Result<()>;
}
```

### 4.3 可观测性接口定义
```rust
pub trait ObservabilityProvider: Send + Sync {
    // 记录指标
    fn record_metric(&self, name: &str, value: f64, labels: &[(&str, &str)]);
    // 开始追踪Span
    fn start_span(&self, name: &str, attributes: &[(&str, &str)]) -> Span;
    // 记录日志
    fn log(&self, level: LogLevel, message: &str, attributes: &[(&str, &str)]);
}
```

## 5. 安全设计 (Security Design)

1.  **WASM隔离**: 使用 WASM 运行时提供沙箱隔离，限制系统调用。
2.  **资源限制**: 每个 WASM 沙箱限制内存和执行时间，防止资源耗尽。
3.  **通信安全**: gRPC 通信使用 Unix Domain Socket，避免网络攻击面。
4.  **输入验证**: 内核对所有输入进行严格验证和过滤。

## 6. 可观测性 (Observability)

1.  **Trace**: 全链路遵循 W3C Trace Context，通过 gRPC Metadata 透传 `trace_id`。
2.  **Metric**: 内核暴露 Prometheus metrics (`neuroflow_request_duration`, `sandbox_cpu_usage`)。
3.  **Log**: 结构化 JSON 日志，统一收集到 stdout。
4.  **集成**: 支持 OpenTelemetry，可导出到 Jaeger、Zipkin、Prometheus 等后端。