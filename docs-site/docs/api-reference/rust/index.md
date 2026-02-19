# Rust Kernel API 参考

NeuroFlow Rust 内核提供了高性能的基础设施层。

## 核心模块

### Gateway (HTTP 网关)

基于 Axum 的高性能 HTTP 网关。

**模块路径**: `neuroflow_kernel::gateway`

**主要结构**:

```rust
use neuroflow_kernel::gateway::{Gateway, GatewayConfig};

#[tokio::main]
async fn main() {
    let config = GatewayConfig {
        host: "0.0.0.0".to_string(),
        port: 8080,
        ..Default::default()
    };
    
    let gateway = Gateway::new(config);
    gateway.start().await.unwrap();
}
```

**配置项**:

```rust
pub struct GatewayConfig {
    pub host: String,           // 监听地址
    pub port: u16,              // 监听端口
    pub max_connections: usize, // 最大连接数
    pub timeout_secs: u64,      // 超时时间 (秒)
}

impl Default for GatewayConfig {
    fn default() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            port: 8080,
            max_connections: 1000,
            timeout_secs: 30,
        }
    }
}
```

**路由**:

```rust
// 内部实现
pub fn create_router() -> Router {
    Router::new()
        .route("/invoke", post(invoke_agent))
        .route("/health", get(health_check))
        .route("/metrics", get(get_metrics))
        .route("/traces", get(get_traces))
}
```

---

### Sandbox (沙箱)

Agent 执行沙箱环境。

**模块路径**: `neuroflow_kernel::sandbox`

**Sandbox trait**:

```rust
use neuroflow_kernel::sandbox::{Sandbox, ExecutionResult};

pub trait Sandbox {
    /// 执行代码
    async fn execute(&mut self, code: &str) -> Result<ExecutionResult>;
    
    /// 获取沙箱状态
    fn status(&self) -> SandboxStatus;
    
    /// 关闭沙箱
    async fn shutdown(&mut self) -> Result<()>;
}
```

**Python 进程沙箱**:

```rust
use neuroflow_kernel::sandbox::PythonProcessSandbox;

let mut sandbox = PythonProcessSandbox::new(config);
let result = await sandbox.execute("print('Hello')");
```

**配置**:

```rust
pub struct SandboxConfig {
    pub python_path: String,        // Python 解释器路径
    pub memory_limit_mb: usize,     // 内存限制 (MB)
    pub cpu_limit: f32,             // CPU 限制 (核心数)
    pub timeout_secs: u64,          // 超时时间
    pub allow_network: bool,        // 允许网络访问
}
```

**执行结果**:

```rust
pub struct ExecutionResult {
    pub success: bool,              // 是否成功
    pub output: String,             // 标准输出
    pub error: String,              // 标准错误
    pub exit_code: i32,             // 退出码
    pub duration_ms: u64,           // 执行时间 (毫秒)
}
```

---

### Scheduler (调度器)

资源调度器。

**模块路径**: `neuroflow_kernel::scheduler`

**主要结构**:

```rust
use neuroflow_kernel::scheduler::{Scheduler, SchedulerConfig};

let config = SchedulerConfig {
    max_concurrent_sandboxes: 10,
    ..Default::default()
};

let scheduler = Scheduler::new(config);
```

**配置**:

```rust
pub struct SchedulerConfig {
    pub max_concurrent_sandboxes: usize,  // 最大并发沙箱数
    pub min_sandboxes: usize,             // 最小沙箱数
    pub max_sandboxes: usize,             // 最大沙箱数
    pub scale_up_threshold: f64,          // 扩容阈值 (CPU 使用率)
    pub scale_down_threshold: f64,        // 缩容阈值
}
```

---

### Observability (可观测性)

OpenTelemetry 集成。

**模块路径**: `neuroflow_kernel::observability`

**初始化**:

```rust
use neuroflow_kernel::observability;

#[tokio::main]
async fn main() {
    observability::initialize(
        "neuroflow-kernel",
        "0.1.0",
        "http://localhost:4317"  // OTLP 端点
    ).await;
    
    // 应用代码
}
```

**追踪**:

```rust
use tracing::{info, instrument};
use tracing_opentelemetry::OpenTelemetrySpanExt;

#[instrument(name = "invoke_agent", skip(request))]
async fn invoke_agent(request: Request) -> Result<Response> {
    info!("Processing request");
    
    // 添加自定义属性
    tracing::Span::current().record("agent_name", &request.agent_name);
    
    // 业务逻辑
}
```

**指标**:

