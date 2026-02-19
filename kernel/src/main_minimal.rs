/// NeuroFlow Kernel - Minimal Version for Memory Testing
/// 
/// 简化版本，只包含 Memory 功能

use actix_web::{web, App, HttpServer};
use std::sync::Arc;
use tracing::info;

mod memory;
mod knowledge;
mod mcp;
mod grpc;
mod utils;

use memory::{MemoryManager, InMemoryBackend, MemoryConfig};
use mcp::MCPService;
use grpc::MemoryService;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // 初始化日志
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));

    info!("Starting NeuroFlow Kernel - Memory Edition");
    info!("Version: {}", env!("CARGO_PKG_VERSION"));

    // ========== 初始化 Memory 模块 ==========
    info!("Initializing Memory module...");
    let memory_config = MemoryConfig::default();
    let memory_manager = Arc::new(MemoryManager::new(
        Arc::new(InMemoryBackend::new(memory_config.clone())),
        memory_config,
    ));
    info!("Memory module initialized");

    // ========== 初始化 MCP 模块 ==========
    info!("Initializing MCP module...");
    let mcp_service = Arc::new(MCPService::new(crate::mcp::MCPConfig::default()));
    info!("MCP module initialized");

    // ========== 创建 Memory 服务（带 Knowledge Extractor） ==========
    info!("Creating Memory Service with Knowledge Extractor...");
    let memory_service = Arc::new(
        MemoryService::new(memory_manager.clone())
            .with_knowledge_extractor(mcp_service.clone())
    );
    info!("Memory Service created");

    // ========== 启动 HTTP 服务器 ==========
    let http_addr = "0.0.0.0:8080";
    info!("Starting HTTP server on {}", http_addr);
    
    let memory_service_data = web::Data::new(memory_service);
    
    HttpServer::new(move || {
        App::new()
            .app_data(memory_service_data.clone())
            .configure(grpc::configure_memory_routes)
    })
    .bind(http_addr)?
    .run()
    .await
}
