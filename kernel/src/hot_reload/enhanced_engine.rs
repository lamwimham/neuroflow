use notify::{Watcher, RecursiveMode, WatcherKind, Config};
use std::{
    path::PathBuf,
    sync::Arc,
    collections::HashMap,
};
use tokio::sync::RwLock;
use tracing::{info, warn, error, debug, trace};
use crate::utils::Result;

/// 增强版热更新配置
#[derive(Debug, Clone)]
pub struct EnhancedHotReloadConfig {
    pub watch_dirs: Vec<PathBuf>,
    pub file_extensions: Vec<String>,
    pub debounce_delay_ms: u64,
    pub max_versions: usize,          // 最大保留版本数
    pub rollback_on_error: bool,      // 发生错误时是否自动回滚
    pub health_check_interval_ms: u64, // 健康检查间隔
    pub validation_timeout_ms: u64,   // 验证超时时间
}

impl Default for EnhancedHotReloadConfig {
    fn default() -> Self {
        Self {
            watch_dirs: vec![PathBuf::from("./agents")],
            file_extensions: vec![".py".to_string(), ".wasm".to_string()],
            debounce_delay_ms: 500,
            max_versions: 10,
            rollback_on_error: true,
            health_check_interval_ms: 5000,
            validation_timeout_ms: 10000,
        }
    }
}

/// 版本状态
#[derive(Debug, Clone, PartialEq)]
pub enum VersionState {
    Active,
    Inactive,
    Failed,
    Rollback,
}

/// 版本快照
#[derive(Debug, Clone)]
pub struct EnhancedVersionSnapshot {
    pub version_id: String,
    pub timestamp: std::time::SystemTime,
    pub files: HashMap<PathBuf, Vec<u8>>,
    pub checksum: String,
    pub state: VersionState,
    pub error_info: Option<String>, // 错误信息
    pub health_status: HealthStatus, // 健康状态
}

/// 健康状态
#[derive(Debug, Clone)]
pub struct HealthStatus {
    pub is_healthy: bool,
    pub last_check: std::time::SystemTime,
    pub error_count: u32,
    pub error_details: Option<String>,
}

impl Default for HealthStatus {
    fn default() -> Self {
        Self {
            is_healthy: true,
            last_check: std::time::SystemTime::now(),
            error_count: 0,
            error_details: None,
        }
    }
}

/// 验证器函数类型
pub type ValidatorFn = Box<dyn Fn(&str) -> Result<()> + Send + Sync>;

/// 增强版热更新引擎
pub struct EnhancedHotReloadEngine {
    config: EnhancedHotReloadConfig,
    watcher: Option<Arc<dyn WatcherKind>>,
    snapshots: Arc<RwLock<HashMap<String, EnhancedVersionSnapshot>>>,
    active_version: Arc<RwLock<String>>,
    version_history: Arc<RwLock<Vec<String>>>, // 版本历史记录
    callback: Option<Box<dyn Fn(&str) -> Result<()> + Send + Sync>>,
    validator: Option<ValidatorFn>,
    rollback_history: Arc<RwLock<Vec<String>>>, // 回滚历史记录
}

impl EnhancedHotReloadEngine {
    pub fn new(config: EnhancedHotReloadConfig) -> Self {
        Self {
            config,
            watcher: None,
            snapshots: Arc::new(RwLock::new(HashMap::new())),
            active_version: Arc::new(RwLock::new("initial".to_string())),
            version_history: Arc::new(RwLock::new(vec!["initial".to_string()])),
            callback: None,
            validator: None,
            rollback_history: Arc::new(RwLock::new(vec![])),
        }
    }

    /// 设置更新回调函数
    pub fn set_callback<F>(&mut self, callback: F)
    where
        F: Fn(&str) -> Result<()> + Send + Sync + 'static,
    {
        self.callback = Some(Box::new(callback));
    }

    /// 设置验证器函数
    pub fn set_validator<F>(&mut self, validator: F)
    where
        F: Fn(&str) -> Result<()> + Send + Sync + 'static,
    {
        self.validator = Some(Box::new(validator));
    }