```rust
use metrics::{counter, histogram};

// 计数器
counter!("requests_total", 1, "method" => "POST");

// 直方图
histogram!("request_duration_seconds", duration.as_secs_f64());
```

---

### Config (配置)

配置管理。

**模块路径**: `neuroflow_kernel::config`

**加载配置**:

```rust
use neuroflow_kernel::config::Config;

// 从文件加载
let config = Config::from_file("config.yaml")?;

// 从环境变量加载
let config = Config::from_env()?;

// 默认配置
let config = Config::default();
```

**配置结构**:

```rust
pub struct Config {
    pub gateway: GatewayConfig,
    pub sandbox: SandboxConfig,
    pub scheduler: SchedulerConfig,
    pub observability: ObservabilityConfig,
}
```

---

## 使用示例

### 最小内核

```rust
use neuroflow_kernel::{Kernel, KernelConfig};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = KernelConfig::default();
    let kernel = Kernel::new(config);
    
    println!("Starting NeuroFlow Kernel...");
    kernel.start().await?;
    
    Ok(())
}
```

### 自定义配置

```rust
use neuroflow_kernel::{
    Kernel,
    KernelConfig,
    GatewayConfig,
    SandboxConfig,
    SchedulerConfig,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = KernelConfig {
        gateway: GatewayConfig {
            host: "0.0.0.0".to_string(),
            port: 9000,
            max_connections: 500,
            timeout_secs: 60,
        },
        sandbox: SandboxConfig {
            python_path: "/usr/bin/python3".to_string(),
            memory_limit_mb: 512,
            cpu_limit: 2.0,
            timeout_secs: 30,
            allow_network: false,
        },
        scheduler: SchedulerConfig {
            max_concurrent_sandboxes: 20,
            min_sandboxes: 2,
            max_sandboxes: 50,
            scale_up_threshold: 0.8,
            scale_down_threshold: 0.3,
        },
        ..Default::default()
    };
    
    let kernel = Kernel::new(config);
    kernel.start().await?;
    
    Ok(())
}
```

### 中间件

```rust
use axum::{
    middleware::{self, Next},
    http::{Request, StatusCode},
    response::Response,
};

async fn auth_middleware<B>(
    request: Request<B>,
    next: Next<B>,
) -> Result<Response, StatusCode> {
    // 验证逻辑
    let auth_header = request.headers().get("Authorization");
    
    if auth_header.is_some() {
        Ok(next.run(request).await)
    } else {
        Err(StatusCode::UNAUTHORIZED)
    }
}

// 注册中间件
let app = Router::new()
    .route("/invoke", post(invoke_agent))
    .layer(middleware::from_fn(auth_middleware));
```

---

## 性能调优

### 连接池

```rust
use deadpool::managed::Config as PoolConfig;

let pool_config = PoolConfig {
    max_size: 100,
    min_size: 10,
    ..Default::default()
};
```

### 缓存

```rust
use moka::future::Cache;

let cache = Cache::builder()
    .max_capacity(1000)
    .time_to_live(std::time::Duration::from_secs(300))
    .build();

// 使用缓存
let result = cache.get(key).await.unwrap_or_else(|| {
    // 计算并缓存
    let value = compute_value();
    cache.insert(key, value).await;
    value
});
```

---

## 错误处理

### 自定义错误

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum KernelError {
    #[error("Gateway error: {0}")]
    Gateway(#[from] GatewayError),
    
    #[error("Sandbox error: {0}")]
    Sandbox(#[from] SandboxError),
    
    #[error("Scheduler error: {0}")]
    Scheduler(#[from] SchedulerError),
    
    #[error("Configuration error: {0}")]
    Config(String),
}

pub type Result<T> = std::result::Result<T, KernelError>;
```

---

## 测试

### 单元测试

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_gateway_start() {
        let config = GatewayConfig::default();
        let gateway = Gateway::new(config);
        
        assert!(gateway.start().await.is_ok());
    }
}
```

### 集成测试

```rust
#[tokio::test]
async fn test_full_request_flow() {
    let kernel = Kernel::new(KernelConfig::default());
    kernel.start().await.unwrap();
    
    // 发送测试请求
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8080/invoke")
        .json(&serde_json::json!({
            "agent": "test_agent",
            "payload": {}
        }))
        .send()
        .await
        .unwrap();
    
    assert!(response.status().is_success());
}
```

---

**相关文档**:
- [Python SDK API](python/index.md)
- [架构概览](../concepts/architecture.md)
- [配置管理](../concepts/configuration.md)
