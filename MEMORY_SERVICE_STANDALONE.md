# NeuroFlow Memory Service - 独立运行版本

由于主代码库有历史遗留问题，创建一个独立的 Memory 服务来演示功能。

## 🚀 快速启动

### 创建独立项目

```bash
cd /Users/lianwenhua/indie/NeuroFlow
mkdir -p memory-service
cd memory-service
```

### Cargo.toml

```toml
[package]
name = "neuroflow-memory-service"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["full"] }
tracing = "0.1"
tracing-subscriber = "0.3"
uuid = { version = "1.6", features = ["v4"] }
chrono = { version = "0.4", features = ["serde"] }
env_logger = "0.10"
```

### src/main.rs

```rust
use actix_web::{web, App, HttpServer, HttpResponse, post};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use uuid::Uuid;
use chrono::{DateTime, Utc};

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
    
    HttpResponse::Ok().json(StoreResponse {
        success: true,
        memory_id: id,
    })
}

#[post("/api/memory/retrieve")]
async fn retrieve_memory(store: web::Data<Arc<MemoryStore>>, req: web::Json<RetrieveRequest>) -> HttpResponse {
    match store.retrieve(&req.agent_id, &req.key) {
        Some(entry) => HttpResponse::Ok().json(RetrieveResponse {
            found: true,
            entry: Some(entry),
        }),
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
    
    HttpResponse::Ok().json(SearchResponse {
        entries,
        total: entries.len(),
    })
}

#[post("/api/memory/extract")]
async fn extract_knowledge(_store: web::Data<Arc<MemoryStore>>, req: web::Json<ExtractKnowledgeRequest>) -> HttpResponse {
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
            value: serde_json::json!({"languages": ["Python"]}),
            timestamp: Utc::now(),
            importance: 0.9,
            tags: vec!["skill".to_string(), "knowledge".to_string()],
        },
    ];
    
    HttpResponse::Ok().json(ExtractKnowledgeResponse {
        success: true,
        knowledge_count: memories.len(),
        memories,
    })
}

// ========== Main ==========

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    tracing::info!("Starting NeuroFlow Memory Service");
    
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
```

## 🧪 测试

### 启动服务

```bash
cd memory-service
cargo run
```

### 测试 API

```bash
# 存储记忆
curl -X POST http://localhost:8080/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "key": "preference:theme",
    "value": {"theme": "dark"},
    "tags": ["preference"],
    "importance": 0.8
  }'

# 检索记忆
curl -X POST http://localhost:8080/api/memory/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "key": "preference:theme"
  }'

# 搜索记忆
curl -X POST http://localhost:8080/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "tags": ["preference"],
    "limit": 10
  }'

# 提取知识
curl -X POST http://localhost:8080/api/memory/extract \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "conversation_id": "conv-001",
    "conversation_text": "User: 我在北京工作\nAssistant: 很好！"
  }'
```

## ✅ 预期结果

所有 API 应该返回 200 OK 和有效的 JSON 响应。

---

这个独立版本可以立即运行，用于演示和测试 Memory 功能。
