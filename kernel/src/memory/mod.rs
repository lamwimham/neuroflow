use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, Mutex};
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error};
use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::utils::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEntry {
    pub id: String,
    pub agent_id: String,
    pub key: String,
    pub value: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub expiry: Option<DateTime<Utc>>,
    pub tags: Vec<String>,
    pub importance: f32, // 0.0-1.0, 表示重要性
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
            importance: 0.5, // 默认中等重要性
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
    pub max_short_term_entries: usize,
    pub max_long_term_entries: usize,
    pub gc_interval_seconds: u64,
    pub embedding_dimension: usize,
}

impl Default for MemoryConfig {
    fn default() -> Self {
        Self {
            max_short_term_entries: 1000,
            max_long_term_entries: 10000,
            gc_interval_seconds: 300, // 5分钟
            embedding_dimension: 384, // Sentence-BERT small模型的维度
        }
    }
}

pub trait MemoryBackend: Send + Sync {
    async fn store(&self, entry: MemoryEntry) -> Result<()>;
    async fn load(&self, agent_id: &str, key: &str) -> Result<Option<MemoryEntry>>;
    async fn delete(&self, agent_id: &str, key: &str) -> Result<()>;
    async fn search(&self, query: MemoryQuery) -> Result<Vec<MemoryEntry>>;
    async fn semantic_search(&self, query: SemanticSearchQuery) -> Result<Vec<(MemoryEntry, f32)>>;
    async fn cleanup_expired(&self) -> Result<usize>;
}

pub struct InMemoryBackend {
    entries: Arc<RwLock<HashMap<String, MemoryEntry>>>, // agent_id:key -> entry
    config: MemoryConfig,
}

impl InMemoryBackend {
    pub fn new(config: MemoryConfig) -> Self {
        Self {
            entries: Arc::new(RwLock::new(HashMap::new())),
            config,
        }
    }
}

#[async_trait::async_trait]
impl MemoryBackend for InMemoryBackend {
    async fn store(&self, entry: MemoryEntry) -> Result<()> {
        if entry.is_expired() {
            warn!("Attempting to store expired memory entry: {}", entry.id);
            return Ok(());
        }

        let mut entries = self.entries.write().await;
        
        // 检查容量限制
        if entries.len() >= self.config.max_long_term_entries {
            // 简单的清理策略：删除最旧的条目
            let oldest_key = entries
                .iter()
                .filter(|(_, entry)| entry.agent_id == entry.agent_id)
                .min_by_key(|(_, entry)| entry.timestamp)
                .map(|(k, _)| k.clone());
            
            if let Some(key) = oldest_key {
                entries.remove(&key);
                info!("Removed oldest memory entry due to capacity limit");
            }
        }

        let key = format!("{}:{}", entry.agent_id, entry.key);
        entries.insert(key, entry);
        Ok(())
    }

    async fn load(&self, agent_id: &str, key: &str) -> Result<Option<MemoryEntry>> {
        let entries = self.entries.read().await;
        let full_key = format!("{}:{}", agent_id, key);
        
        if let Some(entry) = entries.get(&full_key) {
            if entry.is_expired() {
                drop(entries);
                // 删除过期条目
                let mut entries = self.entries.write().await;
                entries.remove(&full_key);
                return Ok(None);
            }
            Ok(Some(entry.clone()))
        } else {
            Ok(None)
        }
    }

    async fn delete(&self, agent_id: &str, key: &str) -> Result<()> {
        let mut entries = self.entries.write().await;
        let full_key = format!("{}:{}", agent_id, key);
        entries.remove(&full_key);
        Ok(())
    }

    async fn search(&self, query: MemoryQuery) -> Result<Vec<MemoryEntry>> {
        let entries = self.entries.read().await;
        
        let mut results: Vec<MemoryEntry> = entries
            .values()
            .filter(|entry| {
                // 检查agent_id
                if entry.agent_id != query.agent_id {
                    return false;
                }
                
                // 检查key模式匹配
                if let Some(pattern) = &query.key_pattern {
                    if !entry.key.contains(pattern) {
                        return false;
                    }
                }
                
                // 检查标签匹配
                if !query.tags.is_empty() {
                    if !query.tags.iter().all(|tag| entry.tags.contains(tag)) {
                        return false;
                    }
                }
                
                // 检查重要性阈值
                if let Some(min_importance) = query.min_importance {
                    if entry.importance < min_importance {
                        return false;
                    }
                }
                
                // 检查是否过期
                if entry.is_expired() {
                    return false;
                }
                
                true
            })
            .cloned()
            .collect();

        // 排序
        match query.sort_by {
            MemorySortBy::TimestampAsc => {
                results.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
            }
            MemorySortBy::TimestampDesc => {
                results.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
            }
            MemorySortBy::ImportanceAsc => {
                results.sort_by(|a, b| a.importance.partial_cmp(&b.importance).unwrap());
            }
            MemorySortBy::ImportanceDesc => {
                results.sort_by(|a, b| b.importance.partial_cmp(&a.importance).unwrap());
            }
        }

        // 应用限制
        if let Some(limit) = query.limit {
            results.truncate(limit);
        }

        Ok(results)
    }

