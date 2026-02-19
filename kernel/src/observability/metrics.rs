//! Prometheus指标收集实现

use prometheus::{
    Counter, Histogram, IntCounter, IntGauge, Registry, TextEncoder, Encoder,
    HistogramOpts, Opts
};
use std::sync::Arc;
use std::error::Error;

/// 核心指标集合
pub struct Metrics {
    // HTTP请求相关指标
    pub http_requests_total: IntCounter,
    pub http_request_duration_seconds: Histogram,
    pub http_requests_in_flight: IntGauge,
    pub http_response_sizes_bytes: Histogram,
    
    // WASM沙箱相关指标
    pub wasm_active_sandboxes: IntGauge,
    pub wasm_sandbox_creation_total: IntCounter,
    pub wasm_sandbox_creation_duration_seconds: Histogram,
    pub wasm_sandbox_errors_total: IntCounter,
    
    // 系统资源指标
    pub system_memory_usage_bytes: IntGauge,
    pub system_cpu_usage_percent: Gauge,
    
    // 业务指标
    pub agent_invocations_total: IntCounter,
    pub agent_invocation_duration_seconds: Histogram,
    pub agent_errors_total: IntCounter,
    
    // 注册表
    pub registry: Arc<Registry>,
}

impl Metrics {
    /// 创建新的指标集合
    pub fn new() -> Result<Self, Box<dyn Error>> {
        let registry = Arc::new(Registry::new());
        
        // HTTP请求指标
        let http_requests_total = IntCounter::new(
            "neuroflow_http_requests_total",
            "Total number of HTTP requests"
        )?;
        
        let http_request_duration_opts = HistogramOpts::new(
            "neuroflow_http_request_duration_seconds",
            "HTTP request duration in seconds"
        ).buckets(prometheus::exponential_buckets(0.0005, 2.0, 20)?);
        let http_request_duration_seconds = Histogram::with_opts(http_request_duration_opts)?;
        
        let http_requests_in_flight = IntGauge::new(
            "neuroflow_http_requests_in_flight",
            "Number of HTTP requests currently being processed"
        )?;
        
        let http_response_sizes_opts = HistogramOpts::new(
            "neuroflow_http_response_sizes_bytes",
            "HTTP response sizes in bytes"
        ).buckets(prometheus::exponential_buckets(100.0, 2.0, 15)?);
        let http_response_sizes_bytes = Histogram::with_opts(http_response_sizes_opts)?;
        
        // WASM沙箱指标
        let wasm_active_sandboxes = IntGauge::new(
            "neuroflow_wasm_active_sandboxes",
            "Number of active WASM sandboxes"
        )?;
        
        let wasm_sandbox_creation_total = IntCounter::new(
            "neuroflow_wasm_sandbox_creation_total",
            "Total number of WASM sandbox creations"
        )?;
        
        let wasm_sandbox_creation_opts = HistogramOpts::new(
            "neuroflow_wasm_sandbox_creation_duration_seconds",
            "WASM sandbox creation duration in seconds"
        ).buckets(prometheus::exponential_buckets(0.001, 2.0, 15)?);
        let wasm_sandbox_creation_duration_seconds = Histogram::with_opts(wasm_sandbox_creation_opts)?;
        
        let wasm_sandbox_errors_total = IntCounter::new(
            "neuroflow_wasm_sandbox_errors_total",
            "Total number of WASM sandbox errors"
        )?;
        
        // 系统资源指标
        let system_memory_usage_bytes = IntGauge::new(
            "neuroflow_system_memory_usage_bytes",
            "System memory usage in bytes"
        )?;
        
        let system_cpu_usage_opts = Opts::new(
            "neuroflow_system_cpu_usage_percent",
            "System CPU usage percentage"
        );
        let system_cpu_usage_percent = Gauge::new(system_cpu_usage_opts)?;
        
        // 业务指标
        let agent_invocations_total = IntCounter::new(
            "neuroflow_agent_invocations_total",
            "Total number of agent invocations"
        )?;
        
        let agent_invocation_opts = HistogramOpts::new(
            "neuroflow_agent_invocation_duration_seconds",
            "Agent invocation duration in seconds"
        ).buckets(prometheus::exponential_buckets(0.001, 2.0, 15)?);
        let agent_invocation_duration_seconds = Histogram::with_opts(agent_invocation_opts)?;
        
        let agent_errors_total = IntCounter::new(
            "neuroflow_agent_errors_total",
            "Total number of agent errors"
        )?;
        
        // 注册所有指标
        registry.register(Box::new(http_requests_total.clone()))?;
        registry.register(Box::new(http_request_duration_seconds.clone()))?;
        registry.register(Box::new(http_requests_in_flight.clone()))?;
        registry.register(Box::new(http_response_sizes_bytes.clone()))?;
        registry.register(Box::new(wasm_active_sandboxes.clone()))?;
        registry.register(Box::new(wasm_sandbox_creation_total.clone()))?;
        registry.register(Box::new(wasm_sandbox_creation_duration_seconds.clone()))?;
        registry.register(Box::new(wasm_sandbox_errors_total.clone()))?;
        registry.register(Box::new(system_memory_usage_bytes.clone()))?;
        registry.register(Box::new(system_cpu_usage_percent.clone()))?;
        registry.register(Box::new(agent_invocations_total.clone()))?;
        registry.register(Box::new(agent_invocation_duration_seconds.clone()))?;
        registry.register(Box::new(agent_errors_total.clone()))?;
        
        Ok(Metrics {
            http_requests_total,
            http_request_duration_seconds,
            http_requests_in_flight,
            http_response_sizes_bytes,
            wasm_active_sandboxes,
            wasm_sandbox_creation_total,
            wasm_sandbox_creation_duration_seconds,
            wasm_sandbox_errors_total,
            system_memory_usage_bytes,
            system_cpu_usage_percent,
            agent_invocations_total,
            agent_invocation_duration_seconds,
            agent_errors_total,
            registry,
        })
    }
    
