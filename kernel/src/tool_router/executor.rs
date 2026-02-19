//! 工具执行器 Trait 和实现
//! 
//! 定义统一的工具执行器接口，支持多种工具来源

use std::sync::Arc;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tracing::{info, debug, error};

use super::{ToolCall, ToolResult, ToolDefinition, ToolSource};
use crate::utils::{Result, NeuroFlowError};

/// 工具执行器 Trait - 所有工具类型的统一接口
#[async_trait]
pub trait ToolExecutor: Send + Sync {
    /// 执行工具调用
    async fn execute(&self, call: ToolCall) -> Result<ToolResult>;
    
    /// 获取工具定义
    async fn get_schema(&self, tool_name: &str) -> Option<ToolDefinition>;
    
    /// 验证参数
    async fn validate_params(&self, tool_name: &str, arguments: &serde_json::Value) -> Result<bool> {
        // 默认实现：总是通过
        Ok(true)
    }
    
    /// 获取执行器类型
    fn executor_type(&self) -> ToolSource;
}

/// 本地 Rust 函数执行器
pub struct LocalExecutor {
    tools: Arc<tokio::sync::RwLock<HashMap<String, Arc<dyn LocalToolFunction>>>>,
    schemas: Arc<tokio::sync::RwLock<HashMap<String, ToolDefinition>>>,
}

use std::collections::HashMap;

impl LocalExecutor {
    pub fn new() -> Self {
        Self {
            tools: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            schemas: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
        }
    }
    
    /// 注册本地工具函数
    pub async fn register_tool<F>(&self, func: F, definition: ToolDefinition) -> Result<()>
    where
        F: LocalToolFunction + 'static,
    {
        let name = definition.name.clone();
        
        let mut tools = self.tools.write().await;
        tools.insert(name.clone(), Arc::new(func));
        
        let mut schemas = self.schemas.write().await;
        schemas.insert(name.clone(), definition);
        
        info!("Registered local tool: {}", name);
        Ok(())
    }
}

impl Default for LocalExecutor {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl ToolExecutor for LocalExecutor {
    async fn execute(&self, call: ToolCall) -> Result<ToolResult> {
        let start = std::time::Instant::now();
        
        let tools = self.tools.read().await;
        let func = tools.get(&call.tool_name)
            .cloned()
            .ok_or_else(|| NeuroFlowError::ToolNotFound(call.tool_name.clone()))?;
        drop(tools);
        
        // 执行工具
        match func.call(call.arguments).await {
            Ok(result) => {
                let elapsed = start.elapsed().as_millis() as u64;
                Ok(ToolResult::success(call.call_id, result, elapsed))
            }
            Err(e) => {
                Ok(ToolResult::error(call.call_id, e.to_string()))
            }
        }
    }
    
    async fn get_schema(&self, tool_name: &str) -> Option<ToolDefinition> {
        let schemas = self.schemas.read().await;
        schemas.get(tool_name).cloned()
    }
    
    fn executor_type(&self) -> ToolSource {
        ToolSource::Local
    }
}

/// 本地工具函数 Trait
#[async_trait]
pub trait LocalToolFunction: Send + Sync {
    async fn call(&self, arguments: serde_json::Value) -> Result<serde_json::Value>;
}

/// 为闭包实现 LocalToolFunction
#[async_trait]
impl<F, Fut> LocalToolFunction for F
where
    F: Fn(serde_json::Value) -> Fut + Send + Sync,
    Fut: std::future::Future<Output = Result<serde_json::Value>> + Send,
{
    async fn call(&self, arguments: serde_json::Value) -> Result<serde_json::Value> {
        self(arguments).await
    }
}

/// MCP 工具执行器
pub struct McpExecutor {
    mcp_service: Arc<crate::mcp::MCPService>,
    tool_mappings: Arc<tokio::sync::RwLock<HashMap<String, String>>>,  // tool_name -> server_id
    schemas: Arc<tokio::sync::RwLock<HashMap<String, ToolDefinition>>>,
}

impl McpExecutor {
    pub fn new(mcp_service: Arc<crate::mcp::MCPService>) -> Self {
        Self {
            mcp_service,
            tool_mappings: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            schemas: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
        }
    }
    
    /// 添加工具映射
    pub async fn add_tool_mapping(&self, tool_name: String, server_id: String) -> Result<()> {
        let mut mappings = self.tool_mappings.write().await;
        mappings.insert(tool_name, server_id);
        Ok(())
    }
    
    /// 注册工具 Schema
    pub async fn register_schema(&self, definition: ToolDefinition) -> Result<()> {
        let name = definition.name.clone();
        let mut schemas = self.schemas.write().await;
        schemas.insert(name, definition);
        Ok(())
    }
    
