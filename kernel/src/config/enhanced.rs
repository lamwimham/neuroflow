use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::Path;
use tokio::sync::RwLock;
use std::sync::Arc;
use tracing::{info, warn, error};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnhancedConfig {
    pub environment: String,
    pub server: ServerConfig,
    pub sandbox: SandboxConfig,
    pub observability: ObservabilityConfig,
    pub security: SecurityConfig,
    pub routing: RoutingConfig,
    pub grpc: GrpcConfig,
    pub hot_reload: HotReloadConfig,
    pub database: DatabaseConfig,
    pub cache: CacheConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub max_connections: usize,
    pub request_timeout: u64,
    pub idle_connection_timeout: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxConfig {
    pub max_instances: usize,
    pub memory_limit: u64,
    pub cpu_limit: f64,
    pub timeout: u64,
    pub allowed_hosts: Vec<String>,
    pub allowed_paths: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObservabilityConfig {
    pub metrics_enabled: bool,
    pub traces_enabled: bool,
    pub logs_level: String,
    pub export_interval: u64,
    pub endpoint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    pub rate_limit: RateLimitConfig,
    pub cors_enabled: bool,
    pub allowed_origins: Vec<String>,
    pub jwt_secret: String,
    pub request_size_limit: u64,
    pub pii_detection: PIIDetectionConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimitConfig {
    pub requests_per_minute: u32,
    pub burst_size: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PIIDetectionConfig {
    pub enabled: bool,
    pub patterns: Vec<String>,
    pub confidence_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingConfig {
    pub semantic_enabled: bool,
    pub vector_dimension: usize,
    pub similarity_threshold: f64,
    pub max_candidates: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrpcConfig {
    pub enabled: bool,
    pub host: String,
    pub port: u16,
    pub max_message_size: u64,
    pub concurrency_limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HotReloadConfig {
    pub enabled: bool,
    pub watch_dirs: Vec<String>,
    pub polling_interval: u64,
    pub backup_enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
    pub min_connections: u32,
    pub connection_timeout: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheConfig {
    pub enabled: bool,
    pub ttl_seconds: u64,
    pub max_entries: usize,
    pub eviction_policy: String,
}

impl Default for EnhancedConfig {
    fn default() -> Self {
        Self {
            environment: "development".to_string(),
            server: ServerConfig::default(),
            sandbox: SandboxConfig::default(),
            observability: ObservabilityConfig::default(),
            security: SecurityConfig::default(),
            routing: RoutingConfig::default(),
            grpc: GrpcConfig::default(),
            hot_reload: HotReloadConfig::default(),
            database: DatabaseConfig::default(),
            cache: CacheConfig::default(),
        }
    }
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            max_connections: 100,
            request_timeout: 30,
            idle_connection_timeout: 60,
        }
    }
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            max_instances: 10,
            memory_limit: 512 * 1024 * 1024, // 512MB
            cpu_limit: 1.0,
            timeout: 30,
            allowed_hosts: vec!["localhost".to_string(), "127.0.0.1".to_string()],
            allowed_paths: vec!["/tmp".to_string()],
        }
    }
}

impl Default for ObservabilityConfig {
    fn default() -> Self {
        Self {
            metrics_enabled: true,
            traces_enabled: true,
            logs_level: "INFO".to_string(),
            export_interval: 15,
            endpoint: "http://localhost:4317".to_string(),
        }
    }
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            rate_limit: RateLimitConfig::default(),
            cors_enabled: true,
            allowed_origins: vec!["*".to_string()],
            jwt_secret: "secret-key-change-in-production".to_string(),
            request_size_limit: 10 * 1024 * 1024, // 10MB
            pii_detection: PIIDetectionConfig::default(),
        }
    }
}

impl Default for RateLimitConfig {
    fn default() -> Self {
        Self {
            requests_per_minute: 1000,
            burst_size: 100,
        }
    }
}

impl Default for PIIDetectionConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            patterns: vec![
                r"\b\d{3}-\d{2}-\d{4}\b".to_string(), // SSN
                r"\b[A-Z]{1,2}[0-9R][0-9A-Z]?\s*[0-9][A-Z]{2}\b".to_string(), // UK postcode
                r"\b\d{16}\b".to_string(), // Credit card
            ],
            confidence_threshold: 0.8,
        }
    }
}

