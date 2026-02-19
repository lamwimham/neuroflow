//! 简化后的配置管理模块
//! 只保留核心配置，移除过度设计

use serde::{Deserialize, Serialize};
use std::path::Path;
use tracing::info;

/// 核心配置结构 - 只包含必要的配置项
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub environment: String,
    pub server: ServerConfig,
    pub sandbox: SandboxConfig,
    pub observability: ObservabilityConfig,
    pub security: SecurityConfig,
}

/// HTTP 服务器配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub max_connections: usize,
    pub request_timeout_ms: u64,
}

/// WASM 沙箱配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxConfig {
    pub max_instances: usize,
    pub memory_limit_mb: u64,
    pub timeout_ms: u64,
}

/// 可观测性配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObservabilityConfig {
    pub tracing_enabled: bool,
    pub metrics_enabled: bool,
    pub log_level: String,
}

/// 安全配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    pub rate_limit_rpm: u32,  // requests per minute
    pub request_size_limit_kb: u64,
    pub cors_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            environment: "development".to_string(),
            server: ServerConfig::default(),
            sandbox: SandboxConfig::default(),
            observability: ObservabilityConfig::default(),
            security: SecurityConfig::default(),
        }
    }
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            max_connections: 100,
            request_timeout_ms: 30000,
        }
    }
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            max_instances: 10,
            memory_limit_mb: 256,
            timeout_ms: 30000,
        }
    }
}

impl Default for ObservabilityConfig {
    fn default() -> Self {
        Self {
            tracing_enabled: true,
            metrics_enabled: true,
            log_level: "info".to_string(),
        }
    }
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            rate_limit_rpm: 1000,
            request_size_limit_kb: 1024,  // 1MB
            cors_enabled: true,
        }
    }
}

/// 配置加载器
pub struct ConfigLoader;

impl ConfigLoader {
    /// 从 TOML 文件加载配置
    pub fn from_file(path: &str) -> Result<Config, Box<dyn std::error::Error>> {
        if !Path::new(path).exists() {
            info!("Config file not found, using defaults");
            return Ok(Config::default());
        }

        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        
        info!("Config loaded from {}", path);
        Ok(config)
    }

    /// 从环境变量加载配置 (支持覆盖)
    pub fn from_env() -> Config {
        let mut config = Config::default();

        if let Ok(port_str) = std::env::var("NEUROFLOW_PORT") {
            if let Ok(port) = port_str.parse::<u16>() {
                config.server.port = port;
            }
        }

        if let Ok(level) = std::env::var("NEUROFLOW_LOG_LEVEL") {
            config.observability.log_level = level;
        }

        config
    }

    /// 验证配置
    pub fn validate(config: &Config) -> Result<(), String> {
        if config.server.port == 0 {
            return Err("Server port cannot be 0".to_string());
        }
        if config.server.max_connections == 0 {
            return Err("Server max_connections cannot be 0".to_string());
        }
        if config.sandbox.max_instances == 0 {
            return Err("Sandbox max_instances cannot be 0".to_string());
        }
        if config.sandbox.memory_limit_mb == 0 {
            return Err("Sandbox memory_limit_mb cannot be 0".to_string());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.server.port, 8080);
        assert_eq!(config.sandbox.max_instances, 10);
        assert!(config.observability.tracing_enabled);
    }

    #[test]
    fn test_config_validation() {
        let config = Config::default();
        assert!(ConfigLoader::validate(&config).is_ok());

        let invalid_config = Config {
            server: ServerConfig {
                port: 0,
                ..Default::default()
            },
            ..Default::default()
        };
        assert!(ConfigLoader::validate(&invalid_config).is_err());
    }
}
