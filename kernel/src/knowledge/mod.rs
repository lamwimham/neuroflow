/// NeuroFlow Kernel - Knowledge Extraction Module
/// 
/// 知识提取模块，负责从对话、文档等中提取知识并存储到 Memory
/// 
/// 架构设计:
/// - KnowledgeExtractor: 核心提取器，依赖 MemoryManager + MCPService
/// - ConversationAnalyzer: 对话分析器，自动监听并提取
/// - KnowledgeCategory: 知识分类
/// 
/// 依赖关系:
/// knowledge → memory (存储)
/// knowledge → mcp (调用 LLM)
/// 无循环依赖

use std::sync::Arc;
use serde::{Deserialize, Serialize};
use tracing::{info, warn, debug};

use crate::memory::{MemoryManager, MemoryEntry};
use crate::mcp::MCPService;
use crate::utils::Result;

/// 知识分类
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum KnowledgeCategory {
    /// 个人信息（位置、职业、公司等）
    PersonalInfo,
    /// 偏好（主题、语言、工具等）
    Preference,
    /// 技能（编程语言、框架、工具等）
    Skill,
    /// 兴趣（爱好、活动等）
    Interest,
    /// 事实知识
    Fact,
    /// 其他
    Other,
}

impl std::fmt::Display for KnowledgeCategory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            KnowledgeCategory::PersonalInfo => write!(f, "personal_info"),
            KnowledgeCategory::Preference => write!(f, "preference"),
            KnowledgeCategory::Skill => write!(f, "skill"),
            KnowledgeCategory::Interest => write!(f, "interest"),
            KnowledgeCategory::Fact => write!(f, "fact"),
            KnowledgeCategory::Other => write!(f, "other"),
        }
    }
}

/// 提取的知识项
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtractedKnowledge {
    pub key: String,
    pub value: serde_json::Value,
    pub category: KnowledgeCategory,
    pub confidence: f32,
    pub tags: Vec<String>,
    pub source: Option<String>,  // 来源（conversation, document 等）
}

/// 对话轮次
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationTurn {
    pub role: String,  // "user" or "assistant"
    pub content: String,
    pub timestamp: Option<chrono::DateTime<chrono::Utc>>,
    pub metadata: Option<serde_json::Value>,
}

/// 知识提取器
pub struct KnowledgeExtractor {
    memory_manager: Arc<MemoryManager>,
    mcp_service: Arc<MCPService>,
    model_name: String,  // 使用的 LLM 模型
}

impl KnowledgeExtractor {
    /// 创建知识提取器
    pub fn new(
        memory_manager: Arc<MemoryManager>,
        mcp_service: Arc<MCPService>,
    ) -> Self {
        Self {
            memory_manager,
            mcp_service,
            model_name: "gpt-4".to_string(),  // 默认使用 GPT-4
        }
    }
    
    /// 设置使用的 LLM 模型
    pub fn with_model(mut self, model_name: &str) -> Self {
        self.model_name = model_name.to_string();
        self
    }
    
    /// 从对话中提取知识
    pub async fn extract_from_conversation(
        &self,
        agent_id: &str,
        conversation_id: &str,
        conversation_text: &str,
    ) -> Result<Vec<MemoryEntry>> {
        info!("Extracting knowledge from conversation: {}", conversation_id);
        
        // 1. 构建提取 prompt
        let prompt = self.build_extraction_prompt(conversation_text);
        
        // 2. 调用 LLM
        let llm_response = self.call_llm(&prompt).await?;
        
        // 3. 解析 LLM 输出
        let knowledge_items = self.parse_llm_response(&llm_response)?;
        
        // 4. 转换为 MemoryEntry 并存储
        let mut memories = Vec::new();
        for item in knowledge_items {
            let entry = MemoryEntry::new(
                agent_id.to_string(),
                format!("knowledge:{}:{}", item.category, item.key),
                serde_json::json!({
                    "value": item.value,
                    "confidence": item.confidence,
                    "source": "conversation",
                    "conversation_id": conversation_id,
                    "category": item.category.to_string(),
                }),
                {
                    let mut tags = item.tags.clone();
                    tags.push("knowledge".to_string());
                    tags.push(item.category.to_string());
                    tags
                },
            )
            .with_importance(item.confidence);
            
            match self.memory_manager.store_memory(entry.clone()).await {
                Ok(_) => {
                    debug!("Stored knowledge: {}", entry.key);
                    memories.push(entry);
                }
                Err(e) => {
                    warn!("Failed to store knowledge {}: {}", entry.key, e);
                }
            }
        }
        
        info!("Extracted {} knowledge items from conversation {}", memories.len(), conversation_id);
        
        Ok(memories)
    }
    
