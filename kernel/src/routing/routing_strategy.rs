//! 路由策略管理
//! 
//! 定义不同的路由决策策略和降级机制

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use serde::{Deserialize, Serialize};

/// 路由策略类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RoutingStrategy {
    /// 最佳匹配：返回相似度最高的单一Agent
    BestMatch,
    /// 多候选：返回多个相似度较高的Agents
    MultiCandidate,
    /// 负载均衡：在相似度相近的Agents中选择负载最低的
    LoadBalanced,
    /// 权重路由：基于Agent权重和相似度的综合评分
    Weighted,
    /// 专家路由：优先选择在特定领域有专长的Agent
    ExpertiseBased,
}

/// Agent权重配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentWeights {
    pub response_time_weight: f32,
    pub success_rate_weight: f32,
    pub capacity_weight: f32,
    pub expertise_score: f32,
}

impl Default for AgentWeights {
    fn default() -> Self {
        Self {
            response_time_weight: 0.3,
            success_rate_weight: 0.3,
            capacity_weight: 0.2,
            expertise_score: 0.2,
        }
    }
}

/// 路由策略配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyConfig {
    pub strategy: RoutingStrategy,
    pub similarity_threshold: f32,
    pub max_candidates: usize,
    pub fallback_enabled: bool,
    pub weights: AgentWeights,
    pub load_balancing_window: usize, // 负载均衡窗口大小
}

impl Default for StrategyConfig {
    fn default() -> Self {
        Self {
            strategy: RoutingStrategy::BestMatch,
            similarity_threshold: 0.7,
            max_candidates: 3,
            fallback_enabled: true,
            weights: AgentWeights::default(),
            load_balancing_window: 10,
        }
    }
}

/// Agent状态信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentStatus {
    pub agent_id: String,
    pub success_rate: f32,
    pub average_response_time: f64, // 毫秒
    pub current_load: usize,
    pub max_capacity: usize,
    pub last_active: std::time::SystemTime,
    pub error_count: u64,
}

impl AgentStatus {
    pub fn new(agent_id: String) -> Self {
        Self {
            agent_id,
            success_rate: 1.0,
            average_response_time: 100.0,
            current_load: 0,
            max_capacity: 10,
            last_active: std::time::SystemTime::now(),
            error_count: 0,
        }
    }

    /// 计算可用容量
    pub fn available_capacity(&self) -> usize {
        self.max_capacity.saturating_sub(self.current_load)
    }

    /// 检查是否过载
    pub fn is_overloaded(&self) -> bool {
        self.current_load >= self.max_capacity
    }

    /// 检查Agent是否活跃
    pub fn is_active(&self) -> bool {
        self.last_active.elapsed().map(|d| d.as_secs() < 300).unwrap_or(false) // 5分钟内活跃
    }
}

/// 路由策略管理器
pub struct RoutingStrategyManager {
    pub config: Arc<RwLock<StrategyConfig>>,
    pub agent_statuses: Arc<RwLock<HashMap<String, AgentStatus>>>,
    pub strategy_history: Arc<RwLock<Vec<RoutingEvent>>>,
}

/// 路由事件
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingEvent {
    pub timestamp: std::time::SystemTime,
    pub agent_id: String,
    pub similarity_score: f32,
    pub strategy_used: RoutingStrategy,
    pub success: bool,
}

impl RoutingStrategyManager {
    /// 创建新的路由策略管理器
    pub fn new(config: StrategyConfig) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
            agent_statuses: Arc::new(RwLock::new(HashMap::new())),
            strategy_history: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// 更新Agent状态
    pub fn update_agent_status(&self, status: AgentStatus) {
        let mut statuses = self.agent_statuses.write().unwrap();
        statuses.insert(status.agent_id.clone(), status);
    }

    /// 获取Agent状态
    pub fn get_agent_status(&self, agent_id: &str) -> Option<AgentStatus> {
        let statuses = self.agent_statuses.read().unwrap();
        statuses.get(agent_id).cloned()
    }

    /// 更新路由策略
    pub fn update_strategy(&self, new_strategy: RoutingStrategy) {
        let mut config = self.config.write().unwrap();
        config.strategy = new_strategy;
    }

