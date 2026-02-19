//! 可观测性服务
//! 
//! 整合OpenTelemetry追踪和Prometheus指标收集

use crate::observability::{init_tracer, SimpleMetrics, tracer::shutdown_tracer};
use std::error::Error;
use std::sync::Arc;

/// 可观测性服务配置
#[derive(Debug, Clone)]
pub struct ObservabilityConfig {
    pub service_name: String,
    pub otlp_endpoint: Option<String>,
    pub metrics_enabled: bool,
    pub tracing_enabled: bool,
}

impl Default for ObservabilityConfig {
    fn default() -> Self {
        Self {
            service_name: "neuroflow-kernel".to_string(),
            otlp_endpoint: Some("http://localhost:4317".to_string()),
            metrics_enabled: true,
            tracing_enabled: true,
        }
    }
}

/// 可观测性服务
pub struct ObservabilityService {
    pub metrics: Arc<SimpleMetrics>,
    config: ObservabilityConfig,
}

impl ObservabilityService {
    /// 创建新的可观测性服务
    pub fn new(config: ObservabilityConfig) -> Result<Self, Box<dyn Error>> {
        // 初始化追踪器
        if config.tracing_enabled {
            init_tracer(
                &config.service_name,
                config.otlp_endpoint.as_deref()
            )?;
        }
        
        // 初始化指标
        let metrics = Arc::new(SimpleMetrics::new());
        
        Ok(Self {
            metrics,
            config,
        })
    }
    
    /// 获取指标文本
    pub fn get_metrics_text(&self) -> Result<String, Box<dyn Error>> {
        Ok(self.metrics.gather_text())
    }
    
    /// 更新系统指标
    pub fn update_system_metrics(&self) -> Result<(), Box<dyn Error>> {
        // 模拟系统指标更新
        self.metrics.set_gauge("system_memory_usage_bytes", 1024.0 * 1024.0 * 100.0);
        self.metrics.set_gauge("system_cpu_usage_percent", 25.5);
        Ok(())
    }
    
    /// 关闭服务
    pub fn shutdown(&self) {
        if self.config.tracing_enabled {
            shutdown_tracer();
        }
        tracing::info!("Observability service shutdown completed");
    }
}

impl Drop for ObservabilityService {
    fn drop(&mut self) {
        self.shutdown();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_observability_service_metrics() {
        let config = ObservabilityConfig {
            service_name: "test-service".to_string(),
            otlp_endpoint: Some("http://localhost:4317".to_string()),
            metrics_enabled: true,
            tracing_enabled: false, // 避免全局追踪器冲突
        };
        
        let service = ObservabilityService::new(config).unwrap();
        
        // 测试指标收集
        service.metrics.inc_counter("neuroflow_http_requests_total");
        let metrics_text = service.get_metrics_text().unwrap();
        assert!(metrics_text.contains("neuroflow_http_requests_total"));
        
        // 测试系统指标更新
        service.update_system_metrics().unwrap();
        let metrics_text = service.get_metrics_text().unwrap();
        assert!(metrics_text.contains("system_memory_usage_bytes"));
    }

    #[tokio::test]
    async fn test_observability_service_drop() {
        let config = ObservabilityConfig {
            tracing_enabled: false, // 避免全局追踪器冲突
            ..Default::default()
        };
        let service = ObservabilityService::new(config).unwrap();
        
        // 服务会在drop时自动关闭
        drop(service);
        
        // 等待清理完成
        sleep(Duration::from_millis(100)).await;
    }

    #[tokio::test]
    async fn test_disabled_features() {
        let config = ObservabilityConfig {
            tracing_enabled: false,
            metrics_enabled: false,
            ..Default::default()
        };
        
        // 即使禁用功能，服务也应该能正常创建
        let service = ObservabilityService::new(config).unwrap();
        
        // 基本操作应该仍然工作
        service.metrics.inc_counter("test_counter");
        assert!(service.get_metrics_text().is_ok());
    }
}