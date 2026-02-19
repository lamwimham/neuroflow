/// NeuroFlow Kernel Library
/// 
/// 简化版本，专注于 Memory 和 Knowledge 功能

pub mod memory;
pub mod knowledge;
pub mod mcp;
pub mod grpc;
pub mod utils;

// 重新导出常用类型
pub use memory::{MemoryManager, MemoryEntry, MemoryConfig};
pub use knowledge::{KnowledgeExtractor, ConversationAnalyzer, KnowledgeCategory};
pub use grpc::{MemoryService, configure_memory_routes};
