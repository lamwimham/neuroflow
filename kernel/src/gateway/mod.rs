use axum::{
    extract::State,
    http::HeaderMap,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use tower::ServiceBuilder;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;
use tokio::net::TcpListener;
use tracing::info;
use uuid::Uuid;

use crate::{
    config::{Config, ServerConfig},
    middleware::{
        cors_middleware, input_validation, rate_limit_middleware,
        request_size_limit, security_headers, timeout_middleware,
    },
    tool_router::{ToolRegistry, ToolCall},
};

#[derive(Debug, Clone)]
pub struct AppState {
    pub config: Arc<Config>,
    pub tool_registry: Arc<ToolRegistry>,
}

impl AppState {
    pub fn new(config: Arc<Config>) -> Self {
        Self {
            config,
            tool_registry: Arc::new(ToolRegistry::new()),
        }
    }
}

#[derive(Deserialize, Debug)]
pub struct InvokeRequest {
    pub agent: Option<String>,
    pub skill: Option<String>,
    pub payload: Value,
}

#[derive(Serialize)]
pub struct InvokeResponse {
    pub success: bool,
    pub data: Option<Value>,
    pub error: Option<String>,
    pub trace_id: String,
}

// ========== 工具路由相关请求/响应类型 ==========

#[derive(Serialize)]
pub struct ToolsListResponse {
    pub tools: Vec<serde_json::Value>,
}

#[derive(Deserialize, Debug)]
pub struct ToolInvokeRequest {
    #[serde(rename = "toolName")]
    pub tool_name: String,
    pub arguments: serde_json::Value,
    #[serde(rename = "timeoutMs", default = "default_timeout")]
    pub timeout_ms: u64,
}

fn default_timeout() -> u64 {
    30000
}

#[derive(Serialize)]
pub struct ToolInvokeResponse {
    pub success: bool,
    pub result: Option<serde_json::Value>,
    pub error: Option<String>,
    #[serde(rename = "executionTimeMs")]
    pub execution_time_ms: u64,
    pub trace_id: String,
}

pub fn create_router(state: AppState) -> Router {
    let middleware_stack = ServiceBuilder::new()
        .layer(axum::middleware::from_fn(request_size_limit))
        .layer(axum::middleware::from_fn(timeout_middleware))
        .layer(axum::middleware::from_fn(input_validation))
        .layer(axum::middleware::from_fn(rate_limit_middleware))
        .layer(axum::middleware::from_fn(security_headers))
        .layer(axum::middleware::from_fn(cors_middleware));

    Router::new()
        // 原有端点
        .route("/", get(health_check))
        .route("/invoke", post(invoke_handler))
        .route("/health", get(health_check))
        // 新增工具路由端点
        .route("/tools", get(list_tools_handler))
        .route("/tools/invoke", post(invoke_tool_handler))
        .with_state(state)
        .layer(middleware_stack)
}

pub async fn health_check(State(state): State<AppState>) -> impl IntoResponse {
    info!("Health check requested");
    Json(serde_json::json!({
        "status": "healthy",
        "version": env!("CARGO_PKG_VERSION"),
        "port": state.config.server.port,
        "environment": state.config.environment
    }))
}

pub async fn invoke_handler(
    State(_state): State<AppState>,
    headers: HeaderMap,
    Json(request): Json<InvokeRequest>,
) -> Json<InvokeResponse> {
    let trace_id = headers
        .get("x-trace-id")
        .and_then(|h| h.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    info!(
        trace_id = %trace_id,
        agent = ?request.agent,
        skill = ?request.skill,
        "Processing invoke request"
    );

    // TODO: 集成真实沙箱调用
    let response = InvokeResponse {
        success: true,
        data: Some(serde_json::json!({
            "message": "Hello from NeuroFlow!",
            "trace_id": trace_id,
            "agent": request.agent.unwrap_or_else(|| "default".to_string()),
            "payload": request.payload
        })),
        error: None,
        trace_id,
    };

    Json(response)
}

// ========== 工具路由端点处理函数 ==========

pub async fn list_tools_handler(
    State(state): State<AppState>,
) -> Json<ToolsListResponse> {
    let tools = state.tool_registry.get_all_llm_schemas().await;
    
    Json(ToolsListResponse {
        tools,
    })
}

pub async fn invoke_tool_handler(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(request): Json<ToolInvokeRequest>,
) -> Json<ToolInvokeResponse> {
    let trace_id = headers
        .get("x-trace-id")
        .and_then(|h| h.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    let call = ToolCall {
        call_id: Uuid::new_v4().to_string(),
        tool_name: request.tool_name.clone(),
        arguments: request.arguments.clone(),
        timeout_ms: request.timeout_ms,
    };

    info!(
        trace_id = %trace_id,
        tool = %request.tool_name,
        "Invoking tool"
    );

    match state.tool_registry.execute(call).await {
        Ok(result) => {
            Json(ToolInvokeResponse {
                success: result.success,
                result: Some(result.result),
                error: result.error,
                execution_time_ms: result.execution_time_ms,
                trace_id,
            })
        }
        Err(e) => {
            Json(ToolInvokeResponse {
                success: false,
                result: None,
                error: Some(e.to_string()),
                execution_time_ms: 0,
                trace_id,
            })
        }
    }
}

pub async fn start_http_server(host: String, port: u16) -> Result<(), Box<dyn std::error::Error>> {
    // 创建简化配置
    let config = Config {
        server: ServerConfig {
            host: host.clone(),
            port,
            ..Default::default()
        },
        ..Default::default()
    };

    let state = AppState::new(Arc::new(config));

    let app = create_router(state.clone());

    let addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(&addr).await?;

    info!("HTTP server listening on {}", addr);

    axum::serve(listener, app).await?;

    Ok(())
}