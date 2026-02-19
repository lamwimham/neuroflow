use clap::Parser;
use kernel::{
    cli::{Cli, CliExecutor},
    config::{ConfigManager, EnhancedConfig},
    gateway::start_http_server,
    grpc::{start_grpc_server, RuntimeServiceImpl},
    hot_reload::{HotReloadEngine, HotReloadConfig},
    utils::logging::init_logging,
};
use std::net::SocketAddr;
use tracing::info;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// HTTP server port
    #[arg(long, default_value_t = 8080)]
    http_port: u16,
    
    /// gRPC server port
    #[arg(long, default_value_t = 50051)]
    grpc_port: u16,
    
    /// Log level
    #[arg(long, default_value = "info")]
    log_level: String,
    
    /// 运行CLI命令
    #[command(subcommand)]
    pub command: Option<Commands>,
}

#[derive(clap::Subcommand, Debug)]
pub enum Commands {
    /// 运行服务器（默认行为）
    Server(ServerArgs),
}

#[derive(clap::Args, Debug)]
struct ServerArgs {
    /// HTTP server port
    #[arg(long, default_value_t = 8080)]
    http_port: u16,
    
    /// gRPC server port
    #[arg(long, default_value_t = 50051)]
    grpc_port: u16,
    
    /// Log level
    #[arg(long, default_value = "info")]
    log_level: String,
    
    /// Enable debug mode
    #[arg(long)]
    debug: bool,
    
    /// Enable verbose logging
    #[arg(long)]
    verbose: bool,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    // 检查是否运行CLI命令
    if let Some(command) = args.command {
        match command {
            Commands::Server(server_args) => {
                run_server(server_args).await
            }
        }
    } else {
        // 默认运行服务器
        let server_args = ServerArgs {
            http_port: args.http_port,
            grpc_port: args.grpc_port,
            log_level: args.log_level,
            debug: false,
            verbose: false,
        };
        run_server(server_args).await
    }
}

async fn run_server(args: ServerArgs) -> Result<(), Box<dyn std::error::Error>> {
    // 初始化日志
    init_logging()?;
    
    info!("Starting NeuroFlow kernel");
    info!("Version: {}", env!("CARGO_PKG_VERSION"));
    
    // 设置调试模式的日志级别
    if args.debug || args.verbose {
        // 在调试模式下，我们不需要重新初始化日志，因为启动时已设置
        println!("🐛 Debug mode enabled");
    }
    
    // 加载增强配置
    let config_path = std::env::var("CONFIG_PATH").unwrap_or_else(|_| "./config/neuroflow.toml".to_string());
    let config_manager = ConfigManager::new(config_path)?;
    
    // 获取当前配置
    let mut config = config_manager.get_config().await;
    
    // 从命令行参数覆盖配置
    config.server.port = args.http_port;
    config.grpc.port = args.grpc_port;
    config.observability.logs_level = args.log_level;
    
    info!("Enhanced configuration loaded: HTTP port={}, gRPC port={}", 
          config.server.port, config.grpc.port);
    
    // 初始化调试工具
    let mut debug_config = kernel::debug::DebugConfig::default();
    debug_config.verbose_logs = args.verbose;
    debug_config.profiling_enabled = args.debug;
    debug_config.memory_profiling = args.debug;
    debug_config.network_analysis = args.debug;
    
    let debug_tools = kernel::debug::DebugTools::new(debug_config);
    
    // 如果启用了调试模式，启动调试服务器
    if args.debug {
        debug_tools.start_debug_server().await?;
        info!("Debug mode enabled");
        
        // 记录启动事件
        let mut metadata = std::collections::HashMap::new();
        metadata.insert("startup_type".to_string(), "debug_mode".to_string());
        debug_tools.session.log_event(tracing::Level::INFO, "NeuroFlow started in debug mode".to_string(), metadata).await;
    }
    
    // 启动gRPC服务器
    let grpc_addr = format!("0.0.0.0:{}", config.grpc.port).parse()?;
    let grpc_service = RuntimeServiceImpl::new();
    
    // 启动热更新引擎
    let hot_reload_config = HotReloadConfig::default();
    let mut hot_reload_engine = HotReloadEngine::new(hot_reload_config);
    hot_reload_engine.start().await?;
    
    // 启动HTTP和gRPC服务器
    let http_future = start_http_server(config.server.host.clone(), config.server.port);
    let grpc_future = start_grpc_server(grpc_addr, grpc_service);
    
    // 等待两个服务器完成
    tokio::select! {
        http_result = http_future => {
            info!("HTTP server stopped");
            http_result?;
        }
        grpc_result = grpc_future => {
            info!("gRPC server stopped");
            grpc_result?;
        }
    }
    
    Ok(())
}

