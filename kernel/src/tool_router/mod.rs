//! Tool Router - 统一工具路由层
//! 
//! 负责将工具请求路由到正确的执行器 (MCP/Skills/Local/Agent)
//! 实现 AI Native 的核心：统一工具接口

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};
use uuid::Uuid;

use crate::utils::{Result, NeuroFlowError};

pub mod executor;
pub mod registry;

// 重新导出
pub use executor::*;
pub use registry::*;

/// 工具来源类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(tag = "type")]
pub enum ToolSource {
    /// 本地 Rust 函数
    Local,
    /// MCP 服务器
    Mcp { 
        server_id: String,
        server_url: Option<String>,
    },
    /// Rust Skills
    Skill { 
        skill_id: String,
    },
    /// Python Agent
    Agent { 
        agent_id: String,
        endpoint: Option<String>,
    },
    /// LLM 动态生成的工具
    LlmGenerated {
        generated_by: String,
    },
}

impl Default for ToolSource {
    fn default() -> Self {
        ToolSource::Local
    }
}

/// 工具参数定义
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolParameter {
    pub name: String,
    #[serde(rename = "type")]
    pub parameter_type: String,  // string, number, boolean, array, object
    pub description: String,
    pub required: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_value: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub enum_values: Option<Vec<serde_json::Value>>,
}

/// 工具定义 - 统一所有工具类型
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub source: ToolSource,
    pub parameters: Vec<ToolParameter>,
    #[serde(rename = "returnType", skip_serializing_if = "Option::is_none")]
    pub return_type: Option<String>,
    /// JSON Schema for LLM Function Calling
    pub schema: serde_json::Value,
    /// 额外元数据
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Map<String, serde_json::Value>>,
}

impl ToolDefinition {
    /// 转换为 OpenAI 兼容的 Function Schema
    pub fn to_openai_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters.iter().map(|p| {
                        let mut prop = json!({
                            "type": p.parameter_type,
                            "description": p.description,
                        });
                        if let Some(default) = &p.default_value {
                            prop["default"] = default.clone();
                        }
                        if let Some(enum_vals) = &p.enum_values {
                            prop["enum"] = json!(enum_vals);
                        }
                        (p.name.clone(), prop)
                    }).collect::<serde_json::Map<String, serde_json::Value>>(),
                    "required": self.parameters.iter()
                        .filter(|p| p.required)
                        .map(|p| p.name.clone())
                        .collect::<Vec<String>>(),
                }
            }
        })
    }

    /// 转换为 Anthropic 兼容的 Tool Schema
    pub fn to_anthropic_schema(&self) -> serde_json::Value {
        json!({
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters.iter().map(|p| {
                    let mut prop = json!({
                        "type": p.parameter_type,
                        "description": p.description,
                    });
                    if let Some(default) = &p.default_value {
                        prop["default"] = default.clone();
                    }
                    (p.name.clone(), prop)
                }).collect::<serde_json::Map<String, serde_json::Value>>(),
                "required": self.parameters.iter()
                    .filter(|p| p.required)
                    .map(|p| p.name.clone())
                    .collect::<Vec<String>>(),
            }
        })
    }
}

/// 工具调用请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    #[serde(rename = "callId")]
    pub call_id: String,
    #[serde(rename = "toolName")]
    pub tool_name: String,
    pub arguments: serde_json::Value,
    #[serde(rename = "timeoutMs", default = "default_timeout")]
    pub timeout_ms: u64,
}

fn default_timeout() -> u64 {
    30000  // 30 秒默认超时
}

impl ToolCall {
    pub fn new(tool_name: String, arguments: serde_json::Value) -> Self {
        Self {
            call_id: Uuid::new_v4().to_string(),
            tool_name,
            arguments,
            timeout_ms: 30000,
        }
    }
}

/// 工具调用结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    #[serde(rename = "callId")]
    pub call_id: String,
    pub success: bool,
    pub result: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(rename = "executionTimeMs")]
    pub execution_time_ms: u64,
    #[serde(rename = "tokensUsed", skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<TokensUsed>,
}

/// Token 使用统计
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokensUsed {
    #[serde(rename = "inputTokens")]
    pub input_tokens: u32,
    #[serde(rename = "outputTokens")]
    pub output_tokens: u32,
    #[serde(rename = "cacheReadTokens", skip_serializing_if = "Option::is_none")]
    pub cache_read_tokens: Option<u32>,
    #[serde(rename = "cacheWriteTokens", skip_serializing_if = "Option::is_none")]
    pub cache_write_tokens: Option<u32>,
}

impl ToolResult {
    pub fn success(call_id: String, result: serde_json::Value, execution_time_ms: u64) -> Self {
        Self {
            call_id,
            success: true,
            result,
            error: None,
            execution_time_ms,
            tokens_used: None,
        }
    }

    pub fn error(call_id: String, error: String) -> Self {
        Self {
            call_id,
            success: false,
            result: serde_json::Value::Null,
            error: Some(error),
            execution_time_ms: 0,
            tokens_used: None,
        }
    }
}

/// 转换为 LLM 消息格式
impl ToolResult {
    pub fn to_llm_message(&self) -> serde_json::Value {
        if self.success {
            json!({
                "role": "tool",
                "content": self.result.to_string(),
                "tool_call_id": self.call_id,
            })
        } else {
            json!({
                "role": "tool",
                "content": json!({
                    "error": self.error,
                }).to_string(),
                "tool_call_id": self.call_id,
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tool_definition_to_openai_schema() {
        let tool = ToolDefinition {
            id: "test-1".to_string(),
            name: "calculator".to_string(),
            description: "数学计算器".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "expression".to_string(),
                    parameter_type: "string".to_string(),
                    description: "数学表达式".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        };

        let schema = tool.to_openai_schema();
        assert_eq!(schema["function"]["name"], "calculator");
        assert!(schema["function"]["description"].as_str().unwrap().contains("计算器"));
    }

    #[test]
    fn test_tool_call_creation() {
        let call = ToolCall::new(
            "test_tool".to_string(),
            json!({"arg": "value"}),
        );
        assert_eq!(call.tool_name, "test_tool");
        assert!(!call.call_id.is_empty());
    }
}
