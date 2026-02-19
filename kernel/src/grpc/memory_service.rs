/// NeuroFlow Kernel - Memory gRPC Service (Simplified)
/// 
/// 简化版本，不依赖 proto 编译

use std::sync::Arc;
use tracing::info;

use crate::memory::MemoryManager;
use crate::knowledge::{KnowledgeExtractor, ConversationAnalyzer};
use crate::mcp::MCPService;

/// Memory gRPC 服务实现（占位符）
pub struct MemoryGrpcService {
    _memory_manager: Arc<MemoryManager>,
}

impl MemoryGrpcService {
    pub fn new(memory_manager: Arc<MemoryManager>) -> Self {
        Self {
            _memory_manager: memory_manager,
        }
    }
}

/// 对话记忆服务实现（占位符）
pub struct ConversationMemoryGrpcService {
    memory_manager: Arc<MemoryManager>,
    knowledge_extractor: Arc<KnowledgeExtractor>,
    _conversation_analyzer: Arc<ConversationAnalyzer>,
}

impl ConversationMemoryGrpcService {
    pub fn new(memory_manager: Arc<MemoryManager>, mcp_service: Arc<MCPService>) -> Self {
        let extractor = Arc::new(KnowledgeExtractor::new(
            memory_manager.clone(),
            mcp_service,
        ));
        
        Self {
            memory_manager,
            knowledge_extractor: extractor.clone(),
            _conversation_analyzer: Arc::new(ConversationAnalyzer::new(extractor)),
        }
    }
    
    /// 获取 knowledge extractor
    pub fn extractor(&self) -> Arc<KnowledgeExtractor> {
        self.knowledge_extractor.clone()
    }
}