impl Default for RoutingConfig {
    fn default() -> Self {
        Self {
            semantic_enabled: true,
            vector_dimension: 768,
            similarity_threshold: 0.7,
            max_candidates: 10,
        }
    }
}

impl Default for GrpcConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            host: "127.0.0.1".to_string(),
            port: 50051,
            max_message_size: 4 * 1024 * 1024, // 4MB
            concurrency_limit: 100,
        }
    }
}

impl Default for HotReloadConfig {
    fn default() -> Self {
        Self {
            enabled: cfg!(debug_assertions),
            watch_dirs: vec!["./config".to_string(), "./plugins".to_string()],
            polling_interval: 1000,
            backup_enabled: true,
        }
    }
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            url: "sqlite::memory:".to_string(),
            max_connections: 20,
            min_connections: 5,
            connection_timeout: 30,
        }
    }
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            ttl_seconds: 300,
            max_entries: 1000,
            eviction_policy: "lru".to_string(),
        }
    }
}

pub struct ConfigManager {
    config: Arc<RwLock<EnhancedConfig>>,
    config_path: String,
}

impl ConfigManager {
    pub fn new(config_path: String) -> Result<Self, Box<dyn std::error::Error>> {
        let config = Self::load_config(&config_path)?;
        Ok(Self {
            config: Arc::new(RwLock::new(config)),
            config_path,
        })
    }

    fn load_config(config_path: &str) -> Result<EnhancedConfig, Box<dyn std::error::Error>> {
        let mut config = if Path::new(config_path).exists() {
            let content = fs::read_to_string(config_path)?;
            toml::from_str(&content)?
        } else {
            EnhancedConfig::default()
        };

        // Override with environment variables
        config = Self::apply_env_overrides(config);

        // Validate configuration
        Self::validate_config(&config)?;

        Ok(config)
    }

    fn apply_env_overrides(mut config: EnhancedConfig) -> EnhancedConfig {
        // Environment
        if let Ok(env) = env::var("NEUROFLOW_ENV") {
            config.environment = env;
        }

        // Server
        if let Ok(host) = env::var("NEUROFLOW_SERVER_HOST") {
            config.server.host = host;
        }
        if let Ok(port_str) = env::var("NEUROFLOW_SERVER_PORT") {
            if let Ok(port) = port_str.parse::<u16>() {
                config.server.port = port;
            }
        }

        // Sandbox
        if let Ok(max_instances_str) = env::var("NEUROFLOW_SANDBOX_MAX_INSTANCES") {
            if let Ok(max_instances) = max_instances_str.parse::<usize>() {
                config.sandbox.max_instances = max_instances;
            }
        }

        // Security
        if let Ok(jwt_secret) = env::var("NEUROFLOW_JWT_SECRET") {
            config.security.jwt_secret = jwt_secret;
        }

        config
    }

    fn validate_config(config: &EnhancedConfig) -> Result<(), Box<dyn std::error::Error>> {
        // Validate server configuration
        if config.server.port == 0 {
            return Err("Server port cannot be 0".into());
        }
        if config.server.max_connections == 0 {
            return Err("Server max connections cannot be 0".into());
        }

        // Validate sandbox configuration
        if config.sandbox.max_instances == 0 {
            return Err("Sandbox max instances cannot be 0".into());
        }
        if config.sandbox.memory_limit == 0 {
            return Err("Sandbox memory limit cannot be 0".into());
        }

        // Validate security configuration
        if config.security.rate_limit.requests_per_minute == 0 {
            return Err("Rate limit requests per minute cannot be 0".into());
        }

        // Validate routing configuration
        if config.routing.similarity_threshold > 1.0 || config.routing.similarity_threshold < 0.0 {
            return Err("Routing similarity threshold must be between 0 and 1".into());
        }

        // Validate JWT secret in production
        if config.environment == "production" && config.security.jwt_secret == "secret-key-change-in-production" {
            return Err("JWT secret must be changed in production environment".into());
        }

        Ok(())
    }

