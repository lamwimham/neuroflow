//! 长期稳定性测试模块
//! 
//! 用于验证NeuroFlow框架的7x24小时运行能力

use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tracing::{info, warn, error, debug};
use crate::utils::Result;

/// 稳定性测试配置
#[derive(Debug, Clone)]
pub struct StabilityTestConfig {
    pub test_duration_hours: u64,
    pub concurrent_requests: usize,
    pub request_interval_ms: u64,
    pub memory_monitor_interval_sec: u64,
    pub cpu_monitor_interval_sec: u64,
    pub checkpoint_interval_minutes: u64,
}

impl Default for StabilityTestConfig {
    fn default() -> Self {
        Self {
            test_duration_hours: 24, // 默认24小时测试
            concurrent_requests: 10, // 并发请求数
            request_interval_ms: 100, // 请求间隔
            memory_monitor_interval_sec: 30, // 内存监控间隔
            cpu_monitor_interval_sec: 30, // CPU监控间隔
            checkpoint_interval_minutes: 5, // 检查点间隔
        }
    }
}

/// 系统资源指标
#[derive(Debug, Clone)]
pub struct SystemMetrics {
    pub memory_usage_mb: f64,
    pub cpu_usage_percent: f64,
    pub uptime_minutes: u64,
    pub request_count: u64,
    pub error_count: u64,
    pub avg_response_time_ms: f64,
}

/// 稳定性测试结果
#[derive(Debug, Clone)]
pub struct StabilityTestResult {
    pub passed: bool,
    pub duration_hours: f64,
    pub total_requests: u64,
    pub successful_requests: u64,
    pub failed_requests: u64,
    pub avg_response_time_ms: f64,
    pub max_memory_usage_mb: f64,
    pub avg_cpu_usage_percent: f64,
    pub checkpoints: Vec<Checkpoint>,
    pub issues: Vec<String>,
}

/// 检查点
#[derive(Debug, Clone)]
pub struct Checkpoint {
    pub timestamp: std::time::SystemTime,
    pub elapsed_minutes: u64,
    pub request_count: u64,
    pub error_count: u64,
    pub memory_usage_mb: f64,
    pub cpu_usage_percent: f64,
    pub avg_response_time_ms: f64,
}

/// 稳定性测试器
pub struct StabilityTester {
    config: StabilityTestConfig,
    metrics: Arc<RwLock<SystemMetrics>>,
    start_time: std::time::SystemTime,
    test_completed: Arc<RwLock<bool>>,
}

impl StabilityTester {
    /// 创建新的稳定性测试器
    pub fn new(config: StabilityTestConfig) -> Self {
        Self {
            config,
            metrics: Arc::new(RwLock::new(SystemMetrics {
                memory_usage_mb: 0.0,
                cpu_usage_percent: 0.0,
                uptime_minutes: 0,
                request_count: 0,
                error_count: 0,
                avg_response_time_ms: 0.0,
            })),
            start_time: std::time::SystemTime::now(),
            test_completed: Arc::new(RwLock::new(false)),
        }
    }

    /// 运行长期稳定性测试
    pub async fn run_stability_test(&self) -> Result<StabilityTestResult> {
        info!("Starting stability test for {} hours", self.config.test_duration_hours);
        
        let end_time = self.start_time + Duration::from_secs(self.config.test_duration_hours * 3600);
        let test_completed = self.test_completed.clone();
        
        // 启动监控任务
        let metrics_clone = self.metrics.clone();
        let monitor_completed = test_completed.clone();
        let monitor_handle = tokio::spawn(async move {
            Self::run_monitoring(metrics_clone, monitor_completed).await;
        });
        
        // 启动请求生成任务
        let metrics_clone = self.metrics.clone();
        let request_completed = test_completed.clone();
        let request_config = self.config.clone();
        let request_handle = tokio::spawn(async move {
            Self::run_request_generation(metrics_clone, request_completed, request_config).await;
        });
        
        // 等待测试完成或超时
        let duration = Duration::from_secs(self.config.test_duration_hours * 3600 + 300); // 额外5分钟缓冲
        if tokio::time::timeout(duration, async {
            loop {
                tokio::time::sleep(Duration::from_secs(1)).await;
                let completed = test_completed.read().await.clone();
                if completed {
                    break;
                }
            }
        }).await.is_err() {
            warn!("Stability test timed out, forcing completion");
        }
        
        // 标记测试完成
        *self.test_completed.write().await = true;
        
        // 等待所有任务完成
        let _ = monitor_handle.await;
        let _ = request_handle.await;
        
        // 生成最终报告
        self.generate_final_report().await
    }