    /// 获取指标文本格式
    pub fn gather_text(&self) -> Result<String, Box<dyn Error>> {
        let mut buffer = Vec::new();
        let encoder = TextEncoder::new();
        let metric_families = self.registry.gather();
        encoder.encode(&metric_families, &mut buffer)?;
        Ok(String::from_utf8(buffer)?)
    }
    
    /// 更新系统资源指标
    pub fn update_system_metrics(&self) -> Result<(), Box<dyn Error>> {
        // 获取内存使用情况
        if let Ok(memory) = self.get_memory_usage() {
            self.system_memory_usage_bytes.set(memory as i64);
        }
        
        // 获取CPU使用率
        if let Ok(cpu) = self.get_cpu_usage() {
            self.system_cpu_usage_percent.set(cpu);
        }
        
        Ok(())
    }
    
    /// 获取内存使用量（字节）
    fn get_memory_usage(&self) -> Result<u64, Box<dyn Error>> {
        // 在实际实现中，这里会调用系统API获取内存使用情况
        // 这里返回模拟数据用于演示
        Ok(1024 * 1024 * 100) // 100MB
    }
    
    /// 获取CPU使用率（百分比）
    fn get_cpu_usage(&self) -> Result<f64, Box<dyn Error>> {
        // 在实际实现中，这里会调用系统API获取CPU使用率
        // 这里返回模拟数据用于演示
        Ok(25.5)
    }
}

// 为Gauge实现必要的trait（prometheus crate中的Gauge）
use prometheus::core::{Collector, Desc};
use std::collections::HashMap;

pub struct Gauge {
    opts: Opts,
    desc: Desc,
    value: std::sync::Mutex<f64>,
}

impl Gauge {
    pub fn new(opts: Opts) -> Result<Self, Box<dyn Error>> {
        let desc = Desc::new(opts.clone())?;
        Ok(Gauge {
            opts,
            desc,
            value: std::sync::Mutex::new(0.0),
        })
    }
    
    pub fn set(&self, val: f64) {
        *self.value.lock().unwrap() = val;
    }
    
    pub fn get(&self) -> f64 {
        *self.value.lock().unwrap()
    }
}

impl Collector for Gauge {
    fn desc(&self) -> Vec<&Desc> {
        vec![&self.desc]
    }
    
    fn collect(&self) -> Vec<prometheus::proto::MetricFamily> {
        let mut m = prometheus::proto::MetricFamily::default();
        m.set_name(self.opts.name.clone());
        m.set_help(self.opts.help.clone());
        m.set_field_type(prometheus::proto::MetricType::GAUGE);
        
        let mut metric = prometheus::proto::Metric::default();
        let mut gauge = prometheus::proto::Gauge::default();
        gauge.set_value(self.get());
        metric.set_gauge(gauge);
        // 简化实现，避免protobuf依赖问题
        // 在实际生产环境中应该正确实现这个方法
        
        vec![m]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_metrics_creation() {
        let metrics = Metrics::new().unwrap();
        
        // 测试基本指标操作
        metrics.http_requests_total.inc();
        metrics.http_requests_in_flight.inc();
        
        let timer = metrics.http_request_duration_seconds.start_timer();
        sleep(Duration::from_millis(10)).await;
        timer.observe_duration();
        
        metrics.http_requests_in_flight.dec();
        
        // 验证指标收集
        let text_output = metrics.gather_text().unwrap();
        assert!(text_output.contains("neuroflow_http_requests_total"));
        assert!(text_output.contains("neuroflow_http_request_duration_seconds"));
    }

    #[tokio::test]
    async fn test_system_metrics() {
        let metrics = Metrics::new().unwrap();
        
        // 更新系统指标
        metrics.update_system_metrics().unwrap();
        
        let text_output = metrics.gather_text().unwrap();
        assert!(text_output.contains("neuroflow_system_memory_usage_bytes"));
        assert!(text_output.contains("neuroflow_system_cpu_usage_percent"));
    }

    #[tokio::test]
    async fn test_wasm_metrics() {
        let metrics = Metrics::new().unwrap();
        
        // 模拟WASM沙箱操作
        metrics.wasm_sandbox_creation_total.inc();
        metrics.wasm_active_sandboxes.inc();
        
        let timer = metrics.wasm_sandbox_creation_duration_seconds.start_timer();
        sleep(Duration::from_millis(5)).await;
        timer.observe_duration();
        
        metrics.wasm_active_sandboxes.dec();
        
        let text_output = metrics.gather_text().unwrap();
        assert!(text_output.contains("neuroflow_wasm_active_sandboxes"));
        assert!(text_output.contains("neuroflow_wasm_sandbox_creation_total"));
    }
}