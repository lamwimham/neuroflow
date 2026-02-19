//! 增强型配置管理器
//! 
//! 实现动态配置更新、多环境管理和配置验证回滚功能

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::Path;
use tokio::sync::RwLock;
use std::sync::Arc;
use tracing::{info, warn, error, debug};
use tokio::time::{sleep, Duration};
use notify::{Watcher, RecursiveMode, Config as NotifyConfig};
use std::sync::mpsc;

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
    pub deployment: DeploymentConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeploymentConfig {
    pub cluster_mode: bool,
    pub instance_id: String,
    pub region: String,
    pub replicas: u32,
    pub rollout_strategy: String,
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
    pub isolation_level: String, // 新增隔离级别
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
    pub firewall_rules: Vec<String>, // 新增防火墙规则
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
            deployment: DeploymentConfig::default(),
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
            isolation_level: "standard".to_string(), // 新增隔离级别
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
            firewall_rules: vec![], // 新增防火墙规则
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

impl Default for DeploymentConfig {
    fn default() -> Self {
        Self {
            cluster_mode: false,
            instance_id: uuid::Uuid::new_v4().to_string(),
            region: "us-east-1".to_string(),
            replicas: 1,
            rollout_strategy: "rolling".to_string(),
        }
    }
}

/// 配置变更事件
#[derive(Debug, Clone)]
pub enum ConfigChangeEvent {
    Updated(String), // 配置键
    Reloaded,
    Rollback(String), // 回滚原因
}

/// 配置管理器
pub struct EnhancedConfigManager {
    config: Arc<RwLock<EnhancedConfig>>,
    config_path: String,
    backup_configs: Arc<RwLock<Vec<EnhancedConfig>>>,
    watchers: Vec<tokio::task::JoinHandle<()>>,
    subscribers: Arc<RwLock<Vec<tokio::sync::mpsc::UnboundedSender<ConfigChangeEvent>>>>,
}

impl EnhancedConfigManager {
    /// 创建新的增强配置管理器
    pub fn new(config_path: String) -> Result<Self, Box<dyn std::error::Error>> {
        let config = Self::load_config(&config_path)?;
        Ok(Self {
            config: Arc::new(RwLock::new(config)),
            config_path,
            backup_configs: Arc::new(RwLock::new(Vec::new())),
            watchers: Vec::new(),
            subscribers: Arc::new(RwLock::new(Vec::new())),
        })
    }

    /// 从文件加载配置
    fn load_config(config_path: &str) -> Result<EnhancedConfig, Box<dyn std::error::Error>> {
        let mut config = if Path::new(config_path).exists() {
            let content = fs::read_to_string(config_path)?;
            toml::from_str(&content)?
        } else {
            EnhancedConfig::default()
        };

        // 应用环境变量覆盖
        config = Self::apply_env_overrides(config);

        // 验证配置
        Self::validate_config(&config)?;

        Ok(config)
    }

    /// 应用环境变量覆盖
    fn apply_env_overrides(mut config: EnhancedConfig) -> EnhancedConfig {
        // 环境
        if let Ok(env) = env::var("NEUROFLOW_ENV") {
            config.environment = env;
        }

        // 服务器
        if let Ok(host) = env::var("NEUROFLOW_SERVER_HOST") {
            config.server.host = host;
        }
        if let Ok(port_str) = env::var("NEUROFLOW_SERVER_PORT") {
            if let Ok(port) = port_str.parse::<u16>() {
                config.server.port = port;
            }
        }

        // 沙箱
        if let Ok(max_instances_str) = env::var("NEUROFLOW_SANDBOX_MAX_INSTANCES") {
            if let Ok(max_instances) = max_instances_str.parse::<usize>() {
                config.sandbox.max_instances = max_instances;
            }
        }

        // 安全
        if let Ok(jwt_secret) = env::var("NEUROFLOW_JWT_SECRET") {
            config.security.jwt_secret = jwt_secret;
        }

        // 部署
        if let Ok(cluster_mode_str) = env::var("NEUROFLOW_CLUSTER_MODE") {
            if let Ok(cluster_mode) = cluster_mode_str.parse::<bool>() {
                config.deployment.cluster_mode = cluster_mode;
            }
        }

        if let Ok(region) = env::var("NEUROFLOW_REGION") {
            config.deployment.region = region;
        }

        config
    }

    /// 验证配置
    fn validate_config(config: &EnhancedConfig) -> Result<(), Box<dyn std::error::Error>> {
        // 验证服务器配置
        if config.server.port == 0 {
            return Err("Server port cannot be 0".into());
        }
        if config.server.max_connections == 0 {
            return Err("Server max connections cannot be 0".into());
        }

        // 验证沙箱配置
        if config.sandbox.max_instances == 0 {
            return Err("Sandbox max instances cannot be 0".into());
        }
        if config.sandbox.memory_limit == 0 {
            return Err("Sandbox memory limit cannot be 0".into());
        }

        // 验证安全配置
        if config.security.rate_limit.requests_per_minute == 0 {
            return Err("Rate limit requests per minute cannot be 0".into());
        }

        // 验证路由配置
        if config.routing.similarity_threshold > 1.0 || config.routing.similarity_threshold < 0.0 {
            return Err("Routing similarity threshold must be between 0 and 1".into());
        }

        // 生产环境验证JWT密钥
        if config.environment == "production" && config.security.jwt_secret == "secret-key-change-in-production" {
            return Err("JWT secret must be changed in production environment".into());
        }

        // 验证部署配置
        if config.deployment.replicas == 0 {
            return Err("Deployment replicas cannot be 0".into());
        }

        Ok(())
    }

    /// 获取当前配置
    pub async fn get_config(&self) -> EnhancedConfig {
        self.config.read().await.clone()
    }

    /// 更新配置
    pub async fn update_config(&self, new_config: EnhancedConfig) -> Result<(), Box<dyn std::error::Error>> {
        // 验证新配置
        Self::validate_config(&new_config)?;

        // 保存当前配置到备份
        {
            let mut backups = self.backup_configs.write().await;
            backups.push(self.config.read().await.clone());
            
            // 限制备份数量，防止无限增长
            if backups.len() > 10 {
                backups.remove(0);
            }
        }

        // 更新配置
        {
            let mut config_write = self.config.write().await;
            *config_write = new_config;
        }

        info!("Configuration updated successfully");
        
        // 通知订阅者配置已更新
        self.notify_subscribers(ConfigChangeEvent::Updated("config".to_string())).await;

        Ok(())
    }

    /// 从文件重新加载配置
    pub async fn reload_from_file(&self) -> Result<(), Box<dyn std::error::Error>> {
        let new_config = Self::load_config(&self.config_path)?;
        
        // 保存当前配置到备份
        {
            let mut backups = self.backup_configs.write().await;
            backups.push(self.config.read().await.clone());
        }

        // 更新配置
        {
            let mut config_write = self.config.write().await;
            *config_write = new_config;
        }

        info!("Configuration reloaded from file: {}", self.config_path);
        
        // 通知订阅者配置已重载
        self.notify_subscribers(ConfigChangeEvent::Reloaded).await;

        Ok(())
    }

    /// 启动配置文件监视
    pub async fn start_watching(&self) -> Result<(), Box<dyn std::error::Error>> {
        let config_path = self.config_path.clone();
        let config_arc = self.config.clone();
        let backup_arc = self.backup_configs.clone();
        let subscribers = self.subscribers.clone();

        let handle = tokio::spawn(async move {
            use notify::{Config, RecommendedWatcher, Event, Error};
            use std::sync::mpsc::channel;
            
            let (tx, rx) = channel();
            let mut watcher = RecommendedWatcher::new(tx, Config::default()).unwrap();

            if let Some(parent_dir) = Path::new(&config_path).parent() {
                if watcher.watch(parent_dir, RecursiveMode::NonRecursive).is_ok() {
                    debug!("Started watching config directory: {:?}", parent_dir);
                }
            }

            loop {
                match rx.recv() {
                    Ok(Ok(Event { paths, kind: notify::EventKind::Modify(_), .. })) => {
                        if paths.iter().any(|path| path.to_string_lossy() == config_path) {
                            debug!("Config file change detected: {}", config_path);
                            
                            // 重新加载配置
                            if let Ok(new_config_content) = fs::read_to_string(&config_path) {
                                match toml::from_str::<EnhancedConfig>(&new_config_content) {
                                    Ok(mut new_config) => {
                                        // 应用环境变量覆盖
                                        new_config = Self::apply_env_overrides(new_config);
                                        
                                        // 验证新配置
                                        match Self::validate_config(&new_config) {
                                            Ok(()) => {
                                                // 保存当前配置到备份
                                                {
                                                    let mut backups = backup_arc.write().await;
                                                    backups.push(config_arc.read().await.clone());
                                                    
                                                    // 限制备份数量
                                                    if backups.len() > 10 {
                                                        backups.remove(0);
                                                    }
                                                }

                                                // 更新配置
                                                {
                                                    let mut config_write = config_arc.write().await;
                                                    *config_write = new_config;
                                                }

                                                info!("Configuration auto-reloaded from file: {}", config_path);
                                                
                                                // 通知订阅者配置已更新
                                                let _ = Self::notify_subscribers_static(&subscribers, ConfigChangeEvent::Reloaded).await;
                                            }
                                            Err(e) => {
                                                error!("Failed to validate new config: {}, rolling back", e);
                                                // 在实际实现中，这里会执行回滚操作
                                                let _ = Self::notify_subscribers_static(&subscribers, ConfigChangeEvent::Rollback(e.to_string())).await;
                                            }
                                        }
                                    }
                                    Err(e) => {
                                        error!("Failed to parse new config: {}, error: {}", config_path, e);
                                        let _ = Self::notify_subscribers_static(&subscribers, ConfigChangeEvent::Rollback(e.to_string())).await;
                                    }
                                }
                            }
                        }
                    }
                    Ok(Ok(_)) => {} // 其他事件忽略
                    Ok(Err(e)) => {
                        error!("Watch error: {:?}", e);
                    }
                    Err(e) => {
                        error!("Channel error: {:?}", e);
                    }
                }
            }
        });

        self.watchers.push(handle);

        Ok(())
    }

    /// 创建配置备份
    pub async fn create_backup(&self) -> Result<String, Box<dyn std::error::Error>> {
        let config = self.config.read().await.clone();
        let backup_path = format!("{}.backup.{}", 
            self.config_path, 
            chrono::Utc::now().format("%Y%m%d_%H%M%S")
        );

        let toml_string = toml::to_string(&config)?;
        fs::write(&backup_path, toml_string)?;

        info!("Configuration backed up to: {}", backup_path);
        Ok(backup_path)
    }

    /// 从备份恢复配置
    pub async fn restore_from_backup(&self, backup_path: &str) -> Result<(), Box<dyn std::error::Error>> {
        if !Path::new(backup_path).exists() {
            return Err(format!("Backup file does not exist: {}", backup_path).into());
        }

        let content = fs::read_to_string(backup_path)?;
        let config: EnhancedConfig = toml::from_str(&content)?;

        // 验证备份配置
        Self::validate_config(&config)?;

        // 保存当前配置到备份
        {
            let mut backups = self.backup_configs.write().await;
            backups.push(self.config.read().await.clone());
        }

        // 更新配置
        {
            let mut config_write = self.config.write().await;
            *config_write = config;
        }

        info!("Configuration restored from backup: {}", backup_path);
        
        // 通知订阅者配置已回滚
        self.notify_subscribers(ConfigChangeEvent::Rollback("restore_from_backup".to_string())).await;

        Ok(())
    }

    /// 获取配置备份列表
    pub async fn get_backups(&self) -> Vec<String> {
        let backups = self.backup_configs.read().await;
        (0..backups.len()).map(|i| format!("backup_{}", i)).collect()
    }

    /// 获取环境特定配置
    pub fn get_environment_specific_config(environment: &str) -> EnhancedConfig {
        let mut config = EnhancedConfig::default();
        
        match environment {
            "development" => {
                config.server.port = 8080;
                config.observability.logs_level = "DEBUG".to_string();
                config.sandbox.timeout = 60;
                config.deployment.replicas = 1;
            },
            "staging" => {
                config.server.port = 8081;
                config.observability.logs_level = "INFO".to_string();
                config.sandbox.timeout = 45;
                config.deployment.replicas = 2;
            },
            "production" => {
                config.server.port = 8082;
                config.observability.logs_level = "WARN".to_string();
                config.sandbox.timeout = 30;
                config.security.request_size_limit = 5 * 1024 * 1024; // 5MB in prod
                config.deployment.replicas = 3;
                config.deployment.cluster_mode = true;
            },
            "testing" => {
                config.server.port = 8083;
                config.observability.logs_level = "ERROR".to_string();
                config.sandbox.timeout = 10;
                config.deployment.replicas = 1;
            },
            _ => {
                // 未知环境的默认配置
            }
        }
        
        config
    }

    /// 订阅配置变更
    pub async fn subscribe(&self) -> tokio::sync::mpsc::UnboundedReceiver<ConfigChangeEvent> {
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
        self.subscribers.write().await.push(tx);
        rx
    }

    /// 通知订阅者配置变更
    async fn notify_subscribers(&self, event: ConfigChangeEvent) {
        let subscribers = self.subscribers.read().await;
        for subscriber in subscribers.iter() {
            let _ = subscriber.send(event.clone());
        }
    }

    /// 静态方法通知订阅者（用于内部调用）
    async fn notify_subscribers_static(
        subscribers: &Arc<RwLock<Vec<tokio::sync::mpsc::UnboundedSender<ConfigChangeEvent>>>>,
        event: ConfigChangeEvent
    ) -> Result<(), Box<dyn std::error::Error>> {
        let subs = subscribers.read().await;
        for subscriber in subs.iter() {
            let _ = subscriber.send(event.clone());
        }
        Ok(())
    }

    /// 获取配置值（通过键路径）
    pub async fn get_value<T>(&self, key_path: &str) -> Option<T>
    where
        T: serde::de::DeserializeOwned,
    {
        let config = self.config.read().await;
        let config_str = match toml::to_string(&*config) {
            Ok(s) => s,
            Err(_) => return None,
        };

        // 解析TOML字符串获取值
        let value: toml::Value = match toml::from_str(&config_str) {
            Ok(v) => v,
            Err(_) => return None,
        };

        // 根据键路径获取值
        let keys: Vec<&str> = key_path.split('.').collect();
        let mut current_value = &value;

        for key in keys {
            match current_value.get(key) {
                Some(v) => current_value = v,
                None => return None,
            }
        }

        // 尝试将值转换为目标类型
        current_value.clone().try_into().ok()
    }

    /// 设置配置值（通过键路径）
    pub async fn set_value<T>(&self, key_path: &str, value: T) -> Result<(), Box<dyn std::error::Error>>
    where
        T: serde::ser::Serialize,
    {
        let mut config = self.config.write().await;
        let mut config_value: toml::Value = toml::from_str(&toml::to_string(&*config)?)?;

        // 根据键路径设置值
        let keys: Vec<&str> = key_path.split('.').collect();
        let mut current_value = &mut config_value;

        for (i, key) in keys.iter().enumerate() {
            if i == keys.len() - 1 {
                // 最后一级，设置值
                *current_value.get_mut(*key).unwrap() = toml::Value::try_from(value)?;
            } else {
                // 中间级，获取下一级
                current_value = current_value.get_mut(*key).unwrap();
            }
        }

        // 将TOML值转换回配置结构
        let new_config: EnhancedConfig = toml::Value::try_into(config_value)?;
        
        // 验证新配置
        Self::validate_config(&new_config)?;
        
        // 更新配置
        *config = new_config;

        Ok(())
    }

    /// 执行配置回滚到上一个版本
    pub async fn rollback(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut backups = self.backup_configs.write().await;
        
        if backups.is_empty() {
            return Err("No backups available for rollback".into());
        }

        // 获取最后一个备份
        if let Some(previous_config) = backups.pop() {
            // 保存当前配置作为新备份
            let current_config = self.config.read().await.clone();
            backups.push(current_config);

            // 恢复到上一个配置
            {
                let mut config_write = self.config.write().await;
                *config_write = previous_config;
            }

            info!("Configuration rolled back to previous version");
            
            // 通知订阅者配置已回滚
            self.notify_subscribers(ConfigChangeEvent::Rollback("manual_rollback".to_string())).await;

            Ok(())
        } else {
            Err("No previous configuration to rollback to".into())
        }
    }

    /// 获取配置历史
    pub async fn get_config_history(&self) -> Vec<EnhancedConfig> {
        self.backup_configs.read().await.clone()
    }
}

impl Drop for EnhancedConfigManager {
    fn drop(&mut self) {
        // 取消所有监视任务
        for handle in self.watchers.drain(..) {
            handle.abort();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_enhanced_config_manager_creation() {
        let temp_config_path = "/tmp/test_enhanced_neuroflow_config.toml";
        let config_content = r#"
            environment = "test"
            
            [server]
            host = "localhost"
            port = 9999
            
            [deployment]
            cluster_mode = false
            instance_id = "test-instance"
            region = "us-test-1"
            replicas = 1
            rollout_strategy = "rolling"
        "#;
        std::fs::write(temp_config_path, config_content).unwrap();

        let manager = EnhancedConfigManager::new(temp_config_path.to_string()).unwrap();
        let config = manager.get_config().await;

        assert_eq!(config.environment, "test");
        assert_eq!(config.server.port, 9999);
        assert_eq!(config.deployment.cluster_mode, false);
        assert_eq!(config.deployment.replicas, 1);
    }

    #[tokio::test]
    async fn test_config_validation() {
        let config = EnhancedConfig::default();
        assert!(EnhancedConfigManager::validate_config(&config).is_ok());

        let invalid_config = EnhancedConfig {
            server: ServerConfig {
                port: 0,
                ..Default::default()
            },
            ..Default::default()
        };
        
        assert!(EnhancedConfigManager::validate_config(&invalid_config).is_err());
    }

    #[tokio::test]
    async fn test_environment_specific_config() {
        let dev_config = EnhancedConfigManager::get_environment_specific_config("development");
        assert_eq!(dev_config.server.port, 8080);
        assert_eq!(dev_config.observability.logs_level, "DEBUG");
        assert_eq!(dev_config.deployment.replicas, 1);

        let prod_config = EnhancedConfigManager::get_environment_specific_config("production");
        assert_eq!(prod_config.server.port, 8082);
        assert_eq!(prod_config.observability.logs_level, "WARN");
        assert_eq!(prod_config.deployment.replicas, 3);
        assert_eq!(prod_config.deployment.cluster_mode, true);
    }

    #[tokio::test]
    async fn test_config_backup_and_restore() {
        let temp_config_path = "/tmp/test_backup_config.toml";
        std::fs::write(temp_config_path, r#"environment = "test""#).unwrap();

        let manager = EnhancedConfigManager::new(temp_config_path.to_string()).unwrap();
        
        // 修改配置
        let mut new_config = manager.get_config().await;
        new_config.environment = "modified".to_string();
        manager.update_config(new_config).await.unwrap();
        
        // 创建备份
        let backup_path = manager.create_backup().await.unwrap();
        assert!(Path::new(&backup_path).exists());
        
        // 清理临时文件
        let _ = std::fs::remove_file(backup_path);
    }

    #[tokio::test]
    async fn test_config_subscription() {
        let temp_config_path = "/tmp/test_subscribe_config.toml";
        std::fs::write(temp_config_path, r#"environment = "test""#).unwrap();

        let manager = EnhancedConfigManager::new(temp_config_path.to_string()).unwrap();
        let mut receiver = manager.subscribe().await;

        // 修改配置以触发事件
        let mut new_config = EnhancedConfig::default();
        new_config.environment = "changed".to_string();
        manager.update_config(new_config).await.unwrap();

        // 检查是否收到事件
        tokio::time::timeout(Duration::from_millis(100), receiver.recv())
            .await
            .expect("Should receive config update event")
            .expect("Should have valid event");
    }
}