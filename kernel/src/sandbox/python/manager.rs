//! 沙箱管理器
//! 管理多个沙箱实例的生命周期、资源分配和负载均衡

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{Mutex, RwLock};
use tokio::time::{Duration, interval};
use tracing::{info, warn, error, debug};

use super::process::{SandboxHandle, SandboxConfig, ExecutionContext, ExecutionResult};
use super::Result;
use super::SandboxError;

/// 沙箱管理器配置
#[derive(Debug, Clone)]
pub struct ManagerConfig {
    /// 最小沙箱数量
    pub min_sandboxes: usize,
    /// 最大沙箱数量
    pub max_sandboxes: usize,
    /// 沙箱空闲超时 (秒)
    pub idle_timeout_secs: u64,
    /// 健康检查间隔 (秒)
    pub health_check_interval_secs: u64,
    /// 基础沙箱配置
    pub sandbox_config: SandboxConfig,
}

impl Default for ManagerConfig {
    fn default() -> Self {
        Self {
            min_sandboxes: 2,
            max_sandboxes: 10,
            idle_timeout_secs: 300,  // 5 分钟
            health_check_interval_secs: 30,
            sandbox_config: SandboxConfig::default(),
        }
    }
}

/// 沙箱管理器
pub struct SandboxManager {
    config: ManagerConfig,
    sandboxes: Arc<RwLock<HashMap<String, Arc<Mutex<SandboxHandle>>>>>,
    running: Arc<RwLock<bool>>,
    stats: Arc<RwLock<ManagerStats>>,
}

/// 管理器统计信息
#[derive(Debug, Default)]
pub struct ManagerStats {
    /// 总执行次数
    pub total_executions: u64,
    /// 成功执行次数
    pub successful_executions: u64,
    /// 失败执行次数
    pub failed_executions: u64,
    /// 平均执行时间 (毫秒)
    pub avg_execution_time_ms: f64,
    /// 当前活跃沙箱数
    pub active_sandboxes: usize,
    /// 沙箱启动次数
    pub sandbox_starts: u64,
    /// 沙箱停止次数
    pub sandbox_stops: u64,
}

impl SandboxManager {
    /// 创建新的沙箱管理器
    pub fn new(config: ManagerConfig) -> Self {
        Self {
            config,
            sandboxes: Arc::new(RwLock::new(HashMap::new())),
            running: Arc::new(RwLock::new(false)),
            stats: Arc::new(RwLock::new(ManagerStats::default())),
        }
    }

    /// 启动管理器
    pub async fn start(&self) -> Result<()> {
        let mut running = self.running.write().await;
        *running = true;

        // 预热沙箱
        self.warmup().await?;

        // 启动健康检查
        self.start_health_check();

        info!("SandboxManager started with {} sandboxes", self.config.min_sandboxes);
        Ok(())
    }

    /// 停止管理器
    pub async fn stop(&self) -> Result<()> {
        let mut running = self.running.write().await;
        *running = false;

        // 停止所有沙箱
        let mut sandboxes = self.sandboxes.write().await;
        for (_, sandbox) in sandboxes.iter_mut() {
            let mut handle = sandbox.lock().await;
            let _ = handle.stop();
        }
        sandboxes.clear();

        info!("SandboxManager stopped");
        Ok(())
    }

    /// 执行代码
    pub async fn execute(
        &self,
        code: &str,
        context: Option<ExecutionContext>,
    ) -> Result<ExecutionResult> {
        // 获取可用的沙箱
        let sandbox = self.get_available_sandbox().await?;
        
        let mut handle = sandbox.lock().await;
        
        // 执行
        let start = std::time::Instant::now();
        let result = handle.execute(code, &context.unwrap_or_default());
        let execution_time = start.elapsed().as_millis() as u64;

        // 更新统计
        self.update_stats(&result, execution_time).await;

        result
    }

    /// 获取可用的沙箱
    async fn get_available_sandbox(&self) -> Result<Arc<Mutex<SandboxHandle>>> {
        let sandboxes = self.sandboxes.read().await;

        // 查找活跃的沙箱
        for (_, sandbox) in sandboxes.iter() {
            let handle = sandbox.lock().await;
            if handle.is_alive() {
                return Ok(sandbox.clone());
            }
        }

        drop(sandboxes);

        // 如果没有可用的，创建新的
        if sandboxes.len() < self.config.max_sandboxes {
            self.create_sandbox().await
        } else {
            Err(SandboxError::ResourceLimit(
                "No available sandboxes and max limit reached".to_string()
            ))
        }
    }

