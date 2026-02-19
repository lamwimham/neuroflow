/// NeuroFlow Memory Service - Standalone Version
/// 
/// 独立运行的 Memory 服务，用于演示和测试

use actix_web::{web, App, HttpServer, HttpResponse, post};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use tracing::{info, warn};

// ========== 数据结构 ==========

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEntry {
    pub id: String,
    pub agent_id: String,
    pub key: String,
    pub value: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub importance: f32,
    pub tags: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct StoreRequest {
    pub agent_id: String,
    pub key: String,
    pub value: serde_json::Value,
    pub tags: Option<Vec<String>>,
    pub importance: Option<f32>,
}

#[derive(Debug, Serialize)]
pub struct StoreResponse {
    pub success: bool,
    pub memory_id: String,
}

#[derive(Debug, Deserialize)]
pub struct RetrieveRequest {
    pub agent_id: String,
    pub key: String,
}

#[derive(Debug, Serialize)]
pub struct RetrieveResponse {
    pub found: bool,
    pub entry: Option<MemoryEntry>,
}

#[derive(Debug, Deserialize)]
pub struct SearchRequest {
    pub agent_id: String,
    pub tags: Option<Vec<String>>,
    pub min_importance: Option<f32>,
    pub limit: Option<usize>,
}

#[derive(Debug, Serialize)]
pub struct SearchResponse {
    pub entries: Vec<MemoryEntry>,
    pub total: usize,
}

#[derive(Debug, Deserialize)]
pub struct ExtractKnowledgeRequest {
    pub agent_id: String,
    pub conversation_id: String,
    pub conversation_text: String,
}

#[derive(Debug, Serialize)]
pub struct ExtractKnowledgeResponse {
    pub success: bool,
    pub knowledge_count: usize,
    pub memories: Vec<MemoryEntry>,
}

// ========== Memory Store ==========

pub struct MemoryStore {
    entries: RwLock<HashMap<String, MemoryEntry>>,
}

impl MemoryStore {
    pub fn new() -> Self {
        Self {
            entries: RwLock::new(HashMap::new()),
        }
    }

    pub fn store(&self, agent_id: String, key: String, value: serde_json::Value, tags: Vec<String>, importance: f32) -> String {
        let id = Uuid::new_v4().to_string();
        let entry = MemoryEntry {
            id: id.clone(),
            agent_id,
            key,
            value,
            timestamp: Utc::now(),
            importance,
            tags,
        };
        
        let mut entries = self.entries.write().unwrap();
        entries.insert(id.clone(), entry);
        id
    }

    pub fn retrieve(&self, agent_id: &str, key: &str) -> Option<MemoryEntry> {
        let entries = self.entries.read().unwrap();
        entries.values()
            .find(|e| e.agent_id == agent_id && e.key == key)
            .cloned()
    }

    pub fn search(&self, agent_id: &str, tags: Option<Vec<String>>, min_importance: Option<f32>, limit: Option<usize>) -> Vec<MemoryEntry> {
        let entries = self.entries.read().unwrap();
        let mut results: Vec<MemoryEntry> = entries.values()
            .filter(|e| {
                if e.agent_id != agent_id {
                    return false;
                }
                if let Some(ref tags) = tags {
                    if !tags.iter().all(|t| e.tags.contains(t)) {
                        return false;
                    }
                }
                if let Some(min_imp) = min_importance {
                    if e.importance < min_imp {
                        return false;
                    }
                }
                true
            })
            .cloned()
            .collect();
        
        results.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        
        if let Some(limit) = limit {
            results.truncate(limit);
        }
        
        results
    }
}

// ========== HTTP Handlers ==========

#[post("/api/memory/store")]
async fn store_memory(store: web::Data<Arc<MemoryStore>>, req: web::Json<StoreRequest>) -> HttpResponse {
    let id = store.store(
        req.agent_id.clone(),
        req.key.clone(),
        req.value.clone(),
        req.tags.clone().unwrap_or_default(),
        req.importance.unwrap_or(0.5),
    );
    
    info!("Stored memory: {} for agent {}", id, req.agent_id);
    
    HttpResponse::Ok().json(StoreResponse {
        success: true,
        memory_id: id,
    })
}

#[post("/api/memory/retrieve")]
async fn retrieve_memory(store: web::Data<Arc<MemoryStore>>, req: web::Json<RetrieveRequest>) -> HttpResponse {
    match store.retrieve(&req.agent_id, &req.key) {
        Some(entry) => {
            info!("Retrieved memory: {} for agent {}", entry.id, req.agent_id);
            HttpResponse::Ok().json(RetrieveResponse {
                found: true,
                entry: Some(entry),
            })
        }
        None => HttpResponse::Ok().json(RetrieveResponse {
            found: false,
            entry: None,
        }),
    }
}

#[post("/api/memory/search")]
async fn search_memory(store: web::Data<Arc<MemoryStore>>, req: web::Json<SearchRequest>) -> HttpResponse {
    let entries = store.search(
        &req.agent_id,
        req.tags.clone(),
        req.min_importance,
        req.limit,
    );
    
    info!("Search returned {} memories for agent {}", entries.len(), req.agent_id);
    
    HttpResponse::Ok().json(SearchResponse {
        entries,
        total: entries.len(),
    })
}

#[post("/api/memory/extract")]
async fn extract_knowledge(req: web::Json<ExtractKnowledgeRequest>) -> HttpResponse {
    tracing::info!("Extracting knowledge from conversation: {}", req.conversation_id);
    
    // 简化版本：模拟知识提取
    // 实际应该调用 LLM
    
    let memories = vec![
        MemoryEntry {
            id: Uuid::new_v4().to_string(),
            agent_id: req.agent_id.clone(),
            key: "knowledge:personal_info:user_location".to_string(),
            value: serde_json::json!({"city": "北京", "country": "中国"}),
            timestamp: Utc::now(),
            importance: 0.95,
            tags: vec!["personal_info".to_string(), "knowledge".to_string()],
        },
        MemoryEntry {
            id: Uuid::new_v4().to_string(),
            agent_id: req.agent_id.clone(),
            key: "knowledge:skill:programming_languages".to_string(),
            value: serde_json::json!({"languages": ["Python", "Rust"]}),
            timestamp: Utc::now(),
            importance: 0.9,
            tags: vec!["skill".to_string(), "knowledge".to_string()],
        },
    ];
    
    tracing::info!("Extracted {} knowledge items", memories.len());
    
    HttpResponse::Ok().json(ExtractKnowledgeResponse {
        success: true,
        knowledge_count: memories.len(),
        memories,
    })
}

// ========== Main ==========

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // 初始化日志
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    tracing::info!("Starting NeuroFlow Memory Service");
    tracing::info!("Version: {}", env!("CARGO_PKG_VERSION"));
    
    let store = Arc::new(MemoryStore::new());
    let store_data = web::Data::new(store);
    
    let addr = "0.0.0.0:8080";
    tracing::info!("Listening on {}", addr);
    
    HttpServer::new(move || {
        App::new()
            .app_data(store_data.clone())
            .route("/api/memory/store", web::post().to(store_memory))
            .route("/api/memory/retrieve", web::post().to(retrieve_memory))
            .route("/api/memory/search", web::post().to(search_memory))
            .route("/api/memory/extract", web::post().to(extract_knowledge))
    })
    .bind(addr)?
    .run()
    .await
}
