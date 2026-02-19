//! 工具注册表
//! 
//! 统一管理所有工具的注册、发现和调用

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, debug, error};

use super::{ToolCall, ToolResult, ToolDefinition, ToolSource};
use super::executor::ToolExecutor;
use crate::utils::{Result, NeuroFlowError};

/// 统一工具注册表
pub struct ToolRegistry {
    tools: Arc<RwLock<HashMap<String, ToolDefinition>>>,
    executors: Arc<RwLock<HashMap<ToolSource, Arc<dyn ToolExecutor>>>>,
}

impl ToolRegistry {
    /// 创建新的工具注册表
    pub fn new() -> Self {
        Self {
            tools: Arc::new(RwLock::new(HashMap::new())),
            executors: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    /// 注册工具
    pub async fn register_tool(&self, definition: ToolDefinition) -> Result<()> {
        let name = definition.name.clone();
        
        // 检查是否已存在
        {
            let tools = self.tools.read().await;
            if tools.contains_key(&name) {
                return Err(NeuroFlowError::InvalidInput(
                    format!("Tool '{}' already registered", name)
                ));
            }
        }
        
        let mut tools = self.tools.write().await;
        tools.insert(name.clone(), definition);
        
        info!("Registered tool: {}", name);
        Ok(())
    }
    
    /// 注册执行器
    pub async fn register_executor(&self, source: ToolSource, executor: Arc<dyn ToolExecutor>) -> Result<()> {
        let mut executors = self.executors.write().await;
        
        // 检查是否已存在该类型的执行器
        if executors.contains_key(&source) {
            info!("Replacing executor for source: {:?}", source);
        }
        
        executors.insert(source, executor);
        Ok(())
    }
    
    /// 获取工具定义
    pub async fn get_tool(&self, name: &str) -> Option<ToolDefinition> {
        let tools = self.tools.read().await;
        tools.get(name).cloned()
    }
    
    /// 列出所有工具
    pub async fn list_tools(&self) -> Vec<ToolDefinition> {
        let tools = self.tools.read().await;
        tools.values().cloned().collect()
    }
    
    /// 获取所有工具的 LLM Schema (OpenAI 格式)
    pub async fn get_all_llm_schemas(&self) -> Vec<serde_json::Value> {
        let tools = self.tools.read().await;
        tools.values()
            .map(|t| t.to_openai_schema())
            .collect()
    }
    
    /// 获取所有工具的 LLM Schema (Anthropic 格式)
    pub async fn get_all_anthropic_schemas(&self) -> Vec<serde_json::Value> {
        let tools = self.tools.read().await;
        tools.values()
            .map(|t| t.to_anthropic_schema())
            .collect()
    }
    
    /// 执行工具调用
    pub async fn execute(&self, call: ToolCall) -> Result<ToolResult> {
        let tool_name = call.tool_name.clone();
        
        // 查找工具定义
        let tool = {
            let tools = self.tools.read().await;
            tools.get(&tool_name)
                .cloned()
                .ok_or_else(|| NeuroFlowError::ToolNotFound(tool_name.clone()))?
        };
        
        debug!("Executing tool: {} (source: {:?})", tool_name, tool.source);
        
        // 获取对应的执行器
        let executor = {
            let executors = self.executors.read().await;
            executors.get(&tool.source)
                .cloned()
                .ok_or_else(|| NeuroFlowError::InternalError(
                    format!("No executor for source: {:?}", tool.source)
                ))?
        };
        
        // 执行工具
        executor.execute(call).await
    }
    
    /// 根据来源获取工具列表
    pub async fn get_tools_by_source(&self, source: &ToolSource) -> Vec<ToolDefinition> {
        let tools = self.tools.read().await;
        tools.values()
            .filter(|t| &t.source == source)
            .cloned()
            .collect()
    }
    
    /// 移除工具
    pub async fn remove_tool(&self, name: &str) -> Result<()> {
        let mut tools = self.tools.write().await;
        tools.remove(name)
            .ok_or_else(|| NeuroFlowError::ToolNotFound(name.to_string()))?;
        
        info!("Removed tool: {}", name);
        Ok(())
    }
    
    /// 获取工具数量
    pub async fn count(&self) -> usize {
        let tools = self.tools.read().await;
        tools.len()
    }
}

impl Default for ToolRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::executor::LocalExecutor;
    use serde_json::json;

    #[tokio::test]
    async fn test_tool_registry() {
        let registry = ToolRegistry::new();
        
        // 创建工具定义
        let definition = ToolDefinition {
            id: "test-1".to_string(),
            name: "echo".to_string(),
            description: "回显输入".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "message".to_string(),
                    parameter_type: "string".to_string(),
                    description: "要回显的消息".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("string".to_string()),
            schema: json!({}),
            metadata: None,
        };
        
        // 注册工具
        registry.register_tool(definition).await.unwrap();
        
        // 获取工具
        let tool = registry.get_tool("echo").await.unwrap();
        assert_eq!(tool.name, "echo");
        
        // 列出工具
        let tools = registry.list_tools().await;
        assert_eq!(tools.len(), 1);
        
        // 获取 Schema
        let schemas = registry.get_all_llm_schemas().await;
        assert_eq!(schemas.len(), 1);
        assert_eq!(schemas[0]["function"]["name"], "echo");
    }

    #[tokio::test]
    async fn test_tool_registry_with_executor() {
        let registry = ToolRegistry::new();
        
        // 注册执行器
        let executor = Arc::new(LocalExecutor::new());
        registry.register_executor(ToolSource::Local, executor.clone()).await.unwrap();
        
        // 注册工具
        let definition = ToolDefinition {
            id: "test-2".to_string(),
            name: "add".to_string(),
            description: "加法".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "a".to_string(),
                    parameter_type: "number".to_string(),
                    description: "数字 a".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
                ToolParameter {
                    name: "b".to_string(),
                    parameter_type: "number".to_string(),
                    description: "数字 b".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        };
        
        registry.register_tool(definition).await.unwrap();
        
        // 注册函数
        executor.register_tool(
            |args: serde_json::Value| async move {
                let a = args["a"].as_f64().unwrap_or(0.0);
                let b = args["b"].as_f64().unwrap_or(0.0);
                Ok(json!(a + b))
            },
            registry.get_tool("add").await.unwrap(),
        ).await.unwrap();
        
        // 执行工具
        let call = ToolCall::new(
            "add".to_string(),
            json!({"a": 5, "b": 3}),
        );
        
        let result = registry.execute(call).await.unwrap();
        assert!(result.success);
        assert_eq!(result.result.as_f64().unwrap(), 8.0);
    }
}
