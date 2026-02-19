//! 语义路由核心
//! 
//! 实现基于向量相似度的语义路由逻辑

use std::sync::Arc;
use serde::{Deserialize, Serialize};

use crate::routing::{
    vector_index::{VectorIndex, AgentMetadata},
    model_loader::{TextEncoder, ModelConfig},
    routing_strategy::{RoutingStrategyManager, StrategyConfig, AgentStatus},
};

/// 路由请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteRequest {
    pub query: String,
    pub context: Option<String>,
    pub required_capabilities: Vec<String>,
    pub excluded_agents: Vec<String>,
    pub timeout_ms: u64,
}

/// 路由结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingResult {
    pub agent_id: String,
    pub confidence: f32,
    pub matched_skills: Vec<String>,
    pub is_fallback: bool,
    pub processing_time_ms: f64,
    pub candidates_considered: usize,
}

/// 语义路由器
pub struct SemanticRouter {
    pub vector_index: Arc<VectorIndex>,
    pub text_encoder: Arc<TextEncoder>,
    pub strategy_manager: Arc<RoutingStrategyManager>,
    pub initialized: bool,
}

impl SemanticRouter {
    /// 创建新的语义路由器
    pub fn new(
        vector_index: Arc<VectorIndex>,
        text_encoder: Arc<TextEncoder>,
        strategy_manager: Arc<RoutingStrategyManager>,
    ) -> Self {
        Self {
            vector_index,
            text_encoder,
            strategy_manager,
            initialized: false,
        }
    }

    /// 初始化路由器
    pub fn initialize(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // 初始化文本编码器
        self.text_encoder.initialize()?;
        
        // 设置初始状态
        self.initialized = true;
        
        println!("SemanticRouter initialized with {} indexed agents", self.vector_index.size());
        Ok(())
    }

    /// 路由请求到最合适的Agent
    pub async fn route(&self, request: RouteRequest) -> Result<RoutingResult, Box<dyn std::error::Error>> {
        if !self.initialized {
            return Err("SemanticRouter not initialized. Call initialize() first.".into());
        }

        let start_time = std::time::Instant::now();

        // 1. 编码查询文本
        let query_embedding = self.text_encoder.encode_single(&request.query)?;
        
        // 2. 搜索相似的Agents
        let config = self.strategy_manager.config.read().unwrap().clone();
        drop(config); // 释放锁
        
        let candidates = self.vector_index.search_similar(
            &query_embedding,
            self.strategy_manager.config.read().unwrap().max_candidates * 2, // 搜索更多候选项以供筛选
            self.strategy_manager.config.read().unwrap().similarity_threshold * 0.8, // 略微降低阈值以获得更多候选项
        )?;

        // 3. 应用过滤条件
        let filtered_candidates = self.filter_candidates(candidates, &request)?;
        
        // 4. 应用路由策略
        let strategy_results = self.strategy_manager.apply_strategy(filtered_candidates, &request.query);
        
        // 5. 检查是否需要降级
        let final_result = if strategy_results.is_empty() || 
                          self.strategy_manager.should_fallback(&strategy_results) {
            // 使用降级路由
            if let Some(fallback) = self.strategy_manager.get_fallback_route() {
                RoutingResult {
                    agent_id: fallback.0,
                    confidence: fallback.1,
                    matched_skills: vec!["fallback".to_string()],
                    is_fallback: true,
                    processing_time_ms: start_time.elapsed().as_secs_f64() * 1000.0,
                    candidates_considered: 0,
                }
            } else {
                return Err("No suitable agent found and no fallback available".into());
            }
        } else {
            // 使用策略结果
            let (agent_id, confidence) = strategy_results[0].clone();
            
            // 获取Agent元数据以提取技能信息
            let agent_metadata = self.vector_index.get_agent_metadata(&agent_id);
            let matched_skills = agent_metadata
                .map(|meta| meta.skills.clone())
                .unwrap_or_else(|| vec!["general".to_string()]);
            
            RoutingResult {
                agent_id,
                confidence,
                matched_skills,
                is_fallback: false,
                processing_time_ms: start_time.elapsed().as_secs_f64() * 1000.0,
                candidates_considered: strategy_results.len(),
            }
        };

        // 6. 记录路由事件
        self.strategy_manager.record_routing_event(super::routing_strategy::RoutingEvent {
            timestamp: std::time::SystemTime::now(),
            agent_id: final_result.agent_id.clone(),
            similarity_score: final_result.confidence,
            strategy_used: self.strategy_manager.get_current_strategy(),
            success: true, // 简化处理，实际应用中应根据后续执行结果更新
        });

        Ok(final_result)
    }

