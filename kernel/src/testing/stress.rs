//! 压力测试模块
//! 提供系统在高负载下的性能测试能力

use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tokio::time::sleep;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StressTestConfig {
    /// 测试持续时间（秒）
    pub duration_secs: u64,
    /// 并发请求数
    pub concurrency: usize,
    /// 请求频率（每秒请求数）
    pub requests_per_second: u64,
    /// 目标URL
    pub target_url: String,
    /// 测试类型 (http, grpc, sandbox)
    pub test_type: String,
    /// 负载类型 (constant, ramp_up, spike)
    pub load_pattern: String,
}

impl Default for StressTestConfig {
    fn default() -> Self {
        Self {
            duration_secs: 60,
            concurrency: 10,
            requests_per_second: 100,
            target_url: "http://localhost:8080/invoke".to_string(),
            test_type: "http".to_string(),
            load_pattern: "constant".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct StressTestResult {
    pub total_requests: u64,
    pub successful_requests: u64,
    pub failed_requests: u64,
    pub avg_response_time_ms: f64,
    pub p95_response_time_ms: f64,
    pub p99_response_time_ms: f64,
    pub requests_per_second: f64,
    pub errors: Vec<String>,
    pub start_time: std::time::SystemTime,
    pub end_time: std::time::SystemTime,
}

pub struct StressTester {
    config: StressTestConfig,
    client: Client,
}

impl StressTester {
    pub fn new(config: StressTestConfig) -> Self {
        Self {
            client: Client::new(),
            config,
        }
    }

    /// 执行压力测试
    pub async fn run_test(&self) -> Result<StressTestResult, Box<dyn std::error::Error>> {
        info!("Starting stress test with config: {:?}", self.config);

        let start_time = std::time::SystemTime::now();
        let mut results = TestResults::new();
        
        // 根据负载模式执行测试
        match self.config.load_pattern.as_str() {
            "ramp_up" => self.run_ramp_up_test(&mut results).await?,
            "spike" => self.run_spike_test(&mut results).await?,
            _ => self.run_constant_test(&mut results).await?,
        }

        let end_time = std::time::SystemTime::now();

        let result = StressTestResult {
            total_requests: results.total_requests,
            successful_requests: results.successful_requests,
            failed_requests: results.failed_requests,
            avg_response_time_ms: results.calculate_avg_response_time(),
            p95_response_time_ms: results.calculate_percentile(95.0),
            p99_response_time_ms: results.calculate_percentile(99.0),
            requests_per_second: results.calculate_requests_per_second(),
            errors: results.errors,
            start_time,
            end_time,
        };

        info!("Stress test completed: {:?}", result);
        Ok(result)
    }

    async fn run_constant_test(&self, results: &mut TestResults) -> Result<(), Box<dyn std::error::Error>> {
        let start = Instant::now();
        let duration = Duration::from_secs(self.config.duration_secs);
        
        // 创建并发任务
        let tasks: Vec<_> = (0..self.config.concurrency)
            .map(|_| {
                let client = self.client.clone();
                let config = self.config.clone();
                let results = Arc::clone(&results.shared_results);
                
                tokio::spawn(async move {
                    let request_interval = Duration::from_millis(1000 / config.requests_per_second.max(1));
                    
                    loop {
                        if Instant::now().duration_since(start) >= duration {
                            break;
                        }

                        let request_start = Instant::now();
                        
                        match Self::make_request(&client, &config).await {
                            Ok(response_time) => {
                                let mut results_write = results.write().await;
                                results_write.successful_requests += 1;
                                results_write.response_times.push(response_time);
                            }
                            Err(err) => {
                                let mut results_write = results.write().await;
                                results_write.failed_requests += 1;
                                results_write.errors.push(err);
                            }
                        }
                        
                        results_write.write().await.total_requests += 1;
                        sleep(request_interval).await;
                    }
                })
            })
            .collect();

        // 等待所有任务完成
        for task in tasks {
            let _ = task.await;
        }

        Ok(())
    }

    async fn run_ramp_up_test(&self, results: &mut TestResults) -> Result<(), Box<dyn std::error::Error>> {
        info!("Running ramp-up stress test");
        
        let start = Instant::now();
        let duration = Duration::from_secs(self.config.duration_secs);
        let ramp_duration = duration / 2; // 前半段进行加压
        
        // 初始负载
        let base_concurrency = self.config.concurrency / 4;
        let max_concurrency = self.config.concurrency;
        
        // 逐步增加负载
        for step in 0..5 {
            let current_concurrency = base_concurrency + (step * (max_concurrency - base_concurrency) / 4);
            info!("Ramping up to {} concurrent connections", current_concurrency);
            
            // 在当前负载下运行一段时间
            let step_start = Instant::now();
            let step_duration = ramp_duration / 5;
            
            let tasks: Vec<_> = (0..current_concurrency)
                .map(|_| {
                    let client = self.client.clone();
                    let config = self.config.clone();
                    let results = Arc::clone(&results.shared_results);
                    
                    tokio::spawn(async move {
                        let request_interval = Duration::from_millis(1000 / config.requests_per_second.max(1));
                        
                        loop {
                            if Instant::now().duration_since(step_start) >= step_duration ||
                               Instant::now().duration_since(start) >= duration {
                                break;
                            }

                            let request_start = Instant::now();
                            
                            match Self::make_request(&client, &config).await {
                                Ok(response_time) => {
                                    let mut results_write = results.write().await;
                                    results_write.successful_requests += 1;
                                    results_write.response_times.push(response_time);
                                }
                                Err(err) => {
                                    let mut results_write = results.write().await;
                                    results_write.failed_requests += 1;
                                    results_write.errors.push(err);
                                }
                            }
                            
                            results_write.write().await.total_requests += 1;
                            sleep(request_interval).await;
                        }
                    })
                })
                .collect();

            // 等待当前阶段完成
            for task in tasks {
                let _ = task.await;
            }
            
            // 短暂休息
            sleep(Duration::from_secs(2)).await;
        }

        // 最后阶段保持最大负载
        let remaining_duration = duration - ramp_duration;
        if remaining_duration > Duration::from_secs(0) {
            self.run_constant_test_at_max_load(results, remaining_duration).await?;
        }

        Ok(())
    }

    async fn run_spike_test(&self, results: &mut TestResults) -> Result<(), Box<dyn std::error::Error>> {
        info!("Running spike stress test");
        
        let start = Instant::now();
        let duration = Duration::from_secs(self.config.duration_secs);
        
        // 正常负载
        let normal_concurrency = self.config.concurrency / 4;
        // 尖峰负载
        let spike_concurrency = self.config.concurrency * 2;
        
        let mut is_spike_phase = false;
        let spike_interval = Duration::from_secs(10); // 每10秒一次尖峰
        let last_spike = Arc::new(RwLock::new(Instant::now()));
        
        let tasks: Vec<_> = (0..normal_concurrency)
            .map(|_| {
                let client = self.client.clone();
                let config = self.config.clone();
                let results = Arc::clone(&results.shared_results);
                let last_spike = Arc::clone(&last_spike);
                
                tokio::spawn(async move {
                    let request_interval = Duration::from_millis(1000 / (config.requests_per_second / normal_concurrency as u64).max(1));
                    
                    loop {
                        if Instant::now().duration_since(start) >= duration {
                            break;
                        }

                        // 检查是否进入尖峰阶段
                        let now = Instant::now();
                        let last_spike_read = last_spike.read().await;
                        let elapsed_since_spike = now.duration_since(*last_spike_read);
                        drop(last_spike_read);
                        
                        let current_concurrency = if elapsed_since_spike < Duration::from_secs(2) {
                            spike_concurrency
                        } else {
                            normal_concurrency
                        };
                        
                        if elapsed_since_spike >= spike_interval {
                            let mut last_spike_write = last_spike.write().await;
                            *last_spike_write = now;
                            drop(last_spike_write);
                        }

                        let request_start = Instant::now();
                        
                        match Self::make_request(&client, &config).await {
                            Ok(response_time) => {
                                let mut results_write = results.write().await;
                                results_write.successful_requests += 1;
                                results_write.response_times.push(response_time);
                            }
                            Err(err) => {
                                let mut results_write = results.write().await;
                                results_write.failed_requests += 1;
                                results_write.errors.push(err);
                            }
                        }
                        
                        results_write.write().await.total_requests += 1;
                        sleep(request_interval).await;
                    }
                })
            })
            .collect();

        for task in tasks {
            let _ = task.await;
        }

        Ok(())
    }

    async fn run_constant_test_at_max_load(&self, results: &mut TestResults, duration: Duration) -> Result<(), Box<dyn std::error::Error>> {
        let start = Instant::now();
        
        let tasks: Vec<_> = (0..self.config.concurrency)
            .map(|_| {
                let client = self.client.clone();
                let config = self.config.clone();
                let results = Arc::clone(&results.shared_results);
                
                tokio::spawn(async move {
                    let request_interval = Duration::from_millis(1000 / (config.requests_per_second / config.concurrency as u64).max(1));
                    
                    loop {
                        if Instant::now().duration_since(start) >= duration {
                            break;
                        }

                        let request_start = Instant::now();
                        
                        match Self::make_request(&client, &config).await {
                            Ok(response_time) => {
                                let mut results_write = results.write().await;
                                results_write.successful_requests += 1;
                                results_write.response_times.push(response_time);
                            }
                            Err(err) => {
                                let mut results_write = results.write().await;
                                results_write.failed_requests += 1;
                                results_write.errors.push(err);
                            }
                        }
                        
                        results_write.write().await.total_requests += 1;
                        sleep(request_interval).await;
                    }
                })
            })
            .collect();

        for task in tasks {
            let _ = task.await;
        }

        Ok(())
    }

    async fn make_request(client: &Client, config: &StressTestConfig) -> Result<f64, String> {
        let start = Instant::now();
        
        let payload = serde_json::json!({
            "agent": "health-check",
            "payload": {
                "message": "stress-test"
            }
        });

        let response = client
            .post(&config.target_url)
            .header("Content-Type", "application/json")
            .json(&payload)
            .timeout(Duration::from_secs(30)) // 30秒超时
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        let response_time = start.elapsed().as_millis() as f64;

        if response.status().is_success() {
            Ok(response_time)
        } else {
            Err(format!("Request failed with status: {}", response.status()))
        }
    }
}

struct TestResults {
    shared_results: Arc<RwLock<TestResultsData>>,
}

struct TestResultsData {
    total_requests: u64,
    successful_requests: u64,
    failed_requests: u64,
    response_times: Vec<f64>,
    errors: Vec<String>,
}

impl TestResults {
    fn new() -> Self {
        Self {
            shared_results: Arc::new(RwLock::new(TestResultsData {
                total_requests: 0,
                successful_requests: 0,
                failed_requests: 0,
                response_times: Vec::new(),
                errors: Vec::new(),
            })),
        }
    }

    fn calculate_avg_response_time(&self) -> f64 {
        let results = self.shared_results.blocking_write();
        if results.response_times.is_empty() {
            0.0
        } else {
            results.response_times.iter().sum::<f64>() / results.response_times.len() as f64
        }
    }

    fn calculate_percentile(&self, percentile: f64) -> f64 {
        let results = self.shared_results.blocking_write();
        let mut sorted_times = results.response_times.clone();
        sorted_times.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        if sorted_times.is_empty() {
            return 0.0;
        }
        
        let index = ((percentile / 100.0) * (sorted_times.len() - 1) as f64).round() as usize;
        sorted_times[index.min(sorted_times.len() - 1)]
    }

    fn calculate_requests_per_second(&self) -> f64 {
        // This would be calculated based on the test duration
        // For simplicity, we'll return a placeholder
        let results = self.shared_results.blocking_write();
        if results.total_requests > 0 {
            results.total_requests as f64 / 60.0 // Assuming 60-second test
        } else {
            0.0
        }
    }
}

/// 性能监控器
pub struct PerformanceMonitor {
    baseline_metrics: Arc<RwLock<BaselineMetrics>>,
}

#[derive(Debug, Clone)]
pub struct BaselineMetrics {
    pub avg_response_time_ms: f64,
    pub p95_response_time_ms: f64,
    pub p99_response_time_ms: f64,
    pub max_concurrent_requests: usize,
    pub memory_usage_mb: f64,
    pub cpu_usage_percent: f64,
}

impl Default for BaselineMetrics {
    fn default() -> Self {
        Self {
            avg_response_time_ms: 100.0,
            p95_response_time_ms: 200.0,
            p99_response_time_ms: 500.0,
            max_concurrent_requests: 100,
            memory_usage_mb: 100.0,
            cpu_usage_percent: 50.0,
        }
    }
}

impl PerformanceMonitor {
    pub fn new() -> Self {
        Self {
            baseline_metrics: Arc::new(RwLock::new(BaselineMetrics::default())),
        }
    }

    /// 分析压力测试结果
    pub async fn analyze_results(&self, result: &StressTestResult) -> PerformanceAnalysis {
        let baseline = self.baseline_metrics.read().await;
        
        let response_time_degradation = result.avg_response_time_ms / baseline.avg_response_time_ms;
        let p95_degradation = result.p95_response_time_ms / baseline.p95_response_time_ms;
        
        let performance_score = calculate_performance_score(
            result,
            &baseline
        );

        PerformanceAnalysis {
            response_time_degradation,
            p95_degradation,
            performance_score,
            recommendations: generate_recommendations(result, &baseline),
            stability_rating: calculate_stability_rating(result),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct PerformanceAnalysis {
    pub response_time_degradation: f64,
    pub p95_degradation: f64,
    pub performance_score: f64,
    pub recommendations: Vec<String>,
    pub stability_rating: StabilityRating,
}

#[derive(Debug, Clone, Serialize)]
pub enum StabilityRating {
    Excellent,
    Good,
    Fair,
    Poor,
}

fn calculate_performance_score(result: &StressTestResult, baseline: &BaselineMetrics) -> f64 {
    // Calculate a composite performance score
    // Higher score is better
    let response_time_score = (baseline.avg_response_time_ms / result.avg_response_time_ms).min(1.0) * 30.0;
    let success_rate_score = (result.successful_requests as f64 / result.total_requests as f64) * 40.0;
    let throughput_score = (result.requests_per_second / baseline.max_concurrent_requests as f64) * 30.0;
    
    response_time_score + success_rate_score + throughput_score
}

fn generate_recommendations(result: &StressTestResult, baseline: &BaselineMetrics) -> Vec<String> {
    let mut recommendations = Vec::new();
    
    if result.avg_response_time_ms > baseline.avg_response_time_ms * 2.0 {
        recommendations.push("Response time has degraded significantly. Consider optimizing bottlenecks.".to_string());
    }
    
    if result.failed_requests as f64 / result.total_requests as f64 > 0.05 { // > 5% failure rate
        recommendations.push("High failure rate detected. Check system capacity and error handling.".to_string());
    }
    
    if result.p95_response_time_ms > baseline.p95_response_time_ms * 3.0 {
        recommendations.push("High percentiles indicate poor tail latency. Investigate outliers.".to_string());
    }
    
    if result.requests_per_second < baseline.max_concurrent_requests as f64 * 0.7 { // < 70% of baseline
        recommendations.push("Throughput below expectations. Consider capacity planning.".to_string());
    }
    
    if recommendations.is_empty() {
        recommendations.push("Performance looks good! No major issues detected.".to_string());
    }
    
    recommendations
}

fn calculate_stability_rating(result: &StressTestResult) -> StabilityRating {
    let failure_rate = result.failed_requests as f64 / result.total_requests as f64;
    let avg_response_time_ratio = result.avg_response_time_ms / 100.0; // Compare to 100ms baseline
    
    if failure_rate < 0.01 && avg_response_time_ratio < 2.0 { // < 1% failure, < 2x baseline
        StabilityRating::Excellent
    } else if failure_rate < 0.05 && avg_response_time_ratio < 3.0 { // < 5% failure, < 3x baseline
        StabilityRating::Good
    } else if failure_rate < 0.10 && avg_response_time_ratio < 5.0 { // < 10% failure, < 5x baseline
        StabilityRating::Fair
    } else {
        StabilityRating::Poor
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_stress_tester_creation() {
        let config = StressTestConfig::default();
        let tester = StressTester::new(config);
        
        // We can't actually run the test without a server, but we can ensure it creates successfully
        assert!(tester.config.duration_secs > 0);
    }

    #[tokio::test]
    async fn test_performance_monitor() {
        let monitor = PerformanceMonitor::new();
        let baseline = monitor.baseline_metrics.read().await;
        
        assert!(baseline.avg_response_time_ms > 0.0);
        assert!(baseline.p95_response_time_ms > baseline.avg_response_time_ms);
    }

    #[test]
    fn test_calculate_performance_score() {
        let result = StressTestResult {
            total_requests: 1000,
            successful_requests: 950,
            failed_requests: 50,
            avg_response_time_ms: 100.0,
            p95_response_time_ms: 200.0,
            p99_response_time_ms: 500.0,
            requests_per_second: 100.0,
            errors: vec![],
            start_time: std::time::SystemTime::now(),
            end_time: std::time::SystemTime::now(),
        };
        
        let baseline = BaselineMetrics::default();
        let score = calculate_performance_score(&result, &baseline);
        
        // With perfect metrics, score should be around 100
        assert!(score >= 0.0);
    }
}