    pub async fn get_config(&self) -> EnhancedConfig {
        self.config.read().await.clone()
    }

    pub async fn update_config(&self, new_config: EnhancedConfig) -> Result<(), Box<dyn std::error::Error>> {
        // Validate the new configuration
        Self::validate_config(&new_config)?;

        // Update the configuration
        {
            let mut config_write = self.config.write().await;
            *config_write = new_config;
        }

        info!("Configuration updated successfully");
        Ok(())
    }

    pub async fn reload_from_file(&self) -> Result<(), Box<dyn std::error::Error>> {
        let new_config = Self::load_config(&self.config_path)?;
        
        // Update the configuration
        {
            let mut config_write = self.config.write().await;
            *config_write = new_config;
        }

        info!("Configuration reloaded from file: {}", self.config_path);
        Ok(())
    }

    pub async fn watch_and_reload(&self) -> Result<(), Box<dyn std::error::Error>> {
        let config_path = self.config_path.clone();
        let config_arc = self.config.clone();

        tokio::spawn(async move {
            use tokio::time::{sleep, Duration};
            
            loop {
                sleep(Duration::from_secs(5)).await;
                
                // Check if config file has been modified
                if let Ok(metadata) = tokio::fs::metadata(&config_path).await {
                    // In a real implementation, we would track the last modified time
                    // and only reload if it has changed
                }
            }
        });

        Ok(())
    }

    pub fn get_environment_specific_config(environment: &str) -> EnhancedConfig {
        let mut config = EnhancedConfig::default();
        
        match environment {
            "development" => {
                config.server.port = 8080;
                config.observability.logs_level = "DEBUG".to_string();
                config.sandbox.timeout = 60;
            },
            "staging" => {
                config.server.port = 8081;
                config.observability.logs_level = "INFO".to_string();
                config.sandbox.timeout = 45;
            },
            "production" => {
                config.server.port = 8082;
                config.observability.logs_level = "WARN".to_string();
                config.sandbox.timeout = 30;
                config.security.request_size_limit = 5 * 1024 * 1024; // 5MB in prod
            },
            _ => {
                // Default configuration for unknown environments
            }
        }
        
        config
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_config_manager_creation() {
        let temp_config_path = "/tmp/test_neuroflow_config.toml";
        let config_content = r#"
            environment = "test"
            
            [server]
            host = "localhost"
            port = 9999
        "#;
        std::fs::write(temp_config_path, config_content).unwrap();

        let manager = ConfigManager::new(temp_config_path.to_string()).unwrap();
        let config = manager.get_config().await;

        assert_eq!(config.environment, "test");
        assert_eq!(config.server.port, 9999);
    }

    #[tokio::test]
    async fn test_config_validation() {
        let config = EnhancedConfig::default();
        assert!(ConfigManager::validate_config(&config).is_ok());

        let invalid_config = EnhancedConfig {
            server: ServerConfig {
                port: 0,
                ..Default::default()
            },
            ..Default::default()
        };
        
        assert!(ConfigManager::validate_config(&invalid_config).is_err());
    }

    #[tokio::test]
    async fn test_environment_specific_config() {
        let dev_config = ConfigManager::get_environment_specific_config("development");
        assert_eq!(dev_config.server.port, 8080);
        assert_eq!(dev_config.observability.logs_level, "DEBUG");

        let prod_config = ConfigManager::get_environment_specific_config("production");
        assert_eq!(prod_config.server.port, 8082);
        assert_eq!(prod_config.observability.logs_level, "WARN");
    }
}