/// NeuroFlow Kernel - Main Entry Point (Simplified)

use actix_web::{web, App, HttpServer};
use clap::Parser;
use std::sync::Arc;
use tracing::info;

mod memory;
mod knowledge;
mod mcp;
mod grpc;
mod utils;

use memory::{MemoryManager, MemoryConfig};
use mcp::MCPService;
use grpc::MemoryService;

#[derive(clap::Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(long, default_value_t = 8080)]
    http_port: u16,

    #[arg(long, default_value_t = String::from("info"))]
    log_level: String,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let args = Args::parse();
    
    env_logger::init_from_env(
        env_logger::Env::default().default_filter_or(&args.log_level)
    );

    info!("Starting NeuroFlow Kernel");
    info!("Version: {}", env!("CARGO_PKG_VERSION"));

    // 初始化 Memory
    info!("Initializing Memory module...");
    let memory_manager = Arc::new(MemoryManager::new(MemoryConfig::default()));
    info!("Memory module initialized");

    // 初始化 MCP
    info!("Initializing MCP module...");
    let mcp_service = Arc::new(MCPService::new(mcp::MCPConfig::default()));
    info!("MCP module initialized");

    // 创建 Memory Service
    info!("Creating Memory Service...");
    let memory_service = Arc::new(
        MemoryService::new(memory_manager.clone())
    );
    info!("Memory Service created");

    // 启动 HTTP 服务器
    let http_addr = format!("0.0.0.0:{}", args.http_port);
    info!("Starting HTTP server on {}", http_addr);
    
    let memory_service_data = web::Data::new(memory_service);
    
    HttpServer::new(move || {
        App::new()
            .app_data(memory_service_data.clone())
            .configure(grpc::configure_memory_routes)
    })
    .bind(&http_addr)?
    .run()
    .await
}