    /// 启动热更新引擎
    pub async fn start(&mut self) -> Result<()> {
        let (tx, rx) = std::sync::mpsc::channel();
        
        let config = Config::default();
        let mut watcher = notify::recommended_watcher(move |res| {
            if let Ok(event) = res {
                if tx.send(event).is_err() {
                    error!("Failed to send file event");
                }
            }
        }).map_err(|e| crate::utils::NeuroFlowError::InternalError(e.to_string()))?;
        
        // 监听指定目录
        for dir in &self.config.watch_dirs {
            if let Err(e) = watcher.watch(dir, RecursiveMode::Recursive) {
                warn!("Failed to watch directory {:?}: {}", dir, e);
            } else {
                info!("Watching directory: {:?}", dir);
            }
        }
        
        self.watcher = Some(Arc::new(watcher));
        
        // 启动事件处理任务
        let snapshots = self.snapshots.clone();
        let active_version = self.active_version.clone();
        let version_history = self.version_history.clone();
        let callback = self.callback.take();
        let validator = self.validator.take();
        let debounce_delay = self.config.debounce_delay_ms;
        let config_clone = self.config.clone();
        let rollback_history = self.rollback_history.clone();
        
        tokio::spawn(async move {
            let mut events = Vec::new();
            let mut last_event_time = std::time::Instant::now();
            
            loop {
                if let Ok(event) = rx.recv_timeout(std::time::Duration::from_millis(debounce_delay)) {
                    events.push(event);
                    last_event_time = std::time::Instant::now();
                } else {
                    // 检查是否超过了去抖动延迟
                    if !events.is_empty() && last_event_time.elapsed().as_millis() >= debounce_delay as u128 {
                        // 处理累积的事件
                        if let Err(e) = Self::process_events(
                            events.drain(..).collect(), 
                            &snapshots, 
                            &active_version, 
                            &version_history,
                            &callback,
                            &validator,
                            &config_clone,
                            &rollback_history,
                        ).await {
                            error!("Error processing file events: {}", e);
                        }
                    }
                }
            }
        });
        
        // 启动健康检查任务
        self.start_health_check().await;
        
        info!("Enhanced hot reload engine started");
        Ok(())
    }

    /// 启动健康检查
    async fn start_health_check(&self) {
        let snapshots = self.snapshots.clone();
        let active_version = self.active_version.clone();
        let config = self.config.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_millis(config.health_check_interval_ms));
            