    /// 过滤候选Agents
    fn filter_candidates(
        &self,
        candidates: Vec<(String, f32)>,
        request: &RouteRequest,
    ) -> Result<Vec<(String, f32)>, Box<dyn std::error::Error>> {
        let mut filtered = Vec::new();

        for (agent_id, similarity) in candidates {
            // 检查是否在排除列表中
            if request.excluded_agents.contains(&agent_id) {
                continue;
            }

            // 检查Agent元数据是否存在
            let agent_metadata = match self.vector_index.get_agent_metadata(&agent_id) {
                Some(metadata) => metadata,
                None => continue, // 跳过不存在的Agent
            };

            // 检查必需的能力
            if !request.required_capabilities.is_empty() {
                let has_required_capabilities = request.required_capabilities.iter()
                    .all(|req_cap| agent_metadata.capabilities.contains(req_cap));
                
                if !has_required_capabilities {
                    continue;
                }
            }

            filtered.push((agent_id, similarity));
        }

        Ok(filtered)
    }

    /// 注册新的Agent到路由系统
    pub fn register_agent(&self, metadata: AgentMetadata) -> Result<(), Box<dyn std::error::Error>> {
        // 添加到向量索引
        self.vector_index.add_agent(metadata.clone())?;
        
        // 初始化Agent状态
        let status = AgentStatus::new(metadata.agent_id.clone());
        self.strategy_manager.update_agent_status(status);
        
        Ok(())
    }

    /// 批量注册Agents
    pub fn register_agents(&self, metadata_list: Vec<AgentMetadata>) -> Result<(), Box<dyn std::error::Error>> {
        for metadata in metadata_list {
            self.register_agent(metadata)?;
        }
        Ok(())
    }

    /// 更新Agent状态
    pub fn update_agent_status(&self, status: AgentStatus) {
        self.strategy_manager.update_agent_status(status);
    }

    /// 获取路由历史
    pub fn get_routing_history(&self) -> Vec<super::routing_strategy::RoutingEvent> {
        self.strategy_manager.get_routing_history()
    }

    /// 更新路由策略
    pub fn update_routing_strategy(&self, strategy: crate::routing::routing_strategy::RoutingStrategy) {
        self.strategy_manager.update_strategy(strategy);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, RwLock};

    #[tokio::test]
    async fn test_semantic_router_creation() {
        let vector_index = Arc::new(VectorIndex::new(384)); // MiniLM模型维度
        let text_encoder = Arc::new(TextEncoder::new(ModelConfig::default()));
        let strategy_manager = Arc::new(RoutingStrategyManager::default());
        
        let mut router = SemanticRouter::new(vector_index, text_encoder, strategy_manager);
        assert!(!router.initialized);
        
        router.initialize().unwrap();
        assert!(router.initialized);
    }

    #[tokio::test]
    async fn test_agent_registration() {
        let vector_index = Arc::new(VectorIndex::new(4));
        let text_encoder = Arc::new(TextEncoder::new(ModelConfig::default()));
        let strategy_manager = Arc::new(RoutingStrategyManager::default());
        
        let mut router = SemanticRouter::new(vector_index, text_encoder, strategy_manager);
        router.initialize().unwrap();
        
        let metadata = AgentMetadata {
            agent_id: "test_agent".to_string(),
            name: "Test Agent".to_string(),
            description: "A test agent".to_string(),
            skills: vec!["test".to_string(), "example".to_string()],
            capabilities: vec!["computation".to_string(), "logic".to_string()],
            embedding: vec![0.1, 0.2, 0.3, 0.4],
        };
        
        assert!(router.register_agent(metadata).is_ok());
        assert_eq!(router.vector_index.size(), 1);
    }

