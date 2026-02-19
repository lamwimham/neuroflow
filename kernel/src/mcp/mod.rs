use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, Semaphore};
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};
use uuid::Uuid;
use chrono::{DateTime, Utc};

use crate::utils::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelRequest {
    pub id: String,
    pub model_name: String,
    pub operation: ModelOperation,
    pub parameters: serde_json::Value,
    pub context: ModelContext,
    pub priority: RequestPriority,
    pub timeout_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ModelOperation {
    Embedding,
    Generation,
    Classification,
    Translation,
    Summarization,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelContext {
    pub conversation_id: Option<String>,
    pub user_id: Option<String>,
    pub session_id: Option<String>,
    pub metadata: HashMap<String, String>,
    pub previous_responses: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RequestPriority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4,
}

impl Default for RequestPriority {
    fn default() -> Self {
        RequestPriority::Normal
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelResponse {
    pub request_id: String,
    pub model_name: String,
    pub result: serde_json::Value,
    pub execution_time_ms: u64,
    pub tokens_used: Option<TokensUsed>,
    pub cached: bool,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokensUsed {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub version: String,
    pub provider: String,
    pub capabilities: Vec<ModelOperation>,
    pub max_tokens: u32,
    pub input_cost_per_token: f64,
    pub output_cost_per_token: f64,
    pub rate_limit: RateLimit,
    pub health_status: HealthStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimit {
    pub requests_per_minute: u32,
    pub tokens_per_minute: u32,
    pub concurrent_requests: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HealthStatus {
    Healthy,
    Degraded,
    Unhealthy,
    Maintenance,
}

#[derive(Debug, Clone)]
pub struct MCPConfig {
    pub max_concurrent_requests: usize,
    pub default_timeout_ms: u64,
    pub cache_enabled: bool,
    pub cache_ttl_seconds: u64,
    pub retry_attempts: u32,
    pub fallback_enabled: bool,
}

impl Default for MCPConfig {
    fn default() -> Self {
        Self {
            max_concurrent_requests: 100,
            default_timeout_ms: 30000, // 30秒
            cache_enabled: true,
            cache_ttl_seconds: 300, // 5分钟
            retry_attempts: 3,
            fallback_enabled: true,
        }
    }
}

pub trait ModelProvider: Send + Sync {
    async fn execute(&self, request: ModelRequest) -> Result<ModelResponse>;
    async fn get_model_info(&self) -> Result<ModelInfo>;
    async fn health_check(&self) -> Result<HealthStatus>;
    async fn get_rate_limits(&self) -> Result<RateLimit>;
}

pub struct MCPService {
    providers: Arc<RwLock<HashMap<String, Arc<dyn ModelProvider>>>>,
    config: MCPConfig,
    semaphore: Arc<Semaphore>,
    cache: Arc<RwLock<HashMap<String, CachedResponse>>>,
}

#[derive(Debug, Clone)]
struct CachedResponse {
    response: ModelResponse,
    expires_at: DateTime<Utc>,
}

impl MCPService {
    pub fn new(config: MCPConfig) -> Self {
        Self {
            providers: Arc::new(RwLock::new(HashMap::new())),
            config,
            semaphore: Arc::new(Semaphore::new(config.max_concurrent_requests)),
            cache: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn register_provider(&self, name: String, provider: Arc<dyn ModelProvider>) -> Result<()> {
        let mut providers = self.providers.write().await;
        providers.insert(name, provider);
        info!("Registered model provider: {}", name);
        Ok(())
    }

    pub async fn execute_request(&self, mut request: ModelRequest) -> Result<ModelResponse> {
        // 检查缓存
        if self.config.cache_enabled {
            if let Some(cached) = self.check_cache(&request).await {
                debug!("Cache hit for request: {}", request.id);
                return Ok(cached);
            }
        }

        // 应用默认超时
        if request.timeout_ms == 0 {
            request.timeout_ms = self.config.default_timeout_ms;
        }

        // 获取信号量许可（限制并发）
        let _permit = self.semaphore.acquire().await
            .map_err(|e| crate::utils::NeuroFlowError::InternalError(e.to_string()))?;

        // 选择最佳模型提供者
        let provider = self.select_best_provider(&request).await?;
        
        debug!("Executing request {} with provider", request.id);
        
        let start_time = std::time::Instant::now();
        let response = provider.execute(request.clone()).await?;
        let execution_time = start_time.elapsed().as_millis() as u64;

        // 添加执行时间到响应
        let final_response = ModelResponse {
            execution_time_ms: execution_time,
            ..response
        };

        // 缓存响应（如果是可缓存的请求）
        if self.config.cache_enabled && self.is_cacheable(&request) {
            self.cache_response(&request, &final_response).await;
        }

        Ok(final_response)
    }

    async fn check_cache(&self, request: &ModelRequest) -> Option<ModelResponse> {
        let cache = self.cache.read().await;
        let cache_key = self.generate_cache_key(request);

        if let Some(cached) = cache.get(&cache_key) {
            if cached.expires_at > Utc::now() {
                return Some(cached.response.clone());
            } else {
                // 缓存已过期，稍后清理
                drop(cache);
                self.purge_expired_cache().await;
            }
        }

        None
    }

    async fn cache_response(&self, request: &ModelRequest, response: &ModelResponse) {
        if !self.is_cacheable(request) {
            return;
        }

        let cache_key = self.generate_cache_key(request);
        let expires_at = Utc::now() + chrono::Duration::seconds(self.config.cache_ttl_seconds as i64);

        let mut cache = self.cache.write().await;
        cache.insert(cache_key, CachedResponse {
            response: response.clone(),
            expires_at,
        });

        debug!("Cached response for request: {}", request.id);
    }

    fn generate_cache_key(&self, request: &ModelRequest) -> String {
        // 为相同输入生成相同的缓存键
        let mut key_parts = vec![
            request.model_name.clone(),
            serde_json::to_string(&request.operation).unwrap_or_default(),
            serde_json::to_string(&request.parameters).unwrap_or_default(),
        ];

        if let Some(conversation_id) = &request.context.conversation_id {
            key_parts.push(conversation_id.clone());
        }

        // 使用简单哈希作为键
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        key_parts.join("|").hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }

    fn is_cacheable(&self, request: &ModelRequest) -> bool {
        // 某些操作不适合缓存
        match &request.operation {
            ModelOperation::Generation | ModelOperation::Custom(_) => false,
            _ => true,
        }
    }

    async fn select_best_provider(&self, request: &ModelRequest) -> Result<Arc<dyn ModelProvider>> {
        let providers = self.providers.read().await;
        
        // 查找支持请求操作的提供者
        let suitable_providers: Vec<_> = providers
            .iter()
            .filter(|(_, provider)| {
                // 这里可以实现更复杂的负载均衡和选择逻辑
                true
            })
            .collect();

        if suitable_providers.is_empty() {
            return Err(crate::utils::NeuroFlowError::ModelNotFound(
                format!("No provider found for model: {}", request.model_name)));
        }

        // 简单选择第一个合适的提供者（在实际实现中可以更复杂）
        let (_, provider) = suitable_providers[0];
        Ok(provider.clone())
    }

    async fn purge_expired_cache(&self) {
        let mut cache = self.cache.write().await;
        let now = Utc::now();
        
        cache.retain(|_, cached| cached.expires_at > now);
        
        debug!("Purged expired cache entries");
    }

    pub async fn get_model_info(&self, model_name: &str) -> Result<ModelInfo> {
        let providers = self.providers.read().await;
        
        for (name, provider) in providers.iter() {
            if name == model_name {
                return provider.get_model_info().await;
            }
        }

        Err(crate::utils::NeuroFlowError::ModelNotFound(
            format!("Model {} not found", model_name)))
    }

    pub async fn health_check_all(&self) -> Result<HashMap<String, HealthStatus>> {
        let providers = self.providers.read().await;
        let mut results = HashMap::new();

        for (name, provider) in providers.iter() {
            match provider.health_check().await {
                Ok(status) => {
                    results.insert(name.clone(), status);
                }
                Err(e) => {
                    error!("Health check failed for provider {}: {}", name, e);
                    results.insert(name.clone(), HealthStatus::Unhealthy);
                }
            }
        }

        Ok(results)
    }

    pub async fn execute_embedding(&self, texts: Vec<String>, model_name: &str) -> Result<Vec<Vec<f32>>> {
        let request = ModelRequest {
            id: Uuid::new_v4().to_string(),
            model_name: model_name.to_string(),
            operation: ModelOperation::Embedding,
            parameters: json!({ "texts": texts }),
            context: ModelContext {
                conversation_id: None,
                user_id: None,
                session_id: None,
                metadata: HashMap::new(),
                previous_responses: vec![],
            },
            priority: RequestPriority::Normal,
            timeout_ms: 0,
        };

        let response = self.execute_request(request).await?;
        
        // 解析嵌入向量
        let embeddings: Vec<Vec<f32>> = serde_json::from_value(response.result)
            .map_err(|e| crate::utils::NeuroFlowError::SerializationError(e.to_string()))?;

        Ok(embeddings)
    }

    pub async fn execute_generation(&self, prompt: String, model_name: &str, params: serde_json::Value) -> Result<String> {
        let request = ModelRequest {
            id: Uuid::new_v4().to_string(),
            model_name: model_name.to_string(),
            operation: ModelOperation::Generation,
            parameters: json!({ "prompt": prompt, "params": params }),
            context: ModelContext {
                conversation_id: None,
                user_id: None,
                session_id: None,
                metadata: HashMap::new(),
                previous_responses: vec![],
            },
            priority: RequestPriority::Normal,
            timeout_ms: 0,
        };

        let response = self.execute_request(request).await?;
        
        // 解析生成结果
        let result: String = serde_json::from_value(response.result)
            .map_err(|e| crate::utils::NeuroFlowError::SerializationError(e.to_string()))?;

        Ok(result)
    }
}

// 内置的模拟模型提供者，用于测试
pub struct MockModelProvider {
    info: ModelInfo,
}

impl MockModelProvider {
    pub fn new(model_name: &str) -> Self {
        Self {
            info: ModelInfo {
                name: model_name.to_string(),
                version: "1.0.0".to_string(),
                provider: "mock".to_string(),
                capabilities: vec![
                    ModelOperation::Embedding,
                    ModelOperation::Generation,
                    ModelOperation::Classification,
                ],
                max_tokens: 2048,
                input_cost_per_token: 0.0,
                output_cost_per_token: 0.0,
                rate_limit: RateLimit {
                    requests_per_minute: 1000,
                    tokens_per_minute: 100000,
                    concurrent_requests: 10,
                },
                health_status: HealthStatus::Healthy,
            },
        }
    }
}

#[async_trait::async_trait]
impl ModelProvider for MockModelProvider {
    async fn execute(&self, request: ModelRequest) -> Result<ModelResponse> {
        // 模拟处理时间
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

        let result = match request.operation {
            ModelOperation::Embedding => {
                // 生成模拟嵌入向量
                let texts: Vec<String> = serde_json::from_value(
                    request.parameters.get("texts").cloned().unwrap_or(json!([]))
                ).unwrap_or_default();
                
                let embeddings: Vec<Vec<f32>> = texts.iter().map(|_| {
                    // 生成随机嵌入向量（128维）
                    (0..128).map(|_| rand::random::<f32>()).collect()
                }).collect();
                
                serde_json::to_value(embeddings)?
            }
            ModelOperation::Generation => {
                json!("这是一个模拟的生成结果")
            }
            ModelOperation::Classification => {
                json!({"class": "positive", "confidence": 0.95})
            }
            _ => json!("模拟结果"),
        };

        Ok(ModelResponse {
            request_id: request.id,
            model_name: request.model_name,
            result,
            execution_time_ms: 100,
            tokens_used: Some(TokensUsed {
                prompt_tokens: 10,
                completion_tokens: 20,
                total_tokens: 30,
            }),
            cached: false,
            timestamp: Utc::now(),
        })
    }

    async fn get_model_info(&self) -> Result<ModelInfo> {
        Ok(self.info.clone())
    }

    async fn health_check(&self) -> Result<HealthStatus> {
        Ok(HealthStatus::Healthy)
    }

    async fn get_rate_limits(&self) -> Result<RateLimit> {
        Ok(self.info.rate_limit.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mcp_service() {
        let config = MCPConfig::default();
        let service = Arc::new(MCPService::new(config));

        // 注册模拟提供者
        let mock_provider = Arc::new(MockModelProvider::new("mock-model"));
        service.register_provider("mock-model".to_string(), mock_provider).await.unwrap();

        // 测试嵌入请求
        let result = service.execute_embedding(
            vec!["hello world".to_string()], 
            "mock-model"
        ).await.unwrap();

        assert!(!result.is_empty());
        assert_eq!(result[0].len(), 128); // 128维嵌入向量
    }
}