            loop {
                interval.tick().await;
                
                let active_ver = active_version.read().await.clone();
                let mut snapshots_write = snapshots.write().await;
                
                if let Some(snapshot) = snapshots_write.get_mut(&active_ver) {
                    // 这里可以实现具体的健康检查逻辑
                    let is_healthy = Self::perform_health_check(&snapshot.version_id).await;
                    
                    snapshot.health_status = HealthStatus {
                        is_healthy,
                        last_check: std::time::SystemTime::now(),
                        error_count: if is_healthy { 0 } else { snapshot.health_status.error_count + 1 },
                        error_details: if !is_healthy { Some("Health check failed".to_string()) } else { None },
                    };
                    
                    // 如果连续多次不健康，考虑回滚
                    if !is_healthy && snapshot.health_status.error_count >= 3 {
                        warn!("Active version {} is unhealthy, considering rollback", snapshot.version_id);
                    }
                }
            }
        });
    }

    /// 执行健康检查
    async fn perform_health_check(version_id: &str) -> bool {
        // 这里可以实现具体的健康检查逻辑
        // 例如：检查服务是否响应、资源使用情况等
        trace!("Performing health check for version: {}", version_id);
        
        // 简单的健康检查实现
        true // 在实际实现中，这里会检查特定服务的健康状况
    }

    /// 处理文件事件
    async fn process_events(
        events: Vec<notify::Event>,
        snapshots: &Arc<RwLock<HashMap<String, EnhancedVersionSnapshot>>>,
        active_version: &Arc<RwLock<String>>,
        version_history: &Arc<RwLock<Vec<String>>>,
        callback: &Option<Box<dyn Fn(&str) -> Result<()> + Send + Sync>>,
        validator: &Option<ValidatorFn>,
        config: &EnhancedHotReloadConfig,
        rollback_history: &Arc<RwLock<Vec<String>>>,
    ) -> Result<()> {
        debug!("Processing {} file events", events.len());
        
        // 筛选出相关的文件更改
        let mut relevant_changes = Vec::new();
        for event in events {
            for path in event.paths {
                if Self::is_relevant_file(&path, &config.file_extensions) {
                    relevant_changes.push(path);
                }
            }
        }
        
        if relevant_changes.is_empty() {
            return Ok(());
        }
        
        info!("Detected relevant file changes: {:?}", relevant_changes);
        
        // 创建新版本快照
        let new_version_id = Self::generate_version_id();
        let mut new_snapshot = Self::create_snapshot_from_changes(&relevant_changes).await?;
        
        // 保存快照
        {
            let mut snapshots_write = snapshots.write().await;
            snapshots_write.insert(new_version_id.clone(), new_snapshot.clone());
        }
        
        // 更新版本历史
        {
            let mut history = version_history.write().await;
            history.push(new_version_id.clone());
            
            // 限制历史记录数量
            if history.len() > config.max_versions {
                let to_remove = history.len() - config.max_versions;
                for _ in 0..to_remove {
                    if let Some(old_version) = history.remove(0) {
                        let mut snapshots_write = snapshots.write().await;
                        snapshots_write.remove(&old_version);
                    }
                }
            }
        }
        
        // 如果有回调函数，执行更新
        if let Some(ref cb) = callback {
            match cb(&new_version_id) {
                Ok(_) => {
                    // 如果有验证器，执行验证
                    if let Some(ref val) = validator {
                        match tokio::time::timeout(
                            tokio::time::Duration::from_millis(config.validation_timeout_ms),
                            tokio::task::spawn_blocking({
                                let version_id = new_version_id.clone();
                                move || val(&version_id)
                            })
                        ).await {
                            Ok(validation_result) => {
                                match validation_result {
                                    Ok(Ok(_)) => {
                                        // 验证成功，激活新版本
                                        *active_version.write().await = new_version_id.clone();
                                        
                                        // 更新快照状态
                                        {
                                            let mut snapshots_write = snapshots.write().await;
                                            if let Some(mut snapshot) = snapshots_write.get_mut(&new_version_id) {
                                                snapshot.state = VersionState::Active;
                                            }
                                        }
                                        
                                        info!("Successfully updated and validated to version: {}", new_version_id);
                                    }
                                    Ok(Err(e)) => {
                                        error!("Validation failed for version {}: {}", new_version_id, e);
                                        Self::mark_version_as_failed(snapshots, &new_version_id, &e.to_string()).await;
                                        
                                        if config.rollback_on_error {
                                            Self::perform_rollback(
                                                snapshots, 
                                                active_version, 
                                                version_history,
                                                rollback_history,
                                            ).await?;
                                        }
                                    }
                                    Err(e) => {
                                        error!("Validation task panicked for version {}: {}", new_version_id, e);
                                        Self::mark_version_as_failed(snapshots, &new_version_id, &e.to_string()).await;
                                        
                                        if config.rollback_on_error {
                                            Self::perform_rollback(
                                                snapshots, 
                                                active_version, 
                                                version_history,
                                                rollback_history,
                                            ).await?;
                                        }
                                    }
                                }
                            }
                            Err(_) => {
                                error!("Validation timeout for version {}", new_version_id);
                                Self::mark_version_as_failed(snapshots, &new_version_id, "Validation timeout").await;
                                
                                if config.rollback_on_error {
                                    Self::perform_rollback(
                                        snapshots, 
                                        active_version, 
                                        version_history,
                                        rollback_history,
                                    ).await?;
                                }
                            }
                        }
                    } else {
                        // 没有验证器，直接激活版本
                        *active_version.write().await = new_version_id.clone();
                        
                        // 更新快照状态
                        {
                            let mut snapshots_write = snapshots.write().await;
                            if let Some(mut snapshot) = snapshots_write.get_mut(&new_version_id) {
                                snapshot.state = VersionState::Active;
                            }
                        }
                        
                        info!("Successfully updated to version: {}", new_version_id);
                    }
                }
                Err(e) => {
                    error!("Failed to update to version {}: {}", new_version_id, e);
                    Self::mark_version_as_failed(snapshots, &new_version_id, &e.to_string()).await;
                    
                    if config.rollback_on_error {
                        Self::perform_rollback(
                            snapshots, 
                            active_version, 
                            version_history,
                            rollback_history,
                        ).await?;
                    }
                }
            }
        }
        
        Ok(())
    }

    /// 标记版本为失败
    async fn mark_version_as_failed(
        snapshots: &Arc<RwLock<HashMap<String, EnhancedVersionSnapshot>>>,
        version_id: &str,
        error_msg: &str,
    ) {
        let mut snapshots_write = snapshots.write().await;
        if let Some(mut snapshot) = snapshots_write.get_mut(version_id) {
            snapshot.state = VersionState::Failed;
            snapshot.error_info = Some(error_msg.to_string());
        }
    }

    /// 执行回滚
    async fn perform_rollback(
        snapshots: &Arc<RwLock<HashMap<String, EnhancedVersionSnapshot>>>,
        active_version: &Arc<RwLock<String>>,
        version_history: &Arc<RwLock<Vec<String>>>,
        rollback_history: &Arc<RwLock<Vec<String>>>,
    ) -> Result<()> {
        let current_version = active_version.read().await.clone();
        let history = version_history.read().await.clone();
        
        // 找到上一个健康的版本（非当前版本）
        let mut rollback_target = None;
        for version in history.iter().rev() {
            if version != &current_version {
                let snapshots_read = snapshots.read().await;
                if let Some(snapshot) = snapshots_read.get(version) {
                    if snapshot.state != VersionState::Failed && snapshot.health_status.is_healthy {
                        rollback_target = Some(version.clone());
                        break;
                    }
                }
            }
        }
        
        match rollback_target {
            Some(target_version) => {
                *active_version.write().await = target_version.clone();
                
                // 更新快照状态
                {
                    let mut snapshots_write = snapshots.write().await;
                    if let Some(mut snapshot) = snapshots_write.get_mut(&current_version) {
                        snapshot.state = VersionState::Rollback;
                    }
                    if let Some(mut snapshot) = snapshots_write.get_mut(&target_version) {
                        snapshot.state = VersionState::Active;
                    }
                }
                
                // 记录回滚历史
                {
                    let mut rollback_hist = rollback_history.write().await;
                    rollback_hist.push(format!("{}->{}", current_version, target_version));
                    
                    // 限制回滚历史长度
                    if rollback_hist.len() > 20 {
                        rollback_hist.remove(0);
                    }
                }
                
                info!("Rolled back from {} to {}", current_version, target_version);
                Ok(())
            }
            None => {
                error!("No healthy version found for rollback from {}", current_version);
                Err(crate::utils::NeuroFlowError::InternalError("No healthy version found for rollback".to_string()))
            }
        }
    }

    /// 检查文件是否相关（根据扩展名）
    fn is_relevant_file(path: &std::path::Path, extensions: &[String]) -> bool {
        if let Some(ext) = path.extension() {
            if let Some(ext_str) = ext.to_str() {
                return extensions.contains(&format!(".{}", ext_str));
            }
        }
        false
    }

    /// 生成版本ID
    fn generate_version_id() -> String {
        use std::time::{SystemTime, UNIX_EPOCH};
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("Time went backwards")
            .as_millis();
        format!("enh_v{}_{}", now, uuid::Uuid::new_v4().to_simple())
    }

    /// 从更改的文件创建快照
    async fn create_snapshot_from_changes(paths: &[PathBuf]) -> Result<EnhancedVersionSnapshot> {
        let mut files = HashMap::new();
        
        for path in paths {
            if path.exists() {
                let content = tokio::fs::read(path).await
                    .map_err(|e| crate::utils::NeuroFlowError::IoError(e.to_string()))?;
                files.insert(path.clone(), content);
            }
        }
        
        let version_id = Self::generate_version_id();
        let checksum = Self::calculate_checksum(&files)?;
        
        Ok(EnhancedVersionSnapshot {
            version_id,
            timestamp: std::time::SystemTime::now(),
            files,
            checksum,
            state: VersionState::Inactive,
            error_info: None,
            health_status: HealthStatus::default(),
        })
    }

    /// 计算快照校验和
    fn calculate_checksum(files: &HashMap<PathBuf, Vec<u8>>) -> Result<String> {
        use sha2::{Sha256, Digest};
        
        let mut hasher = Sha256::new();
        let mut sorted_paths: Vec<_> = files.keys().collect();
        sorted_paths.sort();
        
        for path in sorted_paths {
            if let Some(content) = files.get(path) {
                hasher.update(path.to_string_lossy().as_bytes());
                hasher.update(content);
            }
        }
        
        Ok(format!("{:x}", hasher.finalize()))
    }

    /// 获取当前活动版本
    pub async fn get_active_version(&self) -> String {
        self.active_version.read().await.clone()
    }

    /// 获取所有版本快照
    pub async fn get_snapshots(&self) -> HashMap<String, EnhancedVersionSnapshot> {
        self.snapshots.read().await.clone()
    }

    /// 获取版本历史
    pub async fn get_version_history(&self) -> Vec<String> {
        self.version_history.read().await.clone()
    }

    /// 获取回滚历史
    pub async fn get_rollback_history(&self) -> Vec<String> {
        self.rollback_history.read().await.clone()
    }

    /// 强制回滚到指定版本
    pub async fn force_rollback(&self, version_id: &str) -> Result<()> {
        let snapshots = self.snapshots.read().await;
        if !snapshots.contains_key(version_id) {
            return Err(crate::utils::NeuroFlowError::InvalidInput(
                format!("Version {} does not exist", version_id)
            ));
        }
        
        let mut active_version = self.active_version.write().await;
        *active_version = version_id.to_string();
        
        info!("Force rolled back to version: {}", version_id);
        Ok(())
    }

    /// 获取活跃版本的健康状态
    pub async fn get_active_version_health(&self) -> Option<HealthStatus> {
        let active_version = self.active_version.read().await.clone();
        let snapshots = self.snapshots.read().await;
        
        snapshots.get(&active_version).map(|s| s.health_status.clone())
    }
}

