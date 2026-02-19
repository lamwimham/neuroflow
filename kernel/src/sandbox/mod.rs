//! 沙箱模块
//! 提供 Agent 代码的安全隔离执行环境

pub mod python;      // Python 进程沙箱
pub mod namespace;   // Linux namespace 隔离
pub mod wasm;        // WASM 沙箱

pub use python::{SandboxConfig as PythonSandboxConfig, SandboxHandle, SandboxManager};
pub use namespace::{NamespaceIsolator, SandboxConfig as NamespaceSandboxConfig, SandboxResult, SandboxError as NamespaceSandboxError};
pub use wasm::{WasmSandbox, WasmSandboxConfig, WasmSandboxManager, WasmModule, WasmExecutionResult, WasmSandboxError};

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
    /// WASM 沙箱
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
    Wasm(WasmSandbox),
}

impl SandboxExecutor {
    pub fn new_python() -> Self {
        Self::Python(SandboxManager::new())
    }
    
    pub fn new_namespace(config: NamespaceSandboxConfig) -> Self {
        Self::Namespace(NamespaceIsolator::new(config))
    }
    
    pub fn new_wasm(config: WasmSandboxConfig) -> Result<Self, anyhow::Error> {
        let sandbox = WasmSandbox::new(config)
            .map_err(|e| anyhow::anyhow!("WASM sandbox creation failed: {}", e))?;
        Ok(Self::Wasm(sandbox))
    }
    
    pub fn execute_wasm(&mut self, module: &WasmModule, input: &[u8]) -> Result<WasmExecutionResult, anyhow::Error> {
        match self {
            Self::Wasm(sandbox) => {
                sandbox.execute(module, input)
                    .map_err(|e| anyhow::anyhow!("WASM execution failed: {}", e))
            }
            _ => Err(anyhow::anyhow!("Wrong sandbox type for WASM execution")),
        }
    }
    
    pub fn execute_namespace(&mut self, command: &str, args: &[&str]) -> Result<namespace::SandboxResult, anyhow::Error> {
        match self {
            Self::Namespace(isolator) => {
                isolator.execute(command, args)
                    .map_err(|e| anyhow::anyhow!("Namespace execution failed: {}", e))
            }
            _ => Err(anyhow::anyhow!("Wrong sandbox type for namespace execution")),
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
