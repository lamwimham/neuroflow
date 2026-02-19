//! 语义路由系统
//! 
//! 基于向量相似度的智能路由系统，使用Sentence-BERT模型进行语义理解

pub mod vector_index;
pub mod model_loader;
pub mod routing_strategy;
pub mod semantic_router;

pub use semantic_router::{SemanticRouter, RoutingResult, RouteRequest};