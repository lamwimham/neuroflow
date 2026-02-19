//! Python Agent 沙箱模块
//! 使用进程隔离实现 Agent 安全执行

pub mod process;
pub mod manager;

pub use process::{PythonSandbox, SandboxHandle, SandboxConfig};
pub use manager::SandboxManager;

use thiserror::Error;

/// 沙箱错误类型
#[derive(Debug, Error)]
pub enum SandboxError {
    #[error("Failed to start sandbox: {0}")]
    StartFailed(String),
    
    #[error("Failed to stop sandbox: {0}")]
    StopFailed(String),
    
    #[error("Execution timeout after {0:?}")]
    Timeout(std::time::Duration),
    
    #[error("Resource limit exceeded: {0}")]
    ResourceLimit(String),
    
    #[error("Execution failed: {0}")]
    ExecutionFailed(String),
    
    #[error("Serialization error: {0}")]
    Serialization(String),
    
    #[error("Communication error: {0}")]
    Communication(String),
}

pub type Result<T> = std::result::Result<T, SandboxError>;