    /// 从 MCP 服务器发现工具
    pub async fn discover_tools(&self, server_id: &str, server_url: &str) -> Result<Vec<ToolDefinition>> {
        // TODO: 实现实际的 MCP 工具发现逻辑
        // 这里使用模拟实现
        info!("Discovering tools from MCP server: {} at {}", server_id, server_url);
        
        // 模拟发现一些工具
        let mock_tools = vec![
            ToolDefinition {
                id: format!("{}:embedding", server_id),
                name: "get_embeddings".to_string(),
                description: "获取文本嵌入向量".to_string(),
                source: ToolSource::Mcp {
                    server_id: server_id.to_string(),
                    server_url: Some(server_url.to_string()),
                },
                parameters: vec![
                    ToolParameter {
                        name: "texts".to_string(),
                        parameter_type: "array".to_string(),
                        description: "文本列表".to_string(),
                        required: true,
                        default_value: None,
                        enum_values: None,
                    },
                    ToolParameter {
                        name: "model".to_string(),
                        parameter_type: "string".to_string(),
                        description: "嵌入模型".to_string(),
                        required: false,
                        default_value: Some(json!("sentence-transformers/all-MiniLM-L6-v2")),
                        enum_values: None,
                    },
                ],
                return_type: Some("array".to_string()),
                schema: json!({}),
                metadata: None,
            },
        ];
        
        for tool in &mock_tools {
            self.add_tool_mapping(tool.name.clone(), server_id.to_string()).await?;
            self.register_schema(tool.clone()).await?;
        }
        
        Ok(mock_tools)
    }
}

#[async_trait]
impl ToolExecutor for McpExecutor {
    async fn execute(&self, call: ToolCall) -> Result<ToolResult> {
        let start = std::time::Instant::now();
        
        let mappings = self.tool_mappings.read().await;
        let server_id = mappings.get(&call.tool_name)
            .cloned()
            .unwrap_or_else(|| "default".to_string());
        drop(mappings);
        
        debug!("Executing MCP tool {} via server {}", call.tool_name, server_id);
        
        // TODO: 实现实际的 MCP 调用
        // 这里使用模拟响应
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
        
        let elapsed = start.elapsed().as_millis() as u64;
        
        let result = json!({
            "tool": call.tool_name,
            "server": server_id,
            "arguments": call.arguments,
            "mock": true,
        });
        
        Ok(ToolResult::success(call.call_id, result, elapsed))
    }
    
    async fn get_schema(&self, tool_name: &str) -> Option<ToolDefinition> {
        let schemas = self.schemas.read().await;
        schemas.get(tool_name).cloned()
    }
    
    fn executor_type(&self) -> ToolSource {
        ToolSource::Mcp {
            server_id: "unknown".to_string(),
            server_url: None,
        }
    }
}

/// Skills 工具执行器
pub struct SkillExecutor {
    skill_registry: Arc<crate::skills::SkillRegistry>,
    schemas: Arc<tokio::sync::RwLock<HashMap<String, ToolDefinition>>>,
}

impl SkillExecutor {
    pub fn new(skill_registry: Arc<crate::skills::SkillRegistry>) -> Self {
        Self {
            skill_registry,
            schemas: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
        }
    }
    
    /// 从 Skills 注册表加载工具
    pub async fn load_skills_as_tools(&self) -> Result<Vec<ToolDefinition>> {
        let skills = self.skill_registry.list_skills(None).await?;
        let mut tool_definitions = Vec::new();
        
        for skill in skills {
            let tool_def = ToolDefinition {
                id: format!("skill:{}", skill.id),
                name: skill.name.clone(),
                description: skill.description.clone(),
                source: ToolSource::Skill {
                    skill_id: skill.id.clone(),
                },
                parameters: skill.parameters.iter().map(|p| {
                    ToolParameter {
                        name: p.name.clone(),
                        parameter_type: p.parameter_type.clone(),
                        description: p.description.clone(),
                        required: p.required,
                        default_value: p.default_value.clone(),
                        enum_values: None,
                    }
                }).collect(),
                return_type: Some(skill.return_type.clone()),
                schema: json!({}),
                metadata: None,
            };
            
            tool_definitions.push(tool_def.clone());
            
            let mut schemas = self.schemas.write().await;
            schemas.insert(skill.name.clone(), tool_def);
        }
        
        Ok(tool_definitions)
    }
}

#[async_trait]
impl ToolExecutor for SkillExecutor {
    async fn execute(&self, call: ToolCall) -> Result<ToolResult> {
        let start = std::time::Instant::now();
        
        debug!("Executing skill: {}", call.tool_name);
        
        let skill_result = self.skill_registry
            .execute_skill(&call.tool_name, call.arguments)
            .await?;
        
        let elapsed = start.elapsed().as_millis() as u64;
        
        Ok(ToolResult {
            call_id: call.call_id,
            success: skill_result.success,
            result: skill_result.output,
            error: skill_result.error_message,
            execution_time_ms: elapsed,
            tokens_used: skill_result.tokens_used.map(|t| TokensUsed {
                input_tokens: t.input_tokens,
                output_tokens: t.output_tokens,
                cache_read_tokens: Some(t.cache_read_tokens),
                cache_write_tokens: Some(t.cache_write_tokens),
            }),
        })
    }
    
    async fn get_schema(&self, tool_name: &str) -> Option<ToolDefinition> {
        let schemas = self.schemas.read().await;
        schemas.get(tool_name).cloned()
    }
    
    fn executor_type(&self) -> ToolSource {
        ToolSource::Skill {
            skill_id: "unknown".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[tokio::test]
    async fn test_local_executor() {
        let executor = LocalExecutor::new();
        
        // 注册一个简单的计算器工具
        let definition = ToolDefinition {
            id: "test-calc".to_string(),
            name: "add".to_string(),
            description: "加法计算器".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "a".to_string(),
                    parameter_type: "number".to_string(),
                    description: "第一个数".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
                ToolParameter {
                    name: "b".to_string(),
                    parameter_type: "number".to_string(),
                    description: "第二个数".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        };
        
        executor.register_tool(
            |args: serde_json::Value| async move {
                let a = args["a"].as_f64().unwrap_or(0.0);
                let b = args["b"].as_f64().unwrap_or(0.0);
                Ok(json!(a + b))
            },
            definition,
        ).await.unwrap();
        
        // 执行工具
        let call = ToolCall::new(
            "add".to_string(),
            json!({"a": 10, "b": 20}),
        );
        
        let result = executor.execute(call).await.unwrap();
        assert!(result.success);
        assert_eq!(result.result.as_f64().unwrap(), 30.0);
    }
}
