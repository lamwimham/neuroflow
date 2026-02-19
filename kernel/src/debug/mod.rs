//! 调试模式模块
//! 提供详细日志、性能分析、诊断工具等功能

use std::collections::HashMap;
use std::time::Instant;
use tokio::sync::RwLock;
use tracing::{debug, info, warn, error, Level, event};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use std::fmt::Debug;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DebugConfig {
    /// 是否启用详细调试日志
    pub verbose_logs: bool,
    /// 是否启用性能分析
    pub profiling_enabled: bool,
    /// 是否启用内存分析
    pub memory_profiling: bool,
    /// 是否启用网络流量分析
    pub network_analysis: bool,
    /// 调试端点端口
    pub debug_port: u16,
    /// 性能采样间隔（毫秒）
    pub sampling_interval_ms: u64,
}

impl Default for DebugConfig {
    fn default() -> Self {
        Self {
            verbose_logs: false,
            profiling_enabled: false,
            memory_profiling: false,
            network_analysis: false,
            debug_port: 9090,
            sampling_interval_ms: 1000,
        }
    }
}

/// 性能分析器
pub struct Profiler {
    start_time: Instant,
    checkpoints: RwLock<HashMap<String, Instant>>,
    metrics: Arc<RwLock<HashMap<String, Vec<f64>>>>,
}

impl Profiler {
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            checkpoints: RwLock::new(HashMap::new()),
            metrics: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start_timer(&self, name: &str) {
        let mut checkpoints = self.checkpoints.write().await;
        checkpoints.insert(name.to_string(), Instant::now());
        debug!("Timer '{}' started", name);
    }

    pub async fn stop_timer(&self, name: &str) -> Option<f64> {
        let mut checkpoints = self.checkpoints.write().await;
        if let Some(start_time) = checkpoints.remove(name) {
            let elapsed = start_time.elapsed().as_micros() as f64 / 1000.0; // Convert to milliseconds
            debug!("Timer '{}' stopped: {:.2}ms", name, elapsed);

            // Record metric
            let mut metrics = self.metrics.write().await;
            metrics.entry(name.to_string()).or_insert_with(Vec::new).push(elapsed);
            
            Some(elapsed)
        } else {
            error!("Timer '{}' not found", name);
            None
        }
    }

    pub async fn record_metric(&self, name: &str, value: f64) {
        let mut metrics = self.metrics.write().await;
        metrics.entry(name.to_string()).or_insert_with(Vec::new).push(value);
        debug!("Metric recorded: {} = {}", name, value);
    }

    pub async fn get_metrics(&self) -> HashMap<String, Vec<f64>> {
        self.metrics.read().await.clone()
    }