    async fn semantic_search(&self, _query: SemanticSearchQuery) -> Result<Vec<(MemoryEntry, f32)>> {
        // TODO: 实现语义搜索功能，需要集成向量数据库
        // 这里暂时返回空结果
        Ok(vec![])
    }

    async fn cleanup_expired(&self) -> Result<usize> {
        let mut entries = self.entries.write().await;
        let initial_len = entries.len();
        
        entries.retain(|_, entry| !entry.is_expired());
        
        let removed_count = initial_len - entries.len();
        
        if removed_count > 0 {
            info!("Cleaned up {} expired memory entries", removed_count);
        }
        
        Ok(removed_count)
    }
}

pub struct MemoryManager {
    backend: Arc<dyn MemoryBackend>,
    config: MemoryConfig,
    gc_task: Option<tokio::task::JoinHandle<()>>,
}

impl MemoryManager {
    pub fn new(backend: Arc<dyn MemoryBackend>, config: MemoryConfig) -> Self {
        Self {
            backend,
            config,
            gc_task: None,
        }
    }

    pub async fn store_memory(&self, entry: MemoryEntry) -> Result<()> {
        self.backend.store(entry).await
    }

    pub async fn retrieve_memory(&self, agent_id: &str, key: &str) -> Result<Option<MemoryEntry>> {
        self.backend.load(agent_id, key).await
    }

    pub async fn delete_memory(&self, agent_id: &str, key: &str) -> Result<()> {
        self.backend.delete(agent_id, key).await
    }

    pub async fn search_memories(&self, query: MemoryQuery) -> Result<Vec<MemoryEntry>> {
        self.backend.search(query).await
    }

    pub async fn semantic_search(&self, query: SemanticSearchQuery) -> Result<Vec<(MemoryEntry, f32)>> {
        self.backend.semantic_search(query).await
    }

    pub fn start_gc_task(&mut self) {
        let backend = self.backend.clone();
        let interval = tokio::time::Duration::from_secs(self.config.gc_interval_seconds);

        self.gc_task = Some(tokio::spawn(async move {
            loop {
                tokio::time::sleep(interval).await;
                
                if let Err(e) = backend.cleanup_expired().await {
                    error!("Memory GC failed: {}", e);
                }
            }
        }));
    }

    pub async fn store_agent_memory(
        &self,
        agent_id: &str,
        key: String,
        value: serde_json::Value,
        tags: Vec<String>,
        importance: Option<f32>,
    ) -> Result<()> {
        let mut entry = MemoryEntry::new(agent_id.to_string(), key, value, tags);
        
        if let Some(importance) = importance {
            entry = entry.with_importance(importance);
        }

        self.store_memory(entry).await
    }

    pub async fn get_recent_memories(&self, agent_id: &str, limit: usize) -> Result<Vec<MemoryEntry>> {
        let query = MemoryQuery {
            agent_id: agent_id.to_string(),
            key_pattern: None,
            tags: vec![],
            min_importance: None,
            limit: Some(limit),
            sort_by: MemorySortBy::TimestampDesc,
        };

        self.search_memories(query).await
    }

    pub async fn get_important_memories(&self, agent_id: &str, min_importance: f32, limit: usize) -> Result<Vec<MemoryEntry>> {
        let query = MemoryQuery {
            agent_id: agent_id.to_string(),
            key_pattern: None,
            tags: vec![],
            min_importance: Some(min_importance),
            limit: Some(limit),
            sort_by: MemorySortBy::ImportanceDesc,
        };

        self.search_memories(query).await
    }
}

impl Drop for MemoryManager {
    fn drop(&mut self) {
        if let Some(handle) = self.gc_task.take() {
            handle.abort();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[tokio::test]
    async fn test_memory_storage_retrieval() {
        let config = MemoryConfig::default();
        let backend = Arc::new(InMemoryBackend::new(config));
        let manager = MemoryManager::new(backend, config);

        let value = json!({"user_name": "Alice", "preference": "coffee"});
        let tags = vec!["user_profile".to_string()];
        
        manager
            .store_agent_memory("agent1", "profile".to_string(), value.clone(), tags, Some(0.8))
            .await
            .unwrap();

        let retrieved = manager.retrieve_memory("agent1", "profile").await.unwrap();
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().value, value);
    }

    #[tokio::test]
    async fn test_memory_search() {
        let config = MemoryConfig::default();
        let backend = Arc::new(InMemoryBackend::new(config));
        let manager = MemoryManager::new(backend, config);

        // 存储一些测试数据
        manager
            .store_agent_memory("agent1", "profile".to_string(), json!({"name": "Alice"}), 
                               vec!["user".to_string()], Some(0.7))
            .await
            .unwrap();
        
        manager
            .store_agent_memory("agent1", "preferences".to_string(), json!({"color": "blue"}), 
                               vec!["setting".to_string()], Some(0.9))
            .await
            .unwrap();

        // 测试搜索
        let query = MemoryQuery {
            agent_id: "agent1".to_string(),
            key_pattern: Some("pref".to_string()),
            tags: vec![],
            min_importance: None,
            limit: None,
            sort_by: MemorySortBy::TimestampDesc,
        };

        let results = manager.search_memories(query).await.unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].key, "preferences");
    }
}