use tonic::{Request, Response, Status};
use tracing::{info, error};

use crate::{
    proto::runtime_service_client::{
        invoke_request::AgentRequest, 
        invoke_response::AgentResponse, 
        health_check_response::Status as HealthStatus,
        RuntimeService, 
        InvokeRequest, 
        InvokeResponse, 
        HealthCheckRequest, 
        HealthCheckResponse,
        RegisterSandboxRequest,
        RegisterSandboxResponse
    },
    runtime::SandboxManager,
    utils::NeuroFlowError,
    observability::predefined_metrics,
};
use std::sync::Arc;
use opentelemetry::trace::{TraceContextExt, Tracer};

// gRPC服务实现
#[derive(Debug, Clone)]
pub struct RuntimeServiceImpl {
    sandbox_manager: Arc<SandboxManager>,
}

impl RuntimeServiceImpl {
    pub fn new(sandbox_manager: Arc<SandboxManager>) -> Self {
        Self { sandbox_manager }
    }
}

#[tonic::async_trait]
impl RuntimeService for RuntimeServiceImpl {
    async fn invoke(
        &self,
        request: Request<InvokeRequest>,
    ) -> Result<Response<InvokeResponse>, Status> {
        let req = request.into_inner();
        info!("Received invoke request: agent_id={}, skill={}", req.agent_id, req.skill_name);

        // 使用OpenTelemetry追踪
        let tracer = opentelemetry::global::tracer("neuroflow-grpc");
        let span = tracer.start("grpc.invoke");
        let _guard = span.context().span().set_parent(span.span_context().clone());

        // 实际调用沙箱逻辑
        let result = self.sandbox_manager.execute_agent_skill(
            &req.agent_id,
            &req.skill_name,
            &req.payload
        ).await;

        match result {
            Ok(data) => {
                let response = InvokeResponse {
                    success: true,
                    data,
                    error_message: String::new(),
                    metrics: None, // 在实际实现中填充执行指标
                };

                // 记录成功调用指标
                predefined_metrics::record_successful_invoke();

                Ok(Response::new(response))
            }
            Err(e) => {
                error!("Failed to execute agent skill: {}", e);
                
                let response = InvokeResponse {
                    success: false,
                    data: vec![], // 空数据
                    error_message: e.to_string(),
                    metrics: None,
                };

                // 记录失败调用指标
                predefined_metrics::record_failed_invoke();

                Ok(Response::new(response))
            }
        }
    }

    async fn health_check(
        &self,
        _request: Request<HealthCheckRequest>,
    ) -> Result<Response<HealthCheckResponse>, Status> {
        info!("Received health check request");

        let response = HealthCheckResponse {
            healthy: true,
            version: "1.0.0".to_string(),
            status: "SERVING".to_string(),
        };

        Ok(Response::new(response))
    }

    async fn register_sandbox(
        &self,
        request: Request<RegisterSandboxRequest>,
    ) -> Result<Response<RegisterSandboxResponse>, Status> {
        let req = request.into_inner();
        info!("Received register sandbox request: agent_id={}", req.agent_id);

        // 在这里可以实现沙箱注册逻辑
        let response = RegisterSandboxResponse {
            success: true,
            sandbox_id: uuid::Uuid::new_v4().to_string(), // 生成唯一沙箱ID
            error_message: String::new(),
        };

        Ok(Response::new(response))
    }
}

// 启动gRPC服务器的函数
pub async fn start_grpc_server(addr: std::net::SocketAddr, service: RuntimeServiceImpl) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    use tonic::transport::Server;

    info!("Starting gRPC server on {}", addr);

    Server::builder()
        .add_service(crate::proto::runtime_service_client::runtime_service_server::RuntimeServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}