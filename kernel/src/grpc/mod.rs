/// NeuroFlow Kernel - gRPC Module
/// 
/// 简化版本，使用 HTTP over Actix-web

pub mod memory_http_service;
pub mod memory_service;

pub use memory_http_service::{MemoryService, configure_memory_routes};
pub use memory_service::{MemoryGrpcService, ConversationMemoryGrpcService};
