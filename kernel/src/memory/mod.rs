/// NeuroFlow Kernel - Memory Module (Simplified)
/// 
/// 简化的 Memory 模块，移除复杂的 trait 对象

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};
use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::utils::Result;

/// 记忆类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum MemoryType {
    ShortTerm,
    LongTerm,
    Semantic,
    Episodic,
}

impl Default for MemoryType {
    fn default() -> Self {
        MemoryType::ShortTerm
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEntry {
    pub id: String,
    pub agent_id: String,
    pub key: String,
    pub value: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub expiry: Option<DateTime<Utc>>,
    pub tags: Vec<String>,
    pub importance: f32,
}

impl MemoryEntry {
    pub fn new(agent_id: String, key: String, value: serde_json::Value, tags: Vec<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            agent_id,
            key,
            value,
            timestamp: Utc::now(),
            expiry: None,
            tags,
            importance: 0.5,
        }
    }

    pub fn with_expiry(mut self, expiry: DateTime<Utc>) -> Self {
        self.expiry = Some(expiry);
        self
    }

    pub fn with_importance(mut self, importance: f32) -> Self {
        self.importance = importance.clamp(0.0, 1.0);
        self
    }

    pub fn is_expired(&self) -> bool {
        if let Some(expiry) = self.expiry {
            Utc::now() > expiry
        } else {
            false
        }
    }
}

#[derive(Debug, Clone)]
pub struct MemoryQuery {
    pub agent_id: String,
    pub key_pattern: Option<String>,
    pub tags: Vec<String>,
    pub min_importance: Option<f32>,
    pub limit: Option<usize>,
    pub sort_by: MemorySortBy,
}

#[derive(Debug, Clone)]
pub enum MemorySortBy {
    TimestampAsc,
    TimestampDesc,
    ImportanceAsc,
    ImportanceDesc,
}

#[derive(Debug, Clone)]
pub struct SemanticSearchQuery {
    pub agent_id: String,
    pub query_text: String,
    pub top_k: usize,
    pub min_similarity: f32,
}

#[derive(Debug, Clone)]
pub struct MemoryConfig {
    pub max_entries: usize,
    pub gc_interval_seconds: u64,
}

impl Default for MemoryConfig {
    fn default() -> Self {
        Self {
            max_entries: 10000,
            gc_interval_seconds: 300,
        }
    }
}

/// 简化的 MemoryManager - 直接使用 HashMap，不使用 trait 对象
pub struct MemoryManager {
    entries: Arc<RwLock<HashMap<String, MemoryEntry>>>,
    config: MemoryConfig,
}

impl MemoryManager {
    pub fn new(config: MemoryConfig) -> Self {
        Self {
            entries: Arc::new(RwLock::new(HashMap::new())),
            config,
        }
    }
    
    pub async fn store_memory(&self, entry: MemoryEntry) -> Result<()> {
        if entry.is_expired() {
            warn!("Attempting to store expired memory entry: {}", entry.id);
            return Ok(());
        }

        let mut entries = self.entries.write().await;
        let key = format!("{}:{}", entry.agent_id, entry.key);
        
        // 检查容量限制
        if entries.len() >= self.config.max_entries {
            // 简单的清理策略：删除最旧的条目
            if let Some((oldest_key, _)) = entries
                .iter()
                .min_by_key(|(_, entry)| entry.timestamp)
                .map(|(k, v)| (k.clone(), v))
            {
                entries.remove(&oldest_key);
                info!("Removed oldest memory entry due to capacity limit");
            }
        }
        
        entries.insert(key, entry);
        Ok(())
    }
    
    pub async fn retrieve_memory(&self, agent_id: &str, key: &str) -> Result<Option<MemoryEntry>> {
        let entries = self.entries.read().await;
        let full_key = format!("{}:{}", agent_id, key);

        if let Some(entry) = entries.get(&full_key) {
            if entry.is_expired() {
                drop(entries);
                self.entries.write().await.remove(&full_key);
                return Ok(None);
            }
            Ok(Some(entry.clone()))
        } else {
            Ok(None)
        }
    }
    
    pub async fn delete_memory(&self, agent_id: &str, key: &str) -> Result<()> {
        let mut entries = self.entries.write().await;
        let full_key = format!("{}:{}", agent_id, key);
        entries.remove(&full_key);
        Ok(())
    }
    
    pub async fn search_memories(&self, query: MemoryQuery) -> Result<Vec<MemoryEntry>> {
        let entries = self.entries.read().await;

        let mut results: Vec<MemoryEntry> = entries
            .values()
            .filter(|entry| {
                if entry.agent_id != query.agent_id {
                    return false;
                }
                if let Some(pattern) = &query.key_pattern {
                    if !entry.key.contains(pattern) {
                        return false;
                    }
                }
                if !query.tags.is_empty() {
                    if !query.tags.iter().all(|tag| entry.tags.contains(tag)) {
                        return false;
                    }
                }
                if let Some(min_importance) = query.min_importance {
                    if entry.importance < min_importance {
                        return false;
                    }
                }
                if entry.is_expired() {
                    return false;
                }
                true
            })
            .cloned()
            .collect();

        // 排序
        match query.sort_by {
            MemorySortBy::TimestampDesc => {
                results.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
            }
            MemorySortBy::ImportanceDesc => {
                results.sort_by(|a, b| b.importance.partial_cmp(&a.importance).unwrap());
            }
            _ => {}
        }

        // 应用限制
        if let Some(limit) = query.limit {
            results.truncate(limit);
        }

        Ok(results)
    }
}
