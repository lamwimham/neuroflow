//! 沙箱模块
//! 提供 Agent 代码的安全隔离执行环境

pub mod python;  // Python 进程沙箱

pub use python::{SandboxConfig, SandboxHandle, SandboxManager};

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// 沙箱类型枚举
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SandboxType {
    /// Python 进程沙箱
    Python,
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
            sandbox_type: SandboxType::Python,
            cpu_limit: 0.5,
            memory_limit_mb: 256,
            timeout: Duration::from_secs(30),
            allowed_domains: vec!["localhost".to_string(), "127.0.0.1".to_string()],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sandbox_config_default() {
        let config = UnifiedSandboxConfig::default();
        assert_eq!(config.sandbox_type, SandboxType::Python);
        assert_eq!(config.cpu_limit, 0.5);
        assert_eq!(config.memory_limit_mb, 256);
        assert_eq!(config.timeout, Duration::from_secs(30));
    }
}