    /// 从对话轮次列表中提取知识
    pub async fn extract_from_turns(
        &self,
        agent_id: &str,
        conversation_id: &str,
        turns: &[ConversationTurn],
    ) -> Result<Vec<MemoryEntry>> {
        // 转换为文本
        let conversation_text = turns
            .iter()
            .map(|turn| format!("{}: {}", turn.role, turn.content))
            .collect::<Vec<_>>()
            .join("\n");
        
        self.extract_from_conversation(agent_id, conversation_id, &conversation_text).await
    }
    
    /// 构建提取 prompt
    fn build_extraction_prompt(&self, conversation_text: &str) -> String {
        format!(
            r#"从以下对话中提取用户的知识。

对话内容:
{conversation}

请提取以下类型的知识:
1. 个人信息（位置、职业、公司、教育背景等）
2. 偏好（主题、语言、工具、框架等）
3. 技能（编程语言、框架、工具、技术等）
4. 兴趣（爱好、活动、关注领域等）
5. 事实知识（用户提到的客观事实）

请以 JSON 数组格式返回，每个知识项包含:
{{
  "key": "简短的键名（英文，下划线分隔）",
  "value": {{ "具体数据对象，结构化" }},
  "category": "personal_info|preference|skill|interest|fact",
  "confidence": 0.0-1.0（置信度）,
  "tags": ["标签 1", "标签 2"]
}}

注意事项:
- 只提取明确的信息，不要推测
- confidence 表示你对提取内容的确信程度
- value 应该是结构化的 JSON 对象
- key 应该简洁且有描述性

示例输出:
[
  {{
    "key": "user_location",
    "value": {{"city": "北京", "country": "中国"}},
    "category": "personal_info",
    "confidence": 0.95,
    "tags": ["location", "personal"]
  }},
  {{
    "key": "programming_languages",
    "value": {{"languages": ["Python", "Rust"], "proficiency": "advanced"}},
    "category": "skill",
    "confidence": 0.9,
    "tags": ["programming", "skills"]
  }}
]

只返回 JSON 数组，不要其他内容。如果对话中没有可提取的知识，返回空数组 []。"#,
            conversation = conversation_text
        )
    }
    
    /// 调用 LLM
    async fn call_llm(&self, prompt: &str) -> Result<String> {
        debug!("Calling LLM for knowledge extraction");
        
        // 简化版本：直接返回模拟响应
        // 实际应该通过 MCPService 调用真实的 LLM
        let mock_response = serde_json::json!([
            {
                "key": "user_location",
                "value": {"city": "北京", "country": "中国"},
                "category": "personal_info",
                "confidence": 0.95,
                "tags": ["location", "personal"]
            }
        ]);
        
        Ok(mock_response.to_string())
    }
    
    /// 解析 LLM 响应
    fn parse_llm_response(&self, response: &str) -> Result<Vec<ExtractedKnowledge>> {
        // 清理响应（可能包含 markdown 代码块标记）
        let json_str = response
            .trim()
            .trim_start_matches("```json")
            .trim_start_matches("```")
            .trim_end_matches("```")
            .trim();
        
        if json_str.is_empty() {
            debug!("LLM returned empty response");
            return Ok(Vec::new());
        }
        
        // 解析 JSON
        let items: Vec<ExtractedKnowledge> = serde_json::from_str(json_str)
            .map_err(|e| {
                warn!("Failed to parse LLM response: {}", e);
                crate::utils::NeuroFlowError::InternalError(
                    format!("Failed to parse LLM response: {}", e)
                )
            })?;
        
        // 验证和过滤
        let valid_items: Vec<ExtractedKnowledge> = items
            .into_iter()
            .filter(|item| {
                if item.key.is_empty() {
                    warn!("Skipping knowledge item with empty key");
                    false
                } else if item.confidence < 0.0 || item.confidence > 1.0 {
                    warn!("Skipping knowledge item with invalid confidence: {}", item.confidence);
                    false
                } else {
                    true
                }
            })
            .collect();
        
        debug!("Parsed {} valid knowledge items", valid_items.len());
        
        Ok(valid_items)
    }
    
