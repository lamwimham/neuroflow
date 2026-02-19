use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, mpsc};
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};
use uuid::Uuid;
use chrono::{DateTime, Utc};

use crate::utils::Result;
use crate::grpc::service::RuntimeServiceClient;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct A2AMessage {
    pub id: String,
    pub sender: String,
    pub receiver: String,
    pub message_type: MessageType,
    pub content: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub correlation_id: Option<String>,
    pub reply_to: Option<String>,
    pub priority: MessagePriority,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageType {
    Request,           // 请求
    Response,          // 响应
    Notification,      // 通知
    Query,             // 查询
    AssistanceRequest, // 协助请求
    StatusUpdate,      // 状态更新
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MessagePriority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4,
}

impl Default for MessagePriority {
    fn default() -> Self {
        MessagePriority::Normal
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCapability {
    pub name: String,
    pub version: String,
    pub description: String,
    pub supported_operations: Vec<String>,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentStatus {
    pub id: String,
    pub status: AgentStatusType,
    pub capabilities: Vec<AgentCapability>,
    pub last_seen: DateTime<Utc>,
    pub load: f32, // 0.0-1.0
    pub available_resources: ResourceInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentStatusType {
    Online,
    Busy,
    Offline,
    Maintenance,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceInfo {
    pub cpu_usage: f32,
    pub memory_usage: f32,
    pub available_memory_mb: u64,
    pub active_connections: u32,
}

#[derive(Debug, Clone)]
pub struct A2AConfig {
    pub max_message_size: usize,
    pub message_queue_size: usize,
    pub timeout_seconds: u64,
    pub retry_attempts: u32,
    pub discovery_interval_seconds: u64,
}

impl Default for A2AConfig {
    fn default() -> Self {
        Self {
            max_message_size: 1024 * 1024, // 1MB
            message_queue_size: 1000,
            timeout_seconds: 30,
            retry_attempts: 3,
            discovery_interval_seconds: 60,
        }
    }
}

pub trait A2AProtocol: Send + Sync {
    async fn send_message(&self, message: A2AMessage) -> Result<()>;
    async fn broadcast_message(&self, message: A2AMessage) -> Result<()>;
    async fn discover_agents(&self) -> Result<Vec<AgentStatus>>;
    async fn get_agent_capabilities(&self, agent_id: &str) -> Result<Vec<AgentCapability>>;
    async fn request_assistance(&self, target_agent: &str, task: &str, params: serde_json::Value) -> Result<serde_json::Value>;
    async fn subscribe_to_agent(&self, agent_id: &str, handler: Box<dyn Fn(A2AMessage) -> () + Send>);
}

pub struct A2AProtocolImpl {
    config: A2AConfig,
    client: Arc<RuntimeServiceClient>,
    message_handlers: Arc<RwLock<HashMap<String, Box<dyn Fn(A2AMessage) -> () + Send>>>>,
    pending_requests: Arc<RwLock<HashMap<String, mpsc::oneshot::Sender<serde_json::Value>>>>,
    agent_registry: Arc<RwLock<HashMap<String, AgentStatus>>>,
}

impl A2AProtocolImpl {
    pub fn new(client: Arc<RuntimeServiceClient>, config: A2AConfig) -> Self {
        Self {
            config,
            client,
            message_handlers: Arc::new(RwLock::new(HashMap::new())),
            pending_requests: Arc::new(RwLock::new(HashMap::new())),
            agent_registry: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    async fn handle_incoming_message(&self, message: A2AMessage) {
        match message.message_type {
            MessageType::Response => {
                // 处理响应消息
                if let Some(correlation_id) = message.correlation_id {
                    let mut pending = self.pending_requests.write().await;
                    if let Some(sender) = pending.remove(&correlation_id) {
                        let _ = sender.send(message.content);
                    }
                }
            }
            MessageType::AssistanceRequest => {
                // 调用订阅的消息处理器
                let handlers = self.message_handlers.read().await;
                for handler in handlers.values() {
                    handler(message.clone());
                }
            }
            _ => {
                // 调用订阅的消息处理器
                let handlers = self.message_handlers.read().await;
                for handler in handlers.values() {
                    handler(message.clone());
                }
            }
        }
    }

    async fn register_agent(&self, agent_status: AgentStatus) -> Result<()> {
        let mut registry = self.agent_registry.write().await;
        registry.insert(agent_status.id.clone(), agent_status);
        Ok(())
    }

    async fn unregister_agent(&self, agent_id: &str) -> Result<()> {
        let mut registry = self.agent_registry.write().await;
        registry.remove(agent_id);
        Ok(())
    }
}

#[async_trait::async_trait]
impl A2AProtocol for A2AProtocolImpl {
    async fn send_message(&self, message: A2AMessage) -> Result<()> {
        // 检查消息大小
        let message_size = serde_json::to_string(&message)?.len();
        if message_size > self.config.max_message_size {
            return Err(crate::utils::NeuroFlowError::InvalidInput(
                format!("Message size {} exceeds maximum allowed size {}", 
                       message_size, self.config.max_message_size)));
        }

        debug!("Sending A2A message: {} -> {}, type: {:?}", 
               message.sender, message.receiver, message.message_type);

        // 通过gRPC发送消息
        let request = tonic::Request::new(proto::A2AMessageRequest {
            message_id: message.id.clone(),
            sender: message.sender.clone(),
            receiver: message.receiver.clone(),
            message_type: message.message_type.clone() as i32,
            content: serde_json::to_string(&message.content)?,
            timestamp: message.timestamp.timestamp_millis() as i64,
            correlation_id: message.correlation_id.clone().unwrap_or_default(),
            priority: message.priority.clone() as i32,
        });

        match self.client.clone().send_a2a_message(request).await {
            Ok(_) => {
                info!("Successfully sent A2A message: {}", message.id);
                Ok(())
            }
            Err(e) => {
                error!("Failed to send A2A message {}: {}", message.id, e);
                Err(e.into())
            }
        }
    }

    async fn broadcast_message(&self, mut message: A2AMessage) -> Result<()> {
        // 获取所有在线代理
        let online_agents = self.discover_agents().await?;

        // 向每个在线代理发送消息
        for agent in online_agents {
            if agent.status == AgentStatusType::Online {
                message.receiver = agent.id.clone();
                self.send_message(message.clone()).await?;
            }
        }

        Ok(())
    }

    async fn discover_agents(&self) -> Result<Vec<AgentStatus>> {
        debug!("Discovering agents");

        let request = tonic::Request::new(proto::DiscoveryRequest {});

        match self.client.clone().discover_agents(request).await {
            Ok(response) => {
                let mut agents = Vec::new();
                for agent_proto in response.into_inner().agents {
                    let agent_status = AgentStatus {
                        id: agent_proto.id,
                        status: match agent_proto.status {
                            0 => AgentStatusType::Online,
                            1 => AgentStatusType::Busy,
                            2 => AgentStatusType::Offline,
                            3 => AgentStatusType::Maintenance,
                            _ => AgentStatusType::Offline,
                        },
                        capabilities: agent_proto.capabilities.into_iter().map(|cap| AgentCapability {
                            name: cap.name,
                            version: cap.version,
                            description: cap.description,
                            supported_operations: cap.supported_operations,
                            tags: cap.tags,
                        }).collect(),
                        last_seen: Utc.timestamp_opt(agent_proto.last_seen, 0).unwrap(),
                        load: agent_proto.load,
                        available_resources: ResourceInfo {
                            cpu_usage: agent_proto.available_resources.as_ref().map(|r| r.cpu_usage).unwrap_or(0.0),
                            memory_usage: agent_proto.available_resources.as_ref().map(|r| r.memory_usage).unwrap_or(0.0),
                            available_memory_mb: agent_proto.available_resources.as_ref().map(|r| r.available_memory_mb).unwrap_or(0),
                            active_connections: agent_proto.available_resources.as_ref().map(|r| r.active_connections).unwrap_or(0),
                        },
                    };
                    agents.push(agent_status);
                }
                Ok(agents)
            }
            Err(e) => {
                error!("Failed to discover agents: {}", e);
                Err(e.into())
            }
        }
    }

    async fn get_agent_capabilities(&self, agent_id: &str) -> Result<Vec<AgentCapability>> {
        let agents = self.discover_agents().await?;
        
        for agent in agents {
            if agent.id == agent_id {
                return Ok(agent.capabilities);
            }
        }

        Err(crate::utils::NeuroFlowError::AgentNotFound(
            format!("Agent {} not found", agent_id)))
    }

    async fn request_assistance(&self, target_agent: &str, task: &str, params: serde_json::Value) -> Result<serde_json::Value> {
        let correlation_id = Uuid::new_v4().to_string();
        
        // 创建协助请求消息
        let message = A2AMessage {
            id: Uuid::new_v4().to_string(),
            sender: "current_agent".to_string(), // 实际使用时应该是当前代理ID
            receiver: target_agent.to_string(),
            message_type: MessageType::AssistanceRequest,
            content: json!({
                "task": task,
                "params": params
            }),
            timestamp: Utc::now(),
            correlation_id: Some(correlation_id.clone()),
            reply_to: None,
            priority: MessagePriority::High,
        };

        // 创建响应通道
        let (tx, rx) = tokio::sync::oneshot::channel();
        {
            let mut pending = self.pending_requests.write().await;
            pending.insert(correlation_id.clone(), tx);
        }

        // 发送消息
        self.send_message(message).await?;

        // 等待响应
        let timeout = tokio::time::Duration::from_secs(self.config.timeout_seconds);
        match tokio::time::timeout(timeout, rx).await {
            Ok(Ok(response)) => Ok(response),
            Ok(Err(_)) => Err(crate::utils::NeuroFlowError::Timeout(
                "Response channel closed".to_string())),
            Err(_) => Err(crate::utils::NeuroFlowError::Timeout(
                "Request timed out".to_string())),
        }
    }

    async fn subscribe_to_agent(&self, agent_id: &str, handler: Box<dyn Fn(A2AMessage) -> () + Send>) {
        let mut handlers = self.message_handlers.write().await;
        handlers.insert(agent_id.to_string(), handler);
    }
}

// 辅助函数
pub fn create_request_message(
    sender: String,
    receiver: String,
    operation: String,
    params: serde_json::Value,
) -> A2AMessage {
    A2AMessage {
        id: Uuid::new_v4().to_string(),
        sender,
        receiver,
        message_type: MessageType::Request,
        content: json!({
            "operation": operation,
            "params": params
        }),
        timestamp: Utc::now(),
        correlation_id: Some(Uuid::new_v4().to_string()),
        reply_to: None,
        priority: MessagePriority::Normal,
    }
}

pub fn create_response_message(
    request_id: String,
    sender: String,
    receiver: String,
    result: serde_json::Value,
) -> A2AMessage {
    A2AMessage {
        id: Uuid::new_v4().to_string(),
        sender,
        receiver,
        message_type: MessageType::Response,
        content: json!({
            "result": result
        }),
        timestamp: Utc::now(),
        correlation_id: Some(request_id),
        reply_to: None,
        priority: MessagePriority::Normal,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_a2a_message_creation() {
        let message = create_request_message(
            "agent1".to_string(),
            "agent2".to_string(),
            "calculate".to_string(),
            json!({"a": 5, "b": 3})
        );

        assert_eq!(message.sender, "agent1");
        assert_eq!(message.receiver, "agent2");
        assert_eq!(message.message_type, MessageType::Request);
    }
}