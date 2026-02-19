//! 简化的可观测性实现
//! 
//! 提供基本的指标收集和日志功能

use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::time::Instant;

/// 简单的指标收集器
#[derive(Debug, Clone)]
pub struct SimpleMetrics {
    counters: Arc<Mutex<HashMap<String, i64>>>,
    gauges: Arc<Mutex<HashMap<String, f64>>>,
    histograms: Arc<Mutex<HashMap<String, Vec<f64>>>>,
}

impl SimpleMetrics {
    /// 创建新的指标收集器
    pub fn new() -> Self {
        Self {
            counters: Arc::new(Mutex::new(HashMap::new())),
            gauges: Arc::new(Mutex::new(HashMap::new())),
            histograms: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    /// 增加计数器
    pub fn inc_counter(&self, name: &str) {
        let mut counters = self.counters.lock().unwrap();
        let count = counters.entry(name.to_string()).or_insert(0);
        *count += 1;
    }
    
    /// 设置仪表值
    pub fn set_gauge(&self, name: &str, value: f64) {
        let mut gauges = self.gauges.lock().unwrap();
        gauges.insert(name.to_string(), value);
    }
    
    /// 记录直方图值
    pub fn observe_histogram(&self, name: &str, value: f64) {
        let mut histograms = self.histograms.lock().unwrap();
        let values = histograms.entry(name.to_string()).or_insert_with(Vec::new);
        values.push(value);
    }
    
    /// 获取计数器值
    pub fn get_counter(&self, name: &str) -> i64 {
        let counters = self.counters.lock().unwrap();
        *counters.get(name).unwrap_or(&0)
    }
    
    /// 获取仪表值
    pub fn get_gauge(&self, name: &str) -> f64 {
        let gauges = self.gauges.lock().unwrap();
        *gauges.get(name).unwrap_or(&0.0)
    }
    
    /// 获取直方图统计信息
    pub fn get_histogram_stats(&self, name: &str) -> Option<HistogramStats> {
        let histograms = self.histograms.lock().unwrap();
        histograms.get(name).map(|values| {
            if values.is_empty() {
                HistogramStats {
                    count: 0,
                    sum: 0.0,
                    avg: 0.0,
                    min: 0.0,
                    max: 0.0,
                }
            } else {
                let sum: f64 = values.iter().sum();
                let count = values.len() as f64;
                let min_val = values.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let max_val = values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
                HistogramStats {
                    count: values.len(),
                    sum,
                    avg: sum / count,
                    min: if min_val.is_finite() { min_val } else { 0.0 },
                    max: if max_val.is_finite() { max_val } else { 0.0 },
                }
            }
        })
    }
    
    /// 获取所有指标的文本表示
    pub fn gather_text(&self) -> String {
        let mut output = String::new();
        
        // 输出计数器
        let counters = self.counters.lock().unwrap();
        for (name, value) in counters.iter() {
            output.push_str(&format!("{} {}\n", name, value));
        }
        
        // 输出仪表
        let gauges = self.gauges.lock().unwrap();
        for (name, value) in gauges.iter() {
            output.push_str(&format!("{} {}\n", name, value));
        }
        
        // 输出直方图统计
        let histograms = self.histograms.lock().unwrap();
        for (name, values) in histograms.iter() {
            if let Some(stats) = self.get_histogram_stats(name) {
                output.push_str(&format!("{}_count {}\n", name, stats.count));
                output.push_str(&format!("{}_sum {}\n", name, stats.sum));
                output.push_str(&format!("{}_avg {}\n", name, stats.avg));
                output.push_str(&format!("{}_min {}\n", name, stats.min));
                output.push_str(&format!("{}_max {}\n", name, stats.max));
            }
        }
        
        output
    }
}

/// 直方图统计信息
#[derive(Debug, Clone)]
pub struct HistogramStats {
    pub count: usize,
    pub sum: f64,
    pub avg: f64,
    pub min: f64,
    pub max: f64,
}

/// 请求计时器
pub struct RequestTimer {
    start: Instant,
    metrics: SimpleMetrics,
    metric_name: String,
}

impl RequestTimer {
    pub fn new(metrics: SimpleMetrics, metric_name: String) -> Self {
        Self {
            start: Instant::now(),
            metrics,
            metric_name,
        }
    }
    
    pub fn observe_duration(self) {
        let duration = self.start.elapsed().as_secs_f64();
        self.metrics.observe_histogram(&self.metric_name, duration);
    }
}

impl Drop for RequestTimer {
    fn drop(&mut self) {
        if !std::thread::panicking() {
            let duration = self.start.elapsed().as_secs_f64();
            self.metrics.observe_histogram(&self.metric_name, duration);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_simple_metrics() {
        let metrics = SimpleMetrics::new();
        
        // 测试计数器
        metrics.inc_counter("test_counter");
        metrics.inc_counter("test_counter");
        assert_eq!(metrics.get_counter("test_counter"), 2);
        
        // 测试仪表
        metrics.set_gauge("test_gauge", 42.5);
        assert_eq!(metrics.get_gauge("test_gauge"), 42.5);
        
        // 测试直方图
        metrics.observe_histogram("test_histogram", 1.0);
        metrics.observe_histogram("test_histogram", 2.0);
        metrics.observe_histogram("test_histogram", 3.0);
        
        let stats = metrics.get_histogram_stats("test_histogram").unwrap();
        assert_eq!(stats.count, 3);
        assert_eq!(stats.sum, 6.0);
        assert_eq!(stats.avg, 2.0);
        assert_eq!(stats.min, 1.0);
        assert_eq!(stats.max, 3.0);
    }

    #[tokio::test]
    async fn test_request_timer() {
        let metrics = SimpleMetrics::new();
        
        {
            let _timer = RequestTimer::new(metrics.clone(), "test_timer".to_string());
            sleep(Duration::from_millis(10)).await;
        }
        
        let stats = metrics.get_histogram_stats("test_timer").unwrap();
        assert!(stats.count > 0);
        assert!(stats.avg > 0.0);
    }

    #[tokio::test]
    async fn test_metrics_text_output() {
        let metrics = SimpleMetrics::new();
        
        metrics.inc_counter("requests_total");
        metrics.set_gauge("memory_usage", 100.0);
        metrics.observe_histogram("request_duration", 0.1);
        
        let text_output = metrics.gather_text();
        assert!(text_output.contains("requests_total"));
        assert!(text_output.contains("memory_usage"));
        assert!(text_output.contains("request_duration_count"));
    }
}