    /// 运行监控任务
    async fn run_monitoring(
        metrics: Arc<RwLock<SystemMetrics>>,
        test_completed: Arc<RwLock<bool>>,
    ) {
        loop {
            if *test_completed.read().await {
                break;
            }
            
            // 获取系统指标
            let sys_metrics = Self::get_system_metrics().await;
            
            // 更新指标
            {
                let mut metrics_write = metrics.write().await;
                metrics_write.memory_usage_mb = sys_metrics.memory_usage_mb;
                metrics_write.cpu_usage_percent = sys_metrics.cpu_usage_percent;
            }
            
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }

    /// 运行请求生成任务
    async fn run_request_generation(
        metrics: Arc<RwLock<SystemMetrics>>,
        test_completed: Arc<RwLock<bool>>,
        config: StabilityTestConfig,
    ) {
        let mut handles = Vec::new();
        
        // 启动并发请求任务
        for _ in 0..config.concurrent_requests {
            let metrics_clone = metrics.clone();
            let completed_clone = test_completed.clone();
            let interval = Duration::from_millis(config.request_interval_ms);
            
            let handle = tokio::spawn(async move {
                loop {
                    if *completed_clone.read().await {
                        break;
                    }
                    
                    let start = Instant::now();
                    
                    // 模拟请求处理
                    let request_success = Self::simulate_request().await;
                    
                    let duration = start.elapsed().as_millis() as f64;
                    
                    // 更新指标
                    {
                        let mut metrics_write = metrics_write.lock().await;
                        metrics_write.request_count += 1;
                        
                        if !request_success {
                            metrics_write.error_count += 1;
                        }
                        
                        // 更新平均响应时间
                        let total_requests = metrics_write.request_count;
                        let old_avg = metrics_write.avg_response_time_ms;
                        metrics_write.avg_response_time_ms = 
                            (old_avg * (total_requests - 1) as f64 + duration) / total_requests as f64;
                    }
                    
                    tokio::time::sleep(interval).await;
                }
            });
            
            handles.push(handle);
        }
        
        // 等待所有任务完成
        for handle in handles {
            let _ = handle.await;
        }
    }

    /// 模拟请求处理
    async fn simulate_request() -> bool {
        // 模拟不同类型的请求处理
        match rand::random::<u8>() % 4 {
            0 => {
                // 成功的请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 50 + 10)).await;
                true
            }
            1 => {
                // 较慢的请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 200 + 50)).await;
                true
            }
            2 => {
                // 偶尔的错误
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 50 + 10)).await;
                false
            }
            _ => {
                // 正常速度请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 100 + 20)).await;
                true
            }
        }
    }

    /// 获取系统指标
    async fn get_system_metrics() -> SystemMetrics {
        // 这里我们会集成实际的系统监控
        // 为了演示，我们使用模拟值
        SystemMetrics {
            memory_usage_mb: (rand::random::<f64>() * 100.0 + 100.0).round(), // 100-200 MB
            cpu_usage_percent: (rand::random::<f64>() * 20.0).round(), // 0-20%
            uptime_minutes: (std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() / 60) as u64,
            request_count: 0, // 这些会在请求处理中更新
            error_count: 0,
            avg_response_time_ms: 0.0,
        }
    }

    /// 生成最终报告
    async fn generate_final_report(&self) -> Result<StabilityTestResult> {
        let metrics = self.metrics.read().await.clone();
        let duration = std::time::SystemTime::now()
            .duration_since(self.start_time)
            .unwrap()
            .as_secs_f64() / 3600.0; // 转换为小时
        
        let result = StabilityTestResult {
            passed: metrics.error_count == 0 && metrics.memory_usage_mb < 1000.0, // 假设小于1GB为通过
            duration_hours: duration,
            total_requests: metrics.request_count,
            successful_requests: metrics.request_count - metrics.error_count,
            failed_requests: metrics.error_count,
            avg_response_time_ms: metrics.avg_response_time_ms,
            max_memory_usage_mb: metrics.memory_usage_mb, // 实际实现中应跟踪最大值
            avg_cpu_usage_percent: metrics.cpu_usage_percent, // 实际实现中应计算平均值
            checkpoints: vec![], // 实际实现中应收集检查点
            issues: if metrics.error_count > 0 {
                vec![format!("{} requests failed during test", metrics.error_count)]
            } else {
                vec![]
            },
        };
        
        Ok(result)
    }
}