impl Drop for EnhancedHotReloadEngine {
    fn drop(&mut self) {
        info!("EnhancedHotReloadEngine is being dropped");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs::File;
    use std::io::Write;

    #[tokio::test]
    async fn test_enhanced_hot_reload_engine_creation() {
        let config = EnhancedHotReloadConfig {
            watch_dirs: vec![std::env::temp_dir()],
            file_extensions: vec![".txt".to_string()],
            debounce_delay_ms: 100,
            ..Default::default()
        };
        
        let mut engine = EnhancedHotReloadEngine::new(config);
        
        // 设置一个简单的回调
        engine.set_callback(|version_id: &str| {
            println!("Updated to version: {}", version_id);
            Ok(())
        });
        
        assert!(engine.start().await.is_ok());
    }

    #[tokio::test]
    async fn test_version_state_transitions() {
        let config = EnhancedHotReloadConfig::default();
        let engine = EnhancedHotReloadEngine::new(config);
        
        // 创建一个快照
        let snapshot = EnhancedVersionSnapshot {
            version_id: "test_version".to_string(),
            timestamp: std::time::SystemTime::now(),
            files: HashMap::new(),
            checksum: "test_checksum".to_string(),
            state: VersionState::Inactive,
            error_info: None,
            health_status: HealthStatus::default(),
        };
        
        {
            let mut snapshots = engine.snapshots.write().await;
            snapshots.insert("test_version".to_string(), snapshot);
        }
        
        // 测试状态转换
        engine.mark_version_as_failed(&engine.snapshots, "test_version", "test error").await;
        
        let snapshots = engine.snapshots.read().await;
        let snapshot = snapshots.get("test_version").unwrap();
        assert_eq!(snapshot.state, VersionState::Failed);
        assert_eq!(snapshot.error_info, Some("test error".to_string()));
    }
}