    /// 从文档中提取知识
    pub async fn extract_from_document(
        &self,
        agent_id: &str,
        document_text: &str,
        document_type: &str,
    ) -> Result<Vec<MemoryEntry>> {
        info!("Extracting knowledge from document (type: {})", document_type);
        
        let prompt = self.build_document_extraction_prompt(document_text, document_type);
        let llm_response = self.call_llm(&prompt).await?;
        let knowledge_items = self.parse_llm_response(&llm_response)?;
        
        let mut memories = Vec::new();
        for item in knowledge_items {
            let entry = MemoryEntry::new(
                agent_id.to_string(),
                format!("knowledge:{}:{}", item.category, item.key),
                serde_json::json!({
                    "value": item.value,
                    "confidence": item.confidence,
                    "source": "document",
                    "document_type": document_type,
                    "category": item.category.to_string(),
                }),
                {
                    let mut tags = item.tags.clone();
                    tags.push("knowledge".to_string());
                    tags.push(item.category.to_string());
                    tags.push("document".to_string());
                    tags
                },
            )
            .with_importance(item.confidence);
            
            self.memory_manager.store_memory(entry.clone()).await?;
            memories.push(entry);
        }
        
        info!("Extracted {} knowledge items from document", memories.len());
        
        Ok(memories)
    }
    
    /// 构建文档提取 prompt
    fn build_document_extraction_prompt(&self, document_text: &str, document_type: &str) -> String {
        format!(
            r#"从以下{doc_type}中提取重要知识。

文档内容:
{content}

请提取有价值的知识项，包括:
- 关键事实
- 重要概念
- 技术细节
- 其他值得记忆的信息

输出格式与对话提取相同（JSON 数组）。"#,
            doc_type = document_type,
            content = document_text
        )
    }
}

/// 对话分析器 - 自动监听对话并提取知识
pub struct ConversationAnalyzer {
    extractor: Arc<KnowledgeExtractor>,
    auto_extract: bool,  // 是否自动提取
    min_turns: usize,    // 最小对话轮数触发提取
}

impl ConversationAnalyzer {
    pub fn new(extractor: Arc<KnowledgeExtractor>) -> Self {
        Self {
            extractor,
            auto_extract: true,
            min_turns: 3,  // 至少 3 轮对话才提取
        }
    }
    
    /// 设置是否自动提取
    pub fn with_auto_extract(mut self, enabled: bool) -> Self {
        self.auto_extract = enabled;
        self
    }
    
    /// 设置最小对话轮数
    pub fn with_min_turns(mut self, min_turns: usize) -> Self {
        self.min_turns = min_turns;
        self
    }
    
    /// 分析对话并提取知识
    pub async fn analyze_and_extract(
        &self,
        agent_id: &str,
        conversation_id: &str,
        turns: &[ConversationTurn],
    ) -> Result<usize> {
        // 检查是否达到最小轮数
        if turns.len() < self.min_turns {
            debug!(
                "Skipping knowledge extraction: only {} turns (min: {})",
                turns.len(),
                self.min_turns
            );
            return Ok(0);
        }
        
        // 检查是否自动提取
        if !self.auto_extract {
            debug!("Auto extraction is disabled");
            return Ok(0);
        }
        
        // 提取知识
        let memories = self.extractor
            .extract_from_turns(agent_id, conversation_id, turns)
            .await?;
        
        Ok(memories.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_knowledge_category_display() {
        assert_eq!(KnowledgeCategory::PersonalInfo.to_string(), "personal_info");
        assert_eq!(KnowledgeCategory::Preference.to_string(), "preference");
        assert_eq!(KnowledgeCategory::Skill.to_string(), "skill");
    }
    
    #[test]
    fn test_parse_empty_response() {
        let extractor = KnowledgeExtractor::new(
            Arc::new(MemoryManager::new(
                Arc::new(crate::memory::InMemoryBackend::new(crate::memory::MemoryConfig::default())),
                crate::memory::MemoryConfig::default(),
            )),
            Arc::new(MCPService::new(crate::mcp::MCPConfig::default())),
        );
        
        let result = extractor.parse_llm_response("[]");
        assert!(result.is_ok());
        assert!(result.unwrap().is_empty());
    }
}
