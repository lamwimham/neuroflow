use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, Mutex};
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use ndarray::Array2;

use crate::utils::Result;
use crate::memory::{MemoryManager, MemoryEntry, MemoryType};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub parameters: Vec<SkillParameter>,
    pub return_type: String,
    pub implementation: SkillImplementation,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: String,
    pub tags: Vec<String>,
    pub complexity: u32, // 1-10, 表示技能复杂度
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillParameter {
    pub name: String,
    pub parameter_type: String,
    pub description: String,
    pub required: bool,
    pub default_value: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SkillImplementation {
    /// 本地Rust函数
    Native { function_name: String },
    /// WASM模块
    Wasm { module_id: String },
    /// Python脚本
    Python { script_path: String },
    /// 由AI生成的动态技能
    Dynamic { code: String, language: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillExecutionResult {
    pub success: bool,
    pub output: serde_json::Value,
    pub execution_time_ms: u64,
    pub tokens_used: Option<TokensUsed>,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokensUsed {
    pub input_tokens: u32,
    pub output_tokens: u32,
    pub cache_read_tokens: u32,
    pub cache_write_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillMetadata {
    pub usage_count: u64,
    pub success_rate: f64,
    pub avg_execution_time_ms: f64,
    pub last_used: Option<DateTime<Utc>>,
    pub learned_from_examples: Vec<SkillExample>,
    pub performance_history: Vec<SkillPerformanceRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillExample {
    pub input: serde_json::Value,
    pub expected_output: serde_json::Value,
    pub context: serde_json::Value,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillPerformanceRecord {
    pub timestamp: DateTime<Utc>,
    pub execution_time_ms: u64,
    pub success: bool,
    pub tokens_used: Option<TokensUsed>,
}

#[derive(Debug, Clone)]
pub struct SkillConfig {
    pub max_dynamic_skills: usize,
    pub skill_cache_ttl_seconds: u64,
    pub learning_enabled: bool,
    pub auto_optimization_enabled: bool,
    pub performance_tracking: bool,
}

impl Default for SkillConfig {
    fn default() -> Self {
        Self {
            max_dynamic_skills: 100,
            skill_cache_ttl_seconds: 3600, // 1小时
            learning_enabled: true,
            auto_optimization_enabled: true,
            performance_tracking: true,
        }
    }
}

pub trait SkillExecutor: Send + Sync {
    async fn execute(&self, skill_id: &str, params: serde_json::Value) -> Result<SkillExecutionResult>;
    async fn validate_params(&self, skill_id: &str, params: &serde_json::Value) -> Result<()>;
}

pub struct SkillRegistry {
    skills: Arc<RwLock<HashMap<String, SkillDefinition>>>,
    metadata: Arc<RwLock<HashMap<String, SkillMetadata>>>,
    executor: Arc<dyn SkillExecutor>,
    memory_manager: Arc<MemoryManager>,
    config: SkillConfig,
    learning_processor: Arc<SkillLearningProcessor>,
}

impl SkillRegistry {
    pub fn new(
        executor: Arc<dyn SkillExecutor>,
        memory_manager: Arc<MemoryManager>,
        config: SkillConfig,
    ) -> Self {
        let registry = Self {
            skills: Arc::new(RwLock::new(HashMap::new())),
            metadata: Arc::new(RwLock::new(HashMap::new())),
            executor,
            memory_manager,
            config,
            learning_processor: Arc::new(SkillLearningProcessor::new()),
        };

        // 初始化内置技能
        registry.initialize_builtin_skills();

        registry
    }

    fn initialize_builtin_skills(&self) {
        // 添加一些内置技能定义
        let builtin_skills = vec![
            SkillDefinition {
                id: "builtin:text_analyzer".to_string(),
                name: "text_analyzer".to_string(),
                description: "文本分析技能".to_string(),
                parameters: vec![
                    SkillParameter {
                        name: "text".to_string(),
                        parameter_type: "string".to_string(),
                        description: "待分析的文本".to_string(),
                        required: true,
                        default_value: None,
                    },
                    SkillParameter {
                        name: "analysis_type".to_string(),
                        parameter_type: "string".to_string(),
                        description: "分析类型".to_string(),
                        required: false,
                        default_value: Some(serde_json::Value::String("sentiment".to_string())),
                    }
                ],
                return_type: "object".to_string(),
                implementation: SkillImplementation::Native { 
                    function_name: "analyze_text".to_string() 
                },
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                tags: vec!["text".to_string(), "analysis".to_string()],
                complexity: 3,
            },
            SkillDefinition {
                id: "builtin:calculator".to_string(),
                name: "calculator".to_string(),
                description: "计算器技能".to_string(),
                parameters: vec![
                    SkillParameter {
                        name: "expression".to_string(),
                        parameter_type: "string".to_string(),
                        description: "数学表达式".to_string(),
                        required: true,
                        default_value: None,
                    }
                ],
                return_type: "number".to_string(),
                implementation: SkillImplementation::Native { 
                    function_name: "calculate".to_string() 
                },
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                tags: vec!["math".to_string(), "calculation".to_string()],
                complexity: 2,
            }
        ];

        let mut skills = self.skills.blocking_write();
        for skill in builtin_skills {
            skills.insert(skill.id.clone(), skill);
        }

        // 初始化元数据
        let mut metadata = self.metadata.blocking_write();
        for skill_id in ["builtin:text_analyzer", "builtin:calculator"] {
            metadata.insert(
                skill_id.to_string(),
                SkillMetadata {
                    usage_count: 0,
                    success_rate: 0.0,
                    avg_execution_time_ms: 0.0,
                    last_used: None,
                    learned_from_examples: vec![],
                    performance_history: vec![],
                },
            );
        }
    }

    pub async fn register_skill(&self, mut skill: SkillDefinition) -> Result<()> {
        // 验证技能定义
        self.validate_skill_definition(&skill)?;

        // 设置时间戳
        let now = Utc::now();
        skill.created_at = now;
        skill.updated_at = now;

        let mut skills = self.skills.write().await;
        skills.insert(skill.id.clone(), skill);

        // 初始化元数据
        let mut metadata = self.metadata.write().await;
        metadata.insert(
            skill.id.clone(),
            SkillMetadata {
                usage_count: 0,
                success_rate: 0.0,
                avg_execution_time_ms: 0.0,
                last_used: None,
                learned_from_examples: vec![],
                performance_history: vec![],
            },
        );

        info!("Registered skill: {}", skill.id);
        Ok(())
    }

    pub async fn execute_skill(&self, skill_id: &str, params: serde_json::Value) -> Result<SkillExecutionResult> {
        // 检查技能是否存在
        let skills = self.skills.read().await;
        let skill = skills.get(skill_id)
            .ok_or_else(|| crate::utils::NeuroFlowError::SkillNotFound(skill_id.to_string()))?
            .clone();
        drop(skills);

        // 验证参数
        self.executor.validate_params(skill_id, &params).await?;

        // 执行技能
        let start_time = std::time::Instant::now();
        let result = self.executor.execute(skill_id, params).await?;
        let execution_time = start_time.elapsed().as_millis() as u64;

        // 更新元数据
        self.update_skill_metadata(skill_id, &result, execution_time).await;

        Ok(result)
    }

    async fn update_skill_metadata(&self, skill_id: &str, result: &SkillExecutionResult, execution_time: u64) {
        let mut metadata = self.metadata.write().await;
        
        if let Some(meta) = metadata.get_mut(skill_id) {
            meta.usage_count += 1;
            meta.last_used = Some(Utc::now());
            
            // 更新成功率
            let total_runs = meta.usage_count;
            let successful_runs = (meta.success_rate * (total_runs as f64 - 1.0)).round() as u64 + 
                                  if result.success { 1 } else { 0 };
            meta.success_rate = successful_runs as f64 / total_runs as f64;
            
            // 更新平均执行时间
            meta.avg_execution_time_ms = ((meta.avg_execution_time_ms * (total_runs as f64 - 1.0)) + execution_time as f64) / total_runs as f64;
            
            // 记录性能历史
            meta.performance_history.push(SkillPerformanceRecord {
                timestamp: Utc::now(),
                execution_time_ms: execution_time,
                success: result.success,
                tokens_used: result.tokens_used.clone(),
            });
            
            // 保持性能历史记录在合理范围内
            if meta.performance_history.len() > 100 {
                meta.performance_history.drain(0..meta.performance_history.len()-100);
            }
        }
    }

    fn validate_skill_definition(&self, skill: &SkillDefinition) -> Result<()> {
        if skill.name.is_empty() {
            return Err(crate::utils::NeuroFlowError::InvalidInput("Skill name cannot be empty".to_string()));
        }

        if skill.description.is_empty() {
            return Err(crate::utils::NeuroFlowError::InvalidInput("Skill description cannot be empty".to_string()));
        }

        Ok(())
    }

    pub async fn get_skill(&self, skill_id: &str) -> Result<SkillDefinition> {
        let skills = self.skills.read().await;
        skills.get(skill_id)
            .cloned()
            .ok_or_else(|| crate::utils::NeuroFlowError::SkillNotFound(skill_id.to_string()))
    }

    pub async fn list_skills(&self, tags: Option<Vec<String>>) -> Result<Vec<SkillDefinition>> {
        let skills = self.skills.read().await;
        
        let filtered_skills: Vec<SkillDefinition> = if let Some(filter_tags) = tags {
            skills.values()
                .filter(|skill| {
                    skill.tags.iter().any(|tag| filter_tags.contains(tag))
                })
                .cloned()
                .collect()
        } else {
            skills.values().cloned().collect()
        };

        Ok(filtered_skills)
    }

    pub async fn get_skill_metadata(&self, skill_id: &str) -> Result<SkillMetadata> {
        let metadata = self.metadata.read().await;
        metadata.get(skill_id)
            .cloned()
            .ok_or_else(|| crate::utils::NeuroFlowError::SkillNotFound(skill_id.to_string()))
    }

    pub async fn learn_new_skill(&self, skill_description: &str, examples: Vec<SkillExample>) -> Result<String> {
        if !self.config.learning_enabled {
            return Err(crate::utils::NeuroFlowError::InvalidInput("Skill learning is disabled".to_string()));
        }

        // 使用学习处理器生成新技能
        let new_skill = self.learning_processor.learn_skill(
            skill_description,
            examples,
            Arc::clone(&self.memory_manager)
        ).await?;

        // 注册新技能
        let skill_id = new_skill.id.clone();
        self.register_skill(new_skill).await?;

        info!("Learned new skill: {}", skill_id);
        Ok(skill_id)
    }

    pub async fn optimize_skill(&self, skill_id: &str) -> Result<()> {
        if !self.config.auto_optimization_enabled {
            return Err(crate::utils::NeuroFlowError::InvalidInput("Skill optimization is disabled".to_string()));
        }

        // 获取技能和性能数据
        let skill = self.get_skill(skill_id).await?;
        let metadata = self.get_skill_metadata(skill_id).await?;

        // 根据性能数据优化技能
        self.learning_processor.optimize_skill(
            skill,
            metadata,
            Arc::clone(&self.memory_manager)
        ).await?;

        info!("Optimized skill: {}", skill_id);
        Ok(())
    }

    pub async fn get_recommended_skills(&self, context: &str, limit: usize) -> Result<Vec<SkillDefinition>> {
        // 基于上下文推荐最相关的技能
        let all_skills = self.list_skills(None).await?;
        
        // 使用语义相似度计算相关性
        let mut scored_skills = Vec::new();
        
        for skill in all_skills {
            let score = self.calculate_context_relevance(context, &skill).await?;
            scored_skills.push((skill, score));
        }
        
        // 按相关性排序
        scored_skills.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        
        // 返回前N个
        let recommended: Vec<SkillDefinition> = scored_skills
            .into_iter()
            .take(limit)
            .map(|(skill, _)| skill)
            .collect();
        
        Ok(recommended)
    }

    async fn calculate_context_relevance(&self, context: &str, skill: &SkillDefinition) -> Result<f64> {
        // 这里可以集成向量数据库进行语义匹配
        // 简化实现：基于关键词匹配
        let context_lower = context.to_lowercase();
        let mut score = 0.0;
        
        // 匹配技能名称
        if context_lower.contains(&skill.name.to_lowercase()) {
            score += 0.3;
        }
        
        // 匹配描述
        if context_lower.contains(&skill.description.to_lowercase()) {
            score += 0.4;
        }
        
        // 匹配标签
        for tag in &skill.tags {
            if context_lower.contains(&tag.to_lowercase()) {
                score += 0.2;
            }
        }
        
        Ok(score.min(1.0))
    }
}

pub struct SkillLearningProcessor;

impl SkillLearningProcessor {
    pub fn new() -> Self {
        Self
    }

    pub async fn learn_skill(
        &self,
        skill_description: &str,
        examples: Vec<SkillExample>,
        memory_manager: Arc<MemoryManager>,
    ) -> Result<SkillDefinition> {
        // 这里集成AI模型来生成新的技能实现
        // 简化实现：生成一个动态技能
        let skill_id = format!("learned:{}", Uuid::new_v4());
        
        // 分析示例来推断参数
        let mut parameters = Vec::new();
        if !examples.is_empty() {
            // 从第一个示例推断参数结构
            if let Some(first_example) = examples.first() {
                if let serde_json::Value::Object(obj) = &first_example.input {
                    for (key, value) in obj {
                        parameters.push(SkillParameter {
                            name: key.clone(),
                            parameter_type: self.infer_type(value),
                            description: format!("Parameter {}", key),
                            required: true,
                            default_value: None,
                        });
                    }
                }
            }
        }

        let skill = SkillDefinition {
            id: skill_id,
            name: format!("learned_skill_{}", Uuid::new_v4().to_string()[..8].to_string()),
            description: skill_description.to_string(),
            parameters,
            return_type: "object".to_string(),
            implementation: SkillImplementation::Dynamic {
                code: self.generate_skill_code(skill_description, &examples)?,
                language: "python".to_string(),
            },
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            tags: vec!["learned".to_string(), "dynamic".to_string()],
            complexity: 5, // 中等复杂度
        };

        // 存储学习示例到记忆中
        self.store_learning_examples(&skill.id, examples, Arc::clone(&memory_manager)).await?;

        Ok(skill)
    }

    fn infer_type(&self, value: &serde_json::Value) -> String {
        match value {
            serde_json::Value::String(_) => "string".to_string(),
            serde_json::Value::Number(_) => "number".to_string(),
            serde_json::Value::Bool(_) => "boolean".to_string(),
            serde_json::Value::Array(_) => "array".to_string(),
            serde_json::Value::Object(_) => "object".to_string(),
            serde_json::Value::Null => "null".to_string(),
        }
    }

    fn generate_skill_code(&self, description: &str, examples: &[SkillExample]) -> Result<String> {
        // 这里应该集成AI模型来生成实际代码
        // 简化实现：返回一个模板
        let code = format!(
            r#"
def execute_skill(params):
    """
    Generated skill for: {}
    Examples: {}
    """
    # Generated implementation based on examples
    # This would be replaced with actual AI-generated code
    result = {{}}
    for key, value in params.items():
        result[f"processed_{{key}}"] = str(value)
    return result
"#,
            description,
            examples.len()
        );

        Ok(code)
    }

    async fn store_learning_examples(
        &self,
        skill_id: &str,
        examples: Vec<SkillExample>,
        memory_manager: Arc<MemoryManager>,
    ) -> Result<()> {
        // 存储学习示例到记忆系统
        for (i, example) in examples.into_iter().enumerate() {
            let memory_key = format!("skill_{}_example_{}", skill_id, i);
            let memory_value = serde_json::json!({
                "input": example.input,
                "expected_output": example.expected_output,
                "context": example.context,
                "timestamp": example.timestamp
            });

            memory_manager.store(
                memory_key,
                memory_value,
                MemoryType::LONG_TERM,
                Some(vec!["skill_learning".to_string(), skill_id.to_string()]),
                0.8,  // 高重要性
                None,
            ).await;
        }

        Ok(())
    }

    pub async fn optimize_skill(
        &self,
        mut skill: SkillDefinition,
        metadata: SkillMetadata,
        memory_manager: Arc<MemoryManager>,
    ) -> Result<SkillDefinition> {
        // 基于性能数据优化技能
        if metadata.avg_execution_time_ms > 1000.0 {
            // 如果执行时间过长，考虑优化实现
            warn!("Skill {} has high execution time: {}ms", skill.id, metadata.avg_execution_time_ms);
            
            // 可以尝试不同的实现方式或优化算法
            // 这里只是示例，实际实现会更复杂
        }

        if metadata.success_rate < 0.8 {
            // 成功率低，可能需要修复或重新训练
            warn!("Skill {} has low success rate: {:.2}%", skill.id, metadata.success_rate * 100.0);
        }

        // 更新技能复杂度基于实际性能
        skill.complexity = self.estimate_complexity(&metadata);

        Ok(skill)
    }

    fn estimate_complexity(&self, metadata: &SkillMetadata) -> u32 {
        // 基于性能数据估计复杂度
        let mut complexity = 5; // 默认中等复杂度

        if metadata.avg_execution_time_ms > 2000.0 {
            complexity = 8; // 很慢，高复杂度
        } else if metadata.avg_execution_time_ms > 500.0 {
            complexity = 6; // 慢，较高复杂度
        } else if metadata.avg_execution_time_ms < 100.0 {
            complexity = 3; // 快，低复杂度
        }

        complexity.min(10).max(1) // 限制在1-10范围内
    }
}

// 简单的技能执行器实现
pub struct SimpleSkillExecutor {
    // 这里应该包含实际的技能执行逻辑
    // 如WASM运行时、Python解释器等
}

#[async_trait::async_trait]
impl SkillExecutor for SimpleSkillExecutor {
    async fn execute(&self, skill_id: &str, params: serde_json::Value) -> Result<SkillExecutionResult> {
        // 模拟执行
        debug!("Executing skill: {} with params: {:?}", skill_id, params);
        
        // 实际实现中会根据技能实现类型执行相应的代码
        let result = SkillExecutionResult {
            success: true,
            output: serde_json::json!({"result": "executed successfully"}),
            execution_time_ms: 100, // 模拟执行时间
            tokens_used: Some(TokensUsed {
                input_tokens: 10,
                output_tokens: 20,
                cache_read_tokens: 0,
                cache_write_tokens: 5,
            }),
            error_message: None,
        };

        Ok(result)
    }

    async fn validate_params(&self, skill_id: &str, params: &serde_json::Value) -> Result<()> {
        // 简单验证：确保params是对象
        if !params.is_object() {
            return Err(crate::utils::NeuroFlowError::InvalidInput(
                format!("Parameters for skill {} must be an object", skill_id)
            ));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_skill_registry() {
        let executor = Arc::new(SimpleSkillExecutor {});
        let memory_manager = Arc::new(MemoryManager::new(crate::memory::MemoryConfig::default()));
        let config = SkillConfig::default();
        let registry = SkillRegistry::new(executor, memory_manager, config);

        // 测试获取内置技能
        let skills = registry.list_skills(None).await.unwrap();
        assert!(!skills.is_empty());

        // 测试执行技能
        let result = registry.execute_skill("builtin:calculator", json!({
            "expression": "2+2"
        })).await;

        assert!(result.is_ok());
    }
}