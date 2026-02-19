use notify::{Watcher, RecursiveMode, WatcherKind, Config};
use std::{
    path::PathBuf,
    sync::Arc,
    collections::HashMap,
};
use tokio::sync::RwLock;
use tracing::{info, warn, error, debug};
use crate::utils::Result;

/// 热更新配置
#[derive(Debug, Clone)]
pub struct HotReloadConfig {
    pub watch_dirs: Vec<PathBuf>,
    pub file_extensions: Vec<String>,
    pub debounce_delay_ms: u64,
}

impl Default for HotReloadConfig {
    fn default() -> Self {
        Self {
            watch_dirs: vec![PathBuf::from("./agents")],
            file_extensions: vec![".py".to_string(), ".wasm".to_string()],
            debounce_delay_ms: 500,
        }
    }
}

/// 版本快照
#[derive(Debug, Clone)]
pub struct VersionSnapshot {
    pub version_id: String,
    pub timestamp: std::time::SystemTime,
    pub files: HashMap<PathBuf, Vec<u8>>,
    pub checksum: String,
}

/// 热更新引擎
pub struct HotReloadEngine {
    config: HotReloadConfig,
    watcher: Option<Arc<dyn WatcherKind>>,
    snapshots: Arc<RwLock<HashMap<String, VersionSnapshot>>>,
    active_version: Arc<RwLock<String>>,
    callback: Option<Box<dyn Fn(&str) -> Result<()> + Send + Sync>>,
}

impl HotReloadEngine {
    pub fn new(config: HotReloadConfig) -> Self {
        Self {
            config,
            watcher: None,
            snapshots: Arc::new(RwLock::new(HashMap::new())),
            active_version: Arc::new(RwLock::new("initial".to_string())),
            callback: None,
        }
    }

    /// 设置更新回调函数
    pub fn set_callback<F>(&mut self, callback: F)
    where
        F: Fn(&str) -> Result<()> + Send + Sync + 'static,
    {
        self.callback = Some(Box::new(callback));
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
        let callback = self.callback.take();
        let debounce_delay = self.config.debounce_delay_ms;
        
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
                        if let Err(e) = Self::process_events(events.drain(..).collect(), &snapshots, &active_version, &callback).await {
                            error!("Error processing file events: {}", e);
                        }
                    }
                }
            }
        });
        
        info!("Hot reload engine started");
        Ok(())
    }

    /// 处理文件事件
    async fn process_events(
        events: Vec<notify::Event>,
        snapshots: &Arc<RwLock<HashMap<String, VersionSnapshot>>>,
        active_version: &Arc<RwLock<String>>,
        callback: &Option<Box<dyn Fn(&str) -> Result<()> + Send + Sync>>
    ) -> Result<()> {
        debug!("Processing {} file events", events.len());
        
        // 筛选出相关的文件更改
        let mut relevant_changes = Vec::new();
        for event in events {
            for path in event.paths {
                if Self::is_relevant_file(&path, &vec![".py".to_string(), ".wasm".to_string()]) {
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
        let new_snapshot = Self::create_snapshot_from_changes(&relevant_changes).await?;
        
        // 保存快照
        {
            let mut snapshots_write = snapshots.write().await;
            snapshots_write.insert(new_version_id.clone(), new_snapshot);
        }
        
        // 如果有回调函数，执行更新
        if let Some(ref cb) = callback {
            match cb(&new_version_id) {
                Ok(_) => {
                    // 更新活动版本
                    *active_version.write().await = new_version_id.clone();
                    info!("Successfully updated to version: {}", new_version_id);
                }
                Err(e) => {
                    error!("Failed to update to version {}: {}", new_version_id, e);
                    // 这里可以实现回滚逻辑
                    if let Err(rollback_err) = Self::rollback_to_previous(snapshots, active_version).await {
                        error!("Rollback failed: {}", rollback_err);
                    }
                }
            }
        }
        
        Ok(())
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
        format!("v{}_{}", now, uuid::Uuid::new_v4().to_simple())
    }

    /// 从更改的文件创建快照
    async fn create_snapshot_from_changes(paths: &[PathBuf]) -> Result<VersionSnapshot> {
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
        
        Ok(VersionSnapshot {
            version_id,
            timestamp: std::time::SystemTime::now(),
            files,
            checksum,
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

    /// 回滚到上一个版本
    async fn rollback_to_previous(
        snapshots: &Arc<RwLock<HashMap<String, VersionSnapshot>>>,
        active_version: &Arc<RwLock<String>>
    ) -> Result<()> {
        let current_version = active_version.read().await.clone();
        let snapshots_read = snapshots.read().await;
        
        // 找到上一个版本（这里简化处理，实际应用中可能需要维护版本历史）
        if let Some(prev_version) = snapshots_read.keys()
            .filter(|&k| k != &current_version)
            .max() // 简单取最新的其他版本
        {
            *active_version.write().await = prev_version.clone();
            warn!("Rolled back to previous version: {}", prev_version);
            Ok(())
        } else {
            Err(crate::utils::NeuroFlowError::InternalError("No previous version to rollback".to_string()))
        }
    }

    /// 获取当前活动版本
    pub async fn get_active_version(&self) -> String {
        self.active_version.read().await.clone()
    }

    /// 获取所有版本快照
    pub async fn get_snapshots(&self) -> HashMap<String, VersionSnapshot> {
        self.snapshots.read().await.clone()
    }
}

impl Drop for HotReloadEngine {
    fn drop(&mut self) {
        info!("HotReloadEngine is being dropped");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs::File;
    use std::io::Write;

    #[tokio::test]
    async fn test_hot_reload_engine_creation() {
        let config = HotReloadConfig {
            watch_dirs: vec![std::env::temp_dir()],
            file_extensions: vec![".txt".to_string()],
            debounce_delay_ms: 100,
        };
        
        let mut engine = HotReloadEngine::new(config);
        assert!(engine.start().await.is_ok());
    }
}