/// 增强的稳定性测试器，具有更全面的监控功能
pub struct EnhancedStabilityTester {
    config: StabilityTestConfig,
    metrics_history: Arc<RwLock<Vec<SystemMetrics>>>,
    start_time: std::time::SystemTime,
    test_completed: Arc<RwLock<bool>>,
    checkpoints: Arc<RwLock<Vec<Checkpoint>>>,
}

impl EnhancedStabilityTester {
    /// 创建增强的稳定性测试器
    pub fn new(config: StabilityTestConfig) -> Self {
        Self {
            config,
            metrics_history: Arc::new(RwLock::new(Vec::new())),
            start_time: std::time::SystemTime::now(),
            test_completed: Arc::new(RwLock::new(false)),
            checkpoints: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// 运行增强的长期稳定性测试
    pub async fn run_enhanced_stability_test(&self) -> Result<StabilityTestResult> {
        info!("Starting enhanced stability test for {} hours", self.config.test_duration_hours);
        
        // 启动系统监控
        let metrics_history = self.metrics_history.clone();
        let test_completed = self.test_completed.clone();
        let monitor_handle = tokio::spawn(async move {
            Self::continuous_monitoring(metrics_history, test_completed).await;
        });
        
        // 启动检查点记录
        let checkpoints = self.checkpoints.clone();
        let metrics_history = self.metrics_history.clone();
        let test_completed = self.test_completed.clone();
        let checkpoint_interval = self.config.checkpoint_interval_minutes;
        let checkpoint_handle = tokio::spawn(async move {
            Self::record_checkpoints(checkpoints, metrics_history, test_completed, checkpoint_interval).await;
        });
        
        // 启动负载生成
        let config = self.config.clone();
        let test_completed = self.test_completed.clone();
        let load_handle = tokio::spawn(async move {
            Self::generate_load(config, test_completed).await;
        });
        
        // 等待测试完成
        let duration = Duration::from_secs(self.config.test_duration_hours * 3600 + 600); // 额外10分钟缓冲
        tokio::time::timeout(duration, async {
            loop {
                tokio::time::sleep(Duration::from_secs(1)).await;
                if *self.test_completed.read().await {
                    break;
                }
            }
        }).await.map_err(|_| crate::utils::NeuroFlowError::Timeout("Stability test timed out".to_string()))?;
        
        // 标记测试完成并等待所有任务结束
        *self.test_completed.write().await = true;
        
        let _ = tokio::time::timeout(Duration::from_secs(30), monitor_handle).await;
        let _ = tokio::time::timeout(Duration::from_secs(30), checkpoint_handle).await;
        let _ = tokio::time::timeout(Duration::from_secs(30), load_handle).await;
        
        // 生成最终报告
        self.generate_enhanced_report().await
    }

    /// 持续系统监控
    async fn continuous_monitoring(
        metrics_history: Arc<RwLock<Vec<SystemMetrics>>>,
        test_completed: Arc<RwLock<bool>>,
    ) {
        use sysinfo::{System, SystemExt, CpuExt, NetworkExt, DiskExt};
        
        let mut system = System::new_all();
        
        loop {
            if *test_completed.read().await {
                break;
            }
            
            system.refresh_all();
            
            let metrics = SystemMetrics {
                memory_usage_mb: (system.used_memory() as f64) / (1024.0 * 1024.0),
                cpu_usage_percent: system.global_cpu_info().cpu_usage() as f64,
                uptime_minutes: (std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs() / 60) as u64,
                request_count: 0, // 这将在负载生成中更新
                error_count: 0,
                avg_response_time_ms: 0.0,
            };
            
            {
                let mut history = metrics_history.write().await;
                history.push(metrics);
                
                // 限制历史记录大小以避免内存耗尽
                if history.len() > 10000 {
                    history.drain(0..history.len()-5000);
                }
            }
            
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }

    /// 记录检查点
    async fn record_checkpoints(
        checkpoints: Arc<RwLock<Vec<Checkpoint>>>,
        metrics_history: Arc<RwLock<Vec<SystemMetrics>>>,
        test_completed: Arc<RwLock<bool>>,
        interval_minutes: u64,
    ) {
        loop {
            if *test_completed.read().await {
                break;
            }
            
            tokio::time::sleep(Duration::from_secs(interval_minutes * 60)).await;
            
            let history = metrics_history.read().await;
            if !history.is_empty() {
                let latest = history.last().unwrap();
                
                let checkpoint = Checkpoint {
                    timestamp: std::time::SystemTime::now(),
                    elapsed_minutes: (std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap()
                        .as_secs() / 60) as u64,
                    request_count: latest.request_count,
                    error_count: latest.error_count,
                    memory_usage_mb: latest.memory_usage_mb,
                    cpu_usage_percent: latest.cpu_usage_percent,
                    avg_response_time_ms: latest.avg_response_time_ms,
                };
                
                {
                    let mut checkpoints_write = checkpoints.write().await;
                    checkpoints_write.push(checkpoint);
                }
            }
        }
    }

    /// 生成负载
    async fn generate_load(
        config: StabilityTestConfig,
        test_completed: Arc<RwLock<bool>>,
    ) {
        use tokio::sync::Mutex;
        
        let stats = Arc::new(Mutex::new((
            0u64, // request_count
            0u64, // error_count
            0f64, // total_response_time
        )));
        
        let mut handles = Vec::new();
        
        // 启动并发请求任务
        for _ in 0..config.concurrent_requests {
            let stats_clone = stats.clone();
            let completed_clone = test_completed.clone();
            let interval = Duration::from_millis(config.request_interval_ms);
            
            let handle = tokio::spawn(async move {
                loop {
                    if *completed_clone.read().await {
                        break;
                    }
                    
                    let start = Instant::now();
                    
                    // 模拟请求处理
                    let request_success = Self::simulate_request().await;
                    let duration = start.elapsed().as_millis() as f64;
                    
                    // 更新统计信息
                    {
                        let mut stats_guard = stats_clone.lock().await;
                        stats_guard.0 += 1; // request_count
                        if !request_success {
                            stats_guard.1 += 1; // error_count
                        }
                        stats_guard.2 += duration; // total_response_time
                    }
                    
                    tokio::time::sleep(interval).await;
                }
            });
            
            handles.push(handle);
        }
        
        // 等待所有任务完成
        for handle in handles {
            let _ = handle.await;
        }
    }

    /// 模拟请求处理
    async fn simulate_request() -> bool {
        // 模拟不同类型的请求处理
        match rand::random::<u8>() % 5 {
            0 => {
                // 快速成功请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 20 + 5)).await;
                true
            }
            1 => {
                // 中等速度成功请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 100 + 20)).await;
                true
            }
            2 => {
                // 较慢的成功请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 300 + 100)).await;
                true
            }
            3 => {
                // 偶尔的失败请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 50 + 10)).await;
                false
            }
            _ => {
                // 正常速度请求
                tokio::time::sleep(Duration::from_millis(rand::random::<u64>() % 150 + 30)).await;
                true
            }
        }
    }

    /// 生成增强报告
    async fn generate_enhanced_report(&self) -> Result<StabilityTestResult> {
        let history = self.metrics_history.read().await;
        let checkpoints = self.checkpoints.read().await.clone();
        
        if history.is_empty() {
            return Err(crate::utils::NeuroFlowError::InternalError("No metrics collected during test".to_string()));
        }
        
        // 计算统计数据
        let max_memory = history.iter().map(|m| m.memory_usage_mb).fold(0.0, f64::max);
        let avg_cpu = history.iter().map(|m| m.cpu_usage_percent).sum::<f64>() / history.len() as f64;
        let duration = std::time::SystemTime::now()
            .duration_since(self.start_time)
            .unwrap()
            .as_secs_f64() / 3600.0;
        
        // 使用最后的指标作为近似值（在真实实现中，这些值应该在负载生成过程中更新）
        let last_metrics = history.last().unwrap();
        let total_requests = last_metrics.request_count;
        let error_count = last_metrics.error_count;
        
        let result = StabilityTestResult {
            passed: error_count == 0 && max_memory < 1000.0, // 假设小于1GB为通过且无错误
            duration_hours: duration,
            total_requests,
            successful_requests: total_requests - error_count,
            failed_requests: error_count,
            avg_response_time_ms: last_metrics.avg_response_time_ms,
            max_memory_usage_mb: max_memory,
            avg_cpu_usage_percent: avg_cpu,
            checkpoints,
            issues: if error_count > 0 {
                vec![format!("{} requests failed during test", error_count)]
            } else if max_memory > 500.0 {
                vec![format!("Peak memory usage {:.2}MB exceeded threshold", max_memory)]
            } else {
                vec![]
            },
        };
        
        Ok(result)
    }
}

/// 打印稳定性测试报告
pub fn print_stability_report(result: &StabilityTestResult) {
    println!("\n🧪 Stability Test Report");
    println!("========================");
    println!("Duration: {:.2} hours", result.duration_hours);
    println!("Total Requests: {}", result.total_requests);
    println!("Successful Requests: {}", result.successful_requests);
    println!("Failed Requests: {}", result.failed_requests);
    println!("Success Rate: {:.2}%", 
             if result.total_requests > 0 { 
                 (result.successful_requests as f64 / result.total_requests as f64) * 100.0 
             } else { 100.0 });
    println!("Avg Response Time: {:.2} ms", result.avg_response_time_ms);
    println!("Max Memory Usage: {:.2} MB", result.max_memory_usage_mb);
    println!("Avg CPU Usage: {:.2}%", result.avg_cpu_usage_percent);
    println!("Passed: {}", if result.passed { "✅ YES" } else { "❌ NO" });
    
    if !result.issues.is_empty() {
        println!("\n⚠️ Issues Found:");
        for issue in &result.issues {
            println!("  - {}", issue);
        }
    }
    
    if !result.checkpoints.is_empty() {
        println!("\n📈 Checkpoints (first and last):");
        if let Some(first) = result.checkpoints.first() {
            println!("  First: {:.2}MB memory, {:.2}% CPU at {} min", 
                     first.memory_usage_mb, first.cpu_usage_percent, first.elapsed_minutes);
        }
        if let Some(last) = result.checkpoints.last() {
            println!("  Last:  {:.2}MB memory, {:.2}% CPU at {} min", 
                     last.memory_usage_mb, last.cpu_usage_percent, last.elapsed_minutes);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_stability_tester_creation() {
        let config = StabilityTestConfig {
            test_duration_hours: 1,
            concurrent_requests: 2,
            request_interval_ms: 1000,
            ..Default::default()
        };
        
        let tester = EnhancedStabilityTester::new(config);
        assert_eq!(tester.config.test_duration_hours, 1);
        assert_eq!(tester.config.concurrent_requests, 2);
    }

    #[tokio::test]
    async fn test_system_metrics_collection() {
        // 这个测试需要实际的系统信息库，所以只测试结构
        let metrics = SystemMetrics {
            memory_usage_mb: 100.0,
            cpu_usage_percent: 5.0,
            uptime_minutes: 10,
            request_count: 100,
            error_count: 0,
            avg_response_time_ms: 10.0,
        };
        
        assert_eq!(metrics.memory_usage_mb, 100.0);
        assert_eq!(metrics.cpu_usage_percent, 5.0);
    }
}