    /// 获取当前策略
    pub fn get_current_strategy(&self) -> RoutingStrategy {
        let config = self.config.read().unwrap();
        config.strategy.clone()
    }

    /// 应用路由策略
    pub fn apply_strategy(
        &self,
        candidates: Vec<(String, f32)>, // (agent_id, similarity_score)
        query: &str,
    ) -> Vec<(String, f32)> {
        let config = self.config.read().unwrap();
        
        match &config.strategy {
            RoutingStrategy::BestMatch => {
                // 返回相似度最高的一个
                if candidates.is_empty() {
                    return Vec::new();
                }
                
                let best = candidates.into_iter()
                    .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
                    .unwrap();
                
                vec![best]
            },
            RoutingStrategy::MultiCandidate => {
                // 返回最多max_candidates个候选
                let mut sorted_candidates = candidates;
                sorted_candidates.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                sorted_candidates.truncate(config.max_candidates);
                sorted_candidates
            },
            RoutingStrategy::LoadBalanced => {
                // 在相似度阈值以上的Agent中选择负载最低的
                let filtered = candidates.into_iter()
                    .filter(|(_, sim)| *sim >= config.similarity_threshold)
                    .collect::<Vec<_>>();
                
                if filtered.is_empty() {
                    return Vec::new();
                }
                
                // 按照负载均衡策略选择
                let statuses = self.agent_statuses.read().unwrap();
                let mut scored_candidates = Vec::new();
                
                for (agent_id, similarity) in filtered {
                    let status = match statuses.get(&agent_id) {
                        Some(s) => s.clone(),
                        None => AgentStatus::new(agent_id.clone()),
                    };
                    
                    // 计算负载分数（负载越低分数越高）
                    let load_score = if status.max_capacity == 0 {
                        0.0
                    } else {
                        (status.available_capacity() as f32) / (status.max_capacity as f32)
                    };
                    
                    // 综合分数 = 相似度 * 0.7 + 负载分数 * 0.3
                    let composite_score = similarity * 0.7 + load_score * 0.3;
                    scored_candidates.push((agent_id, composite_score));
                }
                
                // 排序并返回最高分的
                scored_candidates.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                scored_candidates.truncate(config.max_candidates);
                
                // 将复合分数转换回相似度分数（仅用于兼容性）
                scored_candidates.into_iter()
                    .map(|(id, _)| (id, config.similarity_threshold))
                    .collect()
            },
            RoutingStrategy::Weighted => {
                // 基于权重的综合评分
                let statuses = self.agent_statuses.read().unwrap();
                let weights = &config.weights;
                
                let mut scored_candidates = Vec::new();
                
                for (agent_id, similarity) in candidates {
                    let status = match statuses.get(&agent_id) {
                        Some(s) => s.clone(),
                        None => AgentStatus::new(agent_id.clone()),
                    };
                    
                    // 计算综合评分
                    let response_time_score = 1.0 / (1.0 + (status.average_response_time / 1000.0) as f32);
                    let success_rate_score = status.success_rate;
                    let capacity_score = if status.max_capacity == 0 {
                        0.0
                    } else {
                        (status.available_capacity() as f32) / (status.max_capacity as f32)
                    };
                    
                    let composite_score = 
                        similarity * 0.4 +
                        response_time_score * weights.response_time_weight * 0.4 +
                        success_rate_score * weights.success_rate_weight * 0.4 +
                        capacity_score * weights.capacity_weight * 0.4 +
                        weights.expertise_score * 0.4;
                    
                    scored_candidates.push((agent_id, composite_score));
                }
                
                scored_candidates.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                scored_candidates.truncate(config.max_candidates);
                
                // 将复合分数转换回相似度分数（仅用于兼容性）
                scored_candidates.into_iter()
                    .map(|(id, _)| (id, config.similarity_threshold))
                    .collect()
            },
            RoutingStrategy::ExpertiseBased => {
                // 专家路由：基于特定领域的专长
                // 这里简化实现，实际上需要更复杂的领域匹配逻辑
                let mut sorted_candidates = candidates;
                sorted_candidates.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                sorted_candidates.truncate(config.max_candidates);
                sorted_candidates
            },
        }
    }