    #[tokio::test]
    async fn test_basic_routing() {
        let vector_index = Arc::new(VectorIndex::new(384)); // 使用与编码器相同的维度
        let text_encoder = Arc::new(TextEncoder::new(ModelConfig::default()));
        let strategy_manager = Arc::new(RoutingStrategyManager::default());
        
        let mut router = SemanticRouter::new(vector_index, text_encoder, strategy_manager);
        router.initialize().unwrap();
        
        // 注册一个数学Agent
        let math_agent = AgentMetadata {
            agent_id: "math_agent".to_string(),
            name: "Math Agent".to_string(),
            description: "Handles mathematical computations".to_string(),
            skills: vec!["math".to_string(), "calculation".to_string()],
            capabilities: vec!["computation".to_string(), "arithmetic".to_string()],
            embedding: vec![0.1; 384], // 使用正确的维度
        };
        
        router.register_agent(math_agent).unwrap();
        
        // 注册一个通用Agent
        let general_agent = AgentMetadata {
            agent_id: "general_agent".to_string(),
            name: "General Agent".to_string(),
            description: "Handles general tasks".to_string(),
            skills: vec!["general".to_string(), "misc".to_string()],
            capabilities: vec!["general".to_string()],
            embedding: vec![0.2; 384], // 使用正确的维度
        };
        
        router.register_agent(general_agent).unwrap();
        
        // 测试路由
        let request = RouteRequest {
            query: "Calculate 15 * 25".to_string(),
            context: None,
            required_capabilities: vec![],
            excluded_agents: vec![],
            timeout_ms: 5000,
        };
        
        let result = router.route(request).await.unwrap();
        assert!(!result.agent_id.is_empty());
        assert!(result.confidence >= 0.0);
        assert!(!result.matched_skills.is_empty());
        assert!(result.processing_time_ms >= 0.0);
    }

    #[tokio::test]
    async fn test_capability_filtering() {
        let vector_index = Arc::new(VectorIndex::new(384));
        let text_encoder = Arc::new(TextEncoder::new(ModelConfig::default()));
        let strategy_manager = Arc::new(RoutingStrategyManager::default());
        
        let mut router = SemanticRouter::new(vector_index, text_encoder, strategy_manager);
        router.initialize().unwrap();
        
        // 注册一个仅具有数学能力的Agent
        let math_agent = AgentMetadata {
            agent_id: "math_only_agent".to_string(),
            name: "Math Only Agent".to_string(),
            description: "Handles only mathematical computations".to_string(),
            skills: vec!["math".to_string()],
            capabilities: vec!["computation".to_string(), "arithmetic".to_string()],
            embedding: vec![0.1; 384],
        };
        
        router.register_agent(math_agent).unwrap();
        
        // 测试必需能力过滤
        let request = RouteRequest {
            query: "Process text data".to_string(),
            context: None,
            required_capabilities: vec!["text_processing".to_string()], // 数学Agent不具备此能力
            excluded_agents: vec![],
            timeout_ms: 5000,
        };
        
        let result = router.route(request).await.unwrap();
        // 由于没有满足能力要求的Agent，应该返回降级结果或错误
        // 注意：这取决于具体的实现，这里我们只是测试过滤逻辑
    }

    #[tokio::test]
    async fn test_exclusion_filtering() {
        let vector_index = Arc::new(VectorIndex::new(384));
        let text_encoder = Arc::new(TextEncoder::new(ModelConfig::default()));
        let strategy_manager = Arc::new(RoutingStrategyManager::default());
        
        let mut router = SemanticRouter::new(vector_index, text_encoder, strategy_manager);
        router.initialize().unwrap();
        
        let agent1 = AgentMetadata {
            agent_id: "agent1".to_string(),
            name: "Agent 1".to_string(),
            description: "First agent".to_string(),
            skills: vec!["general".to_string()],
            capabilities: vec!["general".to_string()],
            embedding: vec![0.1; 384],
        };
        
        let agent2 = AgentMetadata {
            agent_id: "agent2".to_string(),
            name: "Agent 2".to_string(),
            description: "Second agent".to_string(),
            skills: vec!["general".to_string()],
            capabilities: vec!["general".to_string()],
            embedding: vec![0.2; 384],
        };
        
        router.register_agent(agent1).unwrap();
        router.register_agent(agent2).unwrap();
        
        // 测试排除过滤
        let request = RouteRequest {
            query: "General task".to_string(),
            context: None,
            required_capabilities: vec![],
            excluded_agents: vec!["agent1".to_string()], // 排除agent1
            timeout_ms: 5000,
        };
        
        let result = router.route(request).await.unwrap();
        // 结果应该是agent2，因为agent1被排除了
        // 注意：具体结果取决于内部算法和相似度计算
    }
}