    /// 创建新沙箱
    async fn create_sandbox(&self) -> Result<Arc<Mutex<SandboxHandle>>> {
        let id = format!("sandbox-{}", uuid::Uuid::new_v4());
        let mut handle = SandboxHandle::new(id.clone(), self.config.sandbox_config.clone());

        // 启动沙箱
        handle.start()?;

        let sandbox = Arc::new(Mutex::new(handle));

        // 添加到管理器
        let mut sandboxes = self.sandboxes.write().await;
        sandboxes.insert(id, sandbox.clone());

        // 更新统计
        let mut stats = self.stats.write().await;
        stats.sandbox_starts += 1;
        stats.active_sandboxes = sandboxes.len();

        info!("Created new sandbox: {}", id);
        Ok(sandbox)
    }

    /// 预热沙箱
    async fn warmup(&self) -> Result<()> {
        info!("Warming up {} sandboxes", self.config.min_sandboxes);

        for _ in 0..self.config.min_sandboxes {
            let _ = self.create_sandbox().await?;
        }

        Ok(())
    }

    /// 启动健康检查
    fn start_health_check(&self) {
        let sandboxes = self.sandboxes.clone();
        let running = self.running.clone();
        let interval_secs = self.config.health_check_interval_secs;
        let idle_timeout = self.config.idle_timeout_secs;

        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(interval_secs));
            
            loop {
                interval.tick().await;
                
                let is_running = *running.read().await;
                if !is_running {
                    break;
                }

                // 检查所有沙箱的健康状态
                let mut to_remove = Vec::new();
                {
                    let sandboxes_ref = sandboxes.read().await;
                    for (id, sandbox) in sandboxes_ref.iter() {
                        let handle = sandbox.lock().await;
                        
                        // 检查是否存活
                        if !handle.is_alive() {
                            warn!("Sandbox {} is not alive, marking for removal", id);
                            to_remove.push(id.clone());
                            continue;
                        }

                        // 检查是否空闲超时
                        let idle_time = handle.last_used.elapsed().as_secs();
                        let current_count = sandboxes_ref.len();
                        
                        if idle_time > idle_timeout && current_count > 2 {
                            warn!("Sandbox {} idle for {}s, marking for removal", id, idle_time);
                            to_remove.push(id.clone());
                        }
                    }
                }

                // 移除不健康的沙箱
                if !to_remove.is_empty() {
                    let mut sandboxes_ref = sandboxes.write().await;
                    for id in to_remove {
                        if let Some(sandbox) = sandboxes_ref.remove(&id) {
                            let mut handle = sandbox.lock().await;
                            let _ = handle.stop();
                            info!("Removed sandbox: {}", id);
                            
                            let mut stats = self.stats.write().await;
                            stats.sandbox_stops += 1;
                            stats.active_sandboxes = sandboxes_ref.len();
                        }
                    }
                }

                // 如果沙箱数量少于最小值，补充
                let current_count = sandboxes.read().await.len();
                if current_count < 2 {
                    drop(sandboxes.read().await);
                    // 这里可以调用 create_sandbox，但需要避免死锁
                }
            }
        });
    }

    /// 更新统计信息
    async fn update_stats(&self, result: &ExecutionResult, execution_time: u64) {
        let mut stats = self.stats.write().await;
        stats.total_executions += 1;

        if result.success {
            stats.successful_executions += 1;
        } else {
            stats.failed_executions += 1;
        }

        // 更新平均执行时间 (简单移动平均)
        let n = stats.total_executions as f64;
        stats.avg_execution_time_ms = 
            (stats.avg_execution_time_ms * (n - 1.0) + execution_time as f64) / n;
    }

    /// 获取统计信息
    pub async fn get_stats(&self) -> ManagerStats {
        self.stats.read().await.clone()
    }

    /// 获取沙箱数量
    pub async fn get_sandbox_count(&self) -> usize {
        self.sandboxes.read().await.len()
    }
}

impl Drop for SandboxManager {
    fn drop(&mut self) {
        // 异步停止可能在 drop 中无法完成，这里只做简单处理
        let runtime = tokio::runtime::Handle::try_current();
        if let Ok(rt) = runtime {
            rt.spawn(async move {
                let _ = self.stop().await;
            });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_manager_basic_operations() {
        let config = ManagerConfig::default();
        let manager = SandboxManager::new(config);

        // 启动管理器
        assert!(manager.start().await.is_ok());

        // 检查预热
        tokio::time::sleep(Duration::from_millis(100)).await;
        assert!(manager.get_sandbox_count().await >= 2);

        // 执行代码
        let result = manager.execute("x = 1 + 1\n_result = x", None).await;
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(result.success);

        // 获取统计
        let stats = manager.get_stats().await;
        assert!(stats.total_executions >= 1);

        // 停止管理器
        assert!(manager.stop().await.is_ok());
    }
}
