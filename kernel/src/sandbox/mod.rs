//! 沙箱模块
//! 提供 Agent 代码的安全隔离执行环境

pub mod python;      // Python 进程沙箱
pub mod namespace;   // Linux namespace 隔离

pub use python::{SandboxConfig as PythonSandboxConfig, SandboxHandle, SandboxManager};
pub use namespace::{NamespaceIsolator, SandboxConfig, SandboxResult, SandboxError};

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// 沙箱类型枚举
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SandboxType {
    /// Python 进程沙箱
    Python,
    /// Linux namespace 隔离沙箱
    Namespace,
    /// WASM 沙箱 (保留用于未来实现)
    Wasm,
}

/// 统一的沙箱配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedSandboxConfig {
    pub sandbox_type: SandboxType,
    pub cpu_limit: f64,
    pub memory_limit_mb: u64,
    pub timeout: Duration,
    pub allowed_domains: Vec<String>,
}

impl Default for UnifiedSandboxConfig {
    fn default() -> Self {
        Self {
            sandbox_type: SandboxType::Namespace,  // 默认使用更强的隔离
            cpu_limit: 0.5,
            memory_limit_mb: 256,
            timeout: Duration::from_secs(30),
            allowed_domains: vec!["localhost".to_string(), "127.0.0.1".to_string()],
        }
    }
}

/// 统一的沙箱执行器
pub enum SandboxExecutor {
    Python(SandboxManager),
    Namespace(NamespaceIsolator),
}

impl SandboxExecutor {
    pub fn new_python() -> Self {
        Self::Python(SandboxManager::new())
    }
    
    pub fn new_namespace(config: SandboxConfig) -> Self {
        Self::Namespace(NamespaceIsolator::new(config))
    }
    
    pub async fn execute(&self, command: &str, args: &[&str]) -> Result<SandboxResult> {
        match self {
            Self::Python(_) => {
                // Python 沙箱执行（简化版本）
                Err(anyhow::anyhow!("Python sandbox not fully implemented"))
            }
            Self::Namespace(isolator) => {
                // Namespace 隔离执行
                isolator.execute(command, args)
                    .map_err(|e| anyhow::anyhow!("Namespace execution failed: {}", e))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sandbox_config_default() {
        let config = UnifiedSandboxConfig::default();
        assert_eq!(config.sandbox_type, SandboxType::Namespace);
        assert_eq!(config.cpu_limit, 0.5);
        assert_eq!(config.memory_limit_mb, 256);
        assert_eq!(config.timeout, Duration::from_secs(30));
    }
}
