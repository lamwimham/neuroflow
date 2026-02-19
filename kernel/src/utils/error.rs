use thiserror::Error;

#[derive(Error, Debug)]
pub enum NeuroFlowError {
    #[error("WASM execution error: {0}")]
    WasmExecution(String),
    
    #[error("Sandbox error: {0}")]
    Sandbox(String),
    
    #[error("Network error: {0}")]
    Network(String),
    
    #[error("Serialization error: {0}")]
    Serialization(String),
    
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    #[error("Resource limit exceeded: {0}")]
    ResourceLimit(String),
    
    #[error("Agent not found: {0}")]
    AgentNotFound(String),
    
    #[error("Unknown error: {0}")]
    Unknown(String),
}

impl From<anyhow::Error> for NeuroFlowError {
    fn from(error: anyhow::Error) -> Self {
        NeuroFlowError::Unknown(error.to_string())
    }
}

pub type Result<T> = std::result::Result<T, NeuroFlowError>;