    /// 处理路由事件
    pub fn record_routing_event(&self, event: RoutingEvent) {
        let mut history = self.strategy_history.write().unwrap();
        history.push(event);
        
        // 限制历史记录大小
        if history.len() > 1000 {
            history.drain(0..100);
        }
    }

    /// 获取路由历史
    pub fn get_routing_history(&self) -> Vec<RoutingEvent> {
        let history = self.strategy_history.read().unwrap();
        history.clone()
    }

    /// 检查是否需要降级
    pub fn should_fallback(&self, candidates: &[(String, f32)]) -> bool {
        let config = self.config.read().unwrap();
        
        if !config.fallback_enabled {
            return false;
        }
        
        // 如果没有足够的候选或相似度都很低，则启用降级
        candidates.is_empty() || 
        candidates.iter().all(|(_, sim)| *sim < config.similarity_threshold * 0.5)
    }

    /// 获取降级路由结果
    pub fn get_fallback_route(&self) -> Option<(String, f32)> {
        let statuses = self.agent_statuses.read().unwrap();
        
        // 返回一个通用的fallback agent，如果没有则返回None
        // 在实际实现中，这里可能会返回一个专门的fallback agent
        statuses.iter()
            .find(|(_, status)| !status.is_overloaded() && status.is_active())
            .map(|(id, _)| (id.clone(), 0.5)) // 降级路由的默认相似度
    }
}

impl Default for RoutingStrategyManager {
    fn default() -> Self {
        Self::new(StrategyConfig::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_best_match_strategy() {
        let manager = RoutingStrategyManager::new(StrategyConfig {
            strategy: RoutingStrategy::BestMatch,
            ..Default::default()
        });

        let candidates = vec![
            ("agent1".to_string(), 0.8),
            ("agent2".to_string(), 0.9),
            ("agent3".to_string(), 0.7),
        ];

        let result = manager.apply_strategy(candidates, "test query");
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].0, "agent2");
        assert_eq!(result[0].1, 0.9);
    }

    #[test]
    fn test_multi_candidate_strategy() {
        let mut config = StrategyConfig::default();
        config.strategy = RoutingStrategy::MultiCandidate;
        config.max_candidates = 2;
        
        let manager = RoutingStrategyManager::new(config);

        let candidates = vec![
            ("agent1".to_string(), 0.8),
            ("agent2".to_string(), 0.9),
            ("agent3".to_string(), 0.7),
        ];

        let result = manager.apply_strategy(candidates, "test query");
        assert_eq!(result.len(), 2);
        assert_eq!(result[0].0, "agent2"); // 最高的
        assert_eq!(result[1].0, "agent1"); // 第二高的
    }

    #[test]
    fn test_agent_status_management() {
        let manager = RoutingStrategyManager::default();
        
        let status = AgentStatus {
            agent_id: "test_agent".to_string(),
            success_rate: 0.95,
            average_response_time: 200.0,
            current_load: 5,
            max_capacity: 10,
            last_active: std::time::SystemTime::now(),
            error_count: 1,
        };
        
        manager.update_agent_status(status);
        
        let retrieved = manager.get_agent_status("test_agent").unwrap();
        assert_eq!(retrieved.success_rate, 0.95);
        assert_eq!(retrieved.current_load, 5);
    }

    #[test]
    fn test_strategy_switching() {
        let manager = RoutingStrategyManager::default();
        
        assert_eq!(manager.get_current_strategy(), RoutingStrategy::BestMatch);
        
        manager.update_strategy(RoutingStrategy::MultiCandidate);
        assert_eq!(manager.get_current_strategy(), RoutingStrategy::MultiCandidate);
    }

    #[test]
    fn test_fallback_logic() {
        let manager = RoutingStrategyManager::default();
        
        // 测试空候选列表触发降级
        let empty_candidates: Vec<(String, f32)> = vec![];
        assert!(manager.should_fallback(&empty_candidates));
        
        // 测试低相似度触发降级
        let low_similarity_candidates = vec![("agent1".to_string(), 0.1)];
        assert!(manager.should_fallback(&low_similarity_candidates));
        
        // 测试高相似度不触发降级
        let high_similarity_candidates = vec![("agent1".to_string(), 0.9)];
        assert!(!manager.should_fallback(&high_similarity_candidates));
    }
}