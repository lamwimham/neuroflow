pub mod a2a;
pub mod cli;
pub mod config;
pub mod debug;
// pub mod docs;  // 原有代码错误，待修复
pub mod gateway;
// pub mod grpc;  // 暂时注释，需要 protoc
pub mod hot_reload;
pub mod memory;
pub mod mcp;
pub mod middleware;
pub mod observability;
pub mod proto;
pub mod routing;
pub mod runtime;
pub mod sandbox;
pub mod security;
pub mod skills;
pub mod testing;
pub mod tool_router;  // NEW: 统一工具路由层
pub mod utils;

// 重新导出常用的类型
pub use utils::{NeuroFlowError, Result};

// 重新导出工具路由相关类型
pub use tool_router::{
    ToolCall,
    ToolResult,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolRegistry,
};