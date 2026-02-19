/// NeuroFlow Kernel - Simplified Memory HTTP Service
/// 
/// HTTP API for Memory operations

use actix_web::{web, HttpResponse, Error};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::info;

use crate::memory::{MemoryManager, MemoryEntry, MemorySortBy};
use crate::knowledge::KnowledgeExtractor;
use crate::mcp::MCPService;

// ========== 请求/响应数据结构 ==========

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
    pub error: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct RetrieveRequest {
    pub agent_id: String,
    pub key: String,
}

#[derive(Debug, Serialize)]
pub struct RetrieveResponse {
    pub found: bool,
    pub entry: Option<MemoryEntryDto>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct MemoryEntryDto {
    pub id: String,
    pub agent_id: String,
    pub key: String,
    pub value: serde_json::Value,
    pub importance: f32,
    pub tags: Vec<String>,
}

impl From<MemoryEntry> for MemoryEntryDto {
    fn from(entry: MemoryEntry) -> Self {
        Self {
            id: entry.id,
            agent_id: entry.agent_id,
            key: entry.key,
            value: entry.value,
            importance: entry.importance,
            tags: entry.tags,
        }
    }
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
    pub entries: Vec<MemoryEntryDto>,
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
    pub memories: Vec<MemoryEntryDto>,
    pub error: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct SaveConversationRequest {
    pub agent_id: String,
    pub conversation_id: String,
    pub turns: Vec<ConversationTurnDto>,
}

#[derive(Debug, Deserialize)]
pub struct ConversationTurnDto {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Serialize)]
pub struct SaveConversationResponse {
    pub success: bool,
    pub turns_saved: usize,
    pub error: Option<String>,
}

// ========== gRPC 服务实现 ==========

pub struct MemoryService {
    memory_manager: Arc<MemoryManager>,
    knowledge_extractor: Option<Arc<KnowledgeExtractor>>,
}

impl MemoryService {
    pub fn new(memory_manager: Arc<MemoryManager>) -> Self {
        Self {
            memory_manager,
            knowledge_extractor: None,
        }
    }
    
    pub fn with_knowledge_extractor(
        mut self,
        mcp_service: Arc<MCPService>,
    ) -> Self {
        let extractor = Arc::new(KnowledgeExtractor::new(
            self.memory_manager.clone(),
            mcp_service,
        ));
        self.knowledge_extractor = Some(extractor);
        self
    }
    
    /// 存储记忆
    pub async fn store(&self, req: StoreRequest) -> StoreResponse {
        let entry = MemoryEntry::new(
            req.agent_id,
            req.key,
            req.value,
            req.tags.unwrap_or_default(),
        )
        .with_importance(req.importance.unwrap_or(0.5));
        
        let memory_id = entry.id.clone();
        
        match self.memory_manager.store_memory(entry).await {
            Ok(_) => StoreResponse {
                success: true,
                memory_id,
                error: None,
            },
            Err(e) => StoreResponse {
                success: false,
                memory_id: String::new(),
                error: Some(e.to_string()),
            },
        }
    }
    
    /// 检索记忆
    pub async fn retrieve(&self, req: RetrieveRequest) -> RetrieveResponse {
        match self.memory_manager.retrieve_memory(&req.agent_id, &req.key).await {
            Ok(Some(entry)) => RetrieveResponse {
                found: true,
                entry: Some(entry.into()),
                error: None,
            },
            Ok(None) => RetrieveResponse {
                found: false,
                entry: None,
                error: None,
            },
            Err(e) => RetrieveResponse {
                found: false,
                entry: None,
                error: Some(e.to_string()),
            },
        }
    }
    
    /// 搜索记忆
    pub async fn search(&self, req: SearchRequest) -> SearchResponse {
        let query = crate::memory::MemoryQuery {
            agent_id: req.agent_id,
            key_pattern: None,
            tags: req.tags.unwrap_or_default(),
            min_importance: req.min_importance,
            limit: req.limit,
            sort_by: MemorySortBy::TimestampDesc,
        };
        
        match self.memory_manager.search_memories(query).await {
            Ok(entries) => {
                let total = entries.len();
                let dtos: Vec<MemoryEntryDto> = entries.into_iter().map(|e| e.into()).collect();
                
                SearchResponse {
                    entries: dtos,
                    total,
                }
            }
            Err(_) => SearchResponse {
                entries: vec![],
                total: 0,
            },
        }
    }
    
    /// 提取知识
    pub async fn extract_knowledge(&self, req: ExtractKnowledgeRequest) -> ExtractKnowledgeResponse {
        if let Some(extractor) = &self.knowledge_extractor {
            match extractor
                .extract_from_conversation(
                    &req.agent_id,
                    &req.conversation_id,
                    &req.conversation_text,
                )
                .await
            {
                Ok(memories) => {
                    let count = memories.len();
                    let dtos: Vec<MemoryEntryDto> = memories.into_iter().map(|e| e.into()).collect();
                    
                    info!("Extracted {} knowledge items", count);
                    
                    ExtractKnowledgeResponse {
                        success: true,
                        knowledge_count: count,
                        memories: dtos,
                        error: None,
                    }
                }
                Err(e) => ExtractKnowledgeResponse {
                    success: false,
                    knowledge_count: 0,
                    memories: vec![],
                    error: Some(e.to_string()),
                },
            }
        } else {
            ExtractKnowledgeResponse {
                success: false,
                knowledge_count: 0,
                memories: vec![],
                error: Some("Knowledge extractor not initialized".to_string()),
            }
        }
    }
    
    /// 保存对话
    pub async fn save_conversation(&self, req: SaveConversationRequest) -> SaveConversationResponse {
        let mut turns_saved = 0;
        
        for (index, turn) in req.turns.iter().enumerate() {
            let entry = MemoryEntry::new(
                req.agent_id.clone(),
                format!("conversation:{}:{}", req.conversation_id, index),
                serde_json::json!({
                    "role": turn.role,
                    "content": turn.content,
                }),
                vec!["conversation".to_string(), req.conversation_id.clone()],
            );
            
            if self.memory_manager.store_memory(entry).await.is_ok() {
                turns_saved += 1;
            }
        }
        
        info!("Saved {} conversation turns", turns_saved);
        
        SaveConversationResponse {
            success: true,
            turns_saved,
            error: None,
        }
    }
}

// ========== HTTP 路由 ==========

pub fn configure_memory_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api/memory")
            .route("/store", web::post().to(store_memory))
            .route("/retrieve", web::post().to(retrieve_memory))
            .route("/search", web::post().to(search_memory))
            .route("/extract", web::post().to(extract_knowledge))
            .route("/conversation", web::post().to(save_conversation))
    );
}

// HTTP handlers
async fn store_memory(
    service: web::Data<Arc<MemoryService>>,
    req: web::Json<StoreRequest>,
) -> Result<HttpResponse, Error> {
    let response = service.store(req.into_inner()).await;
    Ok(HttpResponse::Ok().json(response))
}

async fn retrieve_memory(
    service: web::Data<Arc<MemoryService>>,
    req: web::Json<RetrieveRequest>,
) -> Result<HttpResponse, Error> {
    let response = service.retrieve(req.into_inner()).await;
    Ok(HttpResponse::Ok().json(response))
}

async fn search_memory(
    service: web::Data<Arc<MemoryService>>,
    req: web::Json<SearchRequest>,
) -> Result<HttpResponse, Error> {
    let response = service.search(req.into_inner()).await;
    Ok(HttpResponse::Ok().json(response))
}

async fn extract_knowledge(
    service: web::Data<Arc<MemoryService>>,
    req: web::Json<ExtractKnowledgeRequest>,
) -> Result<HttpResponse, Error> {
    let response = service.extract_knowledge(req.into_inner()).await;
    Ok(HttpResponse::Ok().json(response))
}

async fn save_conversation(
    service: web::Data<Arc<MemoryService>>,
    req: web::Json<SaveConversationRequest>,
) -> Result<HttpResponse, Error> {
    let response = service.save_conversation(req.into_inner()).await;
    Ok(HttpResponse::Ok().json(response))
}