    pub async fn get_statistics(&self) -> HashMap<String, MetricStats> {
        let metrics = self.metrics.read().await;
        let mut stats = HashMap::new();
        
        for (name, values) in metrics.iter() {
            if !values.is_empty() {
                let sum: f64 = values.iter().sum();
                let avg = sum / values.len() as f64;
                let min = values.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let max = values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
                
                stats.insert(name.clone(), MetricStats {
                    count: values.len(),
                    average: avg,
                    min,
                    max,
                    total: sum,
                });
            }
        }
        
        stats
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct MetricStats {
    pub count: usize,
    pub average: f64,
    pub min: f64,
    pub max: f64,
    pub total: f64,
}

/// 内存分析器
pub struct MemoryProfiler {
    allocations: RwLock<Vec<AllocationRecord>>,
}

#[derive(Debug, Clone, Serialize)]
pub struct AllocationRecord {
    pub timestamp: std::time::SystemTime,
    pub size: usize,
    pub location: String,
}

impl MemoryProfiler {
    pub fn new() -> Self {
        Self {
            allocations: RwLock::new(Vec::new()),
        }
    }

    pub async fn record_allocation(&self, size: usize, location: &str) {
        let mut allocations = self.allocations.write().await;
        allocations.push(AllocationRecord {
            timestamp: std::time::SystemTime::now(),
            size,
            location: location.to_string(),
        });
        
        debug!("Memory allocation: {} bytes at {}", size, location);
    }

    pub async fn get_allocations(&self) -> Vec<AllocationRecord> {
        self.allocations.read().await.clone()
    }

    pub async fn get_total_allocated(&self) -> usize {
        self.allocations.read().await.iter()
            .map(|record| record.size)
            .sum()
    }
}

/// 调试会话管理器
pub struct DebugSession {
    pub config: DebugConfig,
    pub profiler: Arc<Profiler>,
    pub memory_profiler: Arc<MemoryProfiler>,
    pub events: Arc<RwLock<Vec<DebugEvent>>>,
}

#[derive(Debug, Clone, Serialize)]
pub struct DebugEvent {
    pub timestamp: std::time::SystemTime,
    pub level: Level,
    pub message: String,
    pub metadata: HashMap<String, String>,
}

impl DebugSession {
    pub fn new(config: DebugConfig) -> Self {
        Self {
            profiler: Arc::new(Profiler::new()),
            memory_profiler: Arc::new(MemoryProfiler::new()),
            events: Arc::new(RwLock::new(Vec::new())),
            config,
        }
    }

    pub async fn log_event(&self, level: Level, message: String, metadata: HashMap<String, String>) {
        let mut events = self.events.write().await;
        events.push(DebugEvent {
            timestamp: std::time::SystemTime::now(),
            level,
            message,
            metadata,
        });

        // Also log to tracing
        match level {
            Level::TRACE | Level::DEBUG => debug!("{}", message),
            Level::INFO => info!("{}", message),
            Level::WARN => warn!("{}", message),
            Level::ERROR => error!("{}", message),
        }
    }

    pub async fn get_recent_events(&self, count: usize) -> Vec<DebugEvent> {
        let events = self.events.read().await;
        events.iter()
            .rev()
            .take(count)
            .cloned()
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect()
    }

    pub async fn get_system_health(&self) -> SystemHealth {
        SystemHealth {
            uptime_ms: self.profiler.start_time.elapsed().as_millis() as u64,
            total_events: self.events.read().await.len(),
            total_allocated: self.memory_profiler.get_total_allocated().await,
            active_timers: self.profiler.checkpoints.read().await.len(),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct SystemHealth {
    pub uptime_ms: u64,
    pub total_events: usize,
    pub total_allocated: usize,
    pub active_timers: usize,
}

/// 调试工具集
pub struct DebugTools {
    pub session: Arc<DebugSession>,
}

impl DebugTools {
    pub fn new(config: DebugConfig) -> Self {
        Self {
            session: Arc::new(DebugSession::new(config)),
        }
    }

    /// 启动调试服务器
    pub async fn start_debug_server(&self) -> Result<(), Box<dyn std::error::Error>> {
        if !self.session.config.network_analysis {
            info!("Debug server not enabled (network_analysis disabled)");
            return Ok(());
        }

        info!("Starting debug server on port {}", self.session.config.debug_port);
        
        // 这里可以启动一个简单的HTTP服务器来提供调试信息
        // 为了简化，我们只打印信息
        println!("🐛 Debug server would start on http://localhost:{}", self.session.config.debug_port);
        println!("📊 Metrics endpoint: http://localhost:{}/metrics", self.session.config.debug_port);
        println!("🔍 Trace endpoint: http://localhost:{}/trace", self.session.config.debug_port);
        
        Ok(())
    }

    /// 记录性能分析数据
    pub async fn profile_block<T, F, Fut>(&self, name: &str, block: F) -> T
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = T>,
    {
        if self.session.config.profiling_enabled {
            self.session.profiler.start_timer(name).await;
            let result = block().await;
            self.session.profiler.stop_timer(name).await;
            result
        } else {
            block().await
        }
    }

    /// 记录内存分配
    pub async fn record_allocation(&self, size: usize, location: &str) {
        if self.session.config.memory_profiling {
            self.session.memory_profiler.record_allocation(size, location).await;
        }
    }

    /// 获取性能统计
    pub async fn get_performance_stats(&self) -> HashMap<String, MetricStats> {
        self.session.profiler.get_statistics().await
    }

    /// 获取内存使用情况
    pub async fn get_memory_stats(&self) -> Vec<AllocationRecord> {
        self.session.memory_profiler.get_allocations().await
    }

    /// 获取系统健康状况
    pub async fn get_health(&self) -> SystemHealth {
        self.session.get_system_health().await
    }
}

impl Default for DebugTools {
    fn default() -> Self {
        Self::new(DebugConfig::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_profiler() {
        let profiler = Profiler::new();
        
        profiler.start_timer("test_operation").await;
        tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        profiler.stop_timer("test_operation").await;
        
        let stats = profiler.get_statistics().await;
        assert!(stats.contains_key("test_operation"));
        
        let metrics = profiler.get_metrics().await;
        assert!(metrics.contains_key("test_operation"));
    }

    #[tokio::test]
    async fn test_memory_profiler() {
        let memory_profiler = MemoryProfiler::new();
        
        memory_profiler.record_allocation(1024, "test_location").await;
        memory_profiler.record_allocation(2048, "another_location").await;
        
        let total = memory_profiler.get_total_allocated().await;
        assert_eq!(total, 1024 + 2048);
        
        let allocations = memory_profiler.get_allocations().await;
        assert_eq!(allocations.len(), 2);
    }

    #[tokio::test]
    async fn test_debug_session() {
        let config = DebugConfig {
            verbose_logs: true,
            profiling_enabled: true,
            ..Default::default()
        };
        
        let session = DebugSession::new(config);
        
        let mut metadata = HashMap::new();
        metadata.insert("test".to_string(), "value".to_string());
        session.log_event(Level::INFO, "Test message".to_string(), metadata).await;
        
        let recent_events = session.get_recent_events(10).await;
        assert_eq!(recent_events.len(), 1);
        assert_eq!(recent_events[0].message, "Test message");
    }
}