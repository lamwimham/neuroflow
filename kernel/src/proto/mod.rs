// src/proto/mod.rs
// Proto 模块 - 提供 gRPC 服务定义

// 由于 protoc 编译问题，这里提供简化实现
// 在完整环境中，应该使用 tonic::include_proto!

/// 调用请求
#[derive(Debug, Clone)]
pub struct InvokeRequest {
    pub agent_id: String,
    pub payload: String,
}

/// 调用响应
#[derive(Debug, Clone)]
pub struct InvokeResponse {
    pub result: String,
    pub error: Option<String>,
}

/// 健康检查请求
#[derive(Debug, Clone, Default)]
pub struct HealthCheckRequest {}

/// 健康检查响应
#[derive(Debug, Clone)]
pub struct HealthCheckResponse {
    pub status: String,
    pub version: String,
}

/// 沙箱注册请求
#[derive(Debug, Clone)]
pub struct RegisterSandboxRequest {
    pub sandbox_id: String,
    pub config: String,
}

/// 沙箱注册响应
#[derive(Debug, Clone)]
pub struct RegisterSandboxResponse {
    pub success: bool,
    pub message: String,
}

/// RuntimeService 客户端 trait
pub trait RuntimeServiceClient: Send + Sync {
    fn invoke(&self, request: InvokeRequest) -> Result<InvokeResponse, Box<dyn std::error::Error>>;
    fn health_check(&self) -> Result<HealthCheckResponse, Box<dyn std::error::Error>>;
}

// 空的客户端实现
pub struct EmptyRuntimeServiceClient;

impl RuntimeServiceClient for EmptyRuntimeServiceClient {
    fn invoke(&self, _request: InvokeRequest) -> Result<InvokeResponse, Box<dyn std::error::Error>> {
        Err("RuntimeService not configured".into())
    }
    
    fn health_check(&self) -> Result<HealthCheckResponse, Box<dyn std::error::Error>> {
        Ok(HealthCheckResponse {
            status: "ok".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
        })
    }
}
