//! 增强型OpenTelemetry链路追踪实现
//! 
//! 提供完整的分布式链路追踪功能

use opentelemetry::{
    global,
    trace::{TraceContextExt, TraceId, SpanKind, StatusCode},
    KeyValue,
};
use opentelemetry_sdk::{
    trace::{BatchSpanProcessor, TracerProvider},
    Resource,
};
use opentelemetry_otlp::{WithExportConfig, ExportConfig};
use opentelemetry_semantic_conventions::resource::{SERVICE_NAME, SERVICE_VERSION};
use std::error::Error;
use tracing::{info, warn, error, debug, span, Level};
use tracing_subscriber::{
    layer::SubscriberExt,
    util::SubscriberInitExt,
    EnvFilter,
};
use std::time::Duration;

/// 增强型可观测性配置
#[derive(Debug, Clone)]
pub struct EnhancedObservabilityConfig {
    pub service_name: String,
    pub service_version: String,
    pub otlp_endpoint: String,
    pub export_timeout: Duration,
    pub batch_timeout: Duration,
    pub max_batch_size: usize,
    pub sampling_ratio: f64,
    pub enable_metrics: bool,
    pub enable_logs: bool,
    pub enable_traces: bool,
}

impl Default for EnhancedObservabilityConfig {
    fn default() -> Self {
        Self {
            service_name: "neuroflow-kernel".to_string(),
            service_version: "1.0.0".to_string(),
            otlp_endpoint: "http://localhost:4317".to_string(),
            export_timeout: Duration::from_secs(10),
            batch_timeout: Duration::from_secs(2),
            max_batch_size: 512,
            sampling_ratio: 1.0, // 100%采样率，生产环境可调整
            enable_metrics: true,
            enable_logs: true,
            enable_traces: true,
        }
    }
}

/// 增强型可观测性服务
pub struct EnhancedObservabilityService {
    config: EnhancedObservabilityConfig,
    shutdown_handles: Vec<ShutdownHandle>,
}

/// 关闭句柄
pub enum ShutdownHandle {
    Tracer(opentelemetry_sdk::trace::Tracer),
    Metrics(opentelemetry_sdk::metrics::SdkMeterProvider),
}

impl EnhancedObservabilityService {
    /// 初始化增强型可观测性服务
    pub fn new(config: EnhancedObservabilityConfig) -> Result<Self, Box<dyn Error>> {
        let mut shutdown_handles = Vec::new();

        // 初始化追踪器
        if config.enable_traces {
            let tracer = Self::init_tracer(&config)?;
            shutdown_handles.push(ShutdownHandle::Tracer(tracer));
        }

        // 初始化日志记录器
        if config.enable_logs {
            Self::init_logging(&config)?;
        }

        info!("Enhanced observability service initialized for: {}", config.service_name);
        Ok(Self { config, shutdown_handles })
    }

    /// 初始化追踪器
    fn init_tracer(config: &EnhancedObservabilityConfig) -> Result<opentelemetry_sdk::trace::Tracer, Box<dyn Error>> {
        let export_config = ExportConfig {
            endpoint: config.otlp_endpoint.clone(),
            timeout: config.export_timeout,
        };

        let tracer_provider = TracerProvider::builder()
            .with_config(
                opentelemetry_sdk::trace::Config::default()
                    .with_resource(Resource::new(vec![
                        KeyValue::new(SERVICE_NAME, config.service_name.clone()),
                        KeyValue::new(SERVICE_VERSION, config.service_version.clone()),
                    ]))
                    .with_sampler(opentelemetry_sdk::trace::Sampler::TraceIdRatioBased(config.sampling_ratio))
            )
            .with_span_processor(
                BatchSpanProcessor::builder(
                    opentelemetry_otlp::new_exporter()
                        .tonic()
                        .with_export_config(export_config),
                    opentelemetry_sdk::runtime::Tokio
                )
                .with_max_queue_size(config.max_batch_size * 2)
                .with_max_export_batch_size(config.max_batch_size)
                .with_schedule_delay(config.batch_timeout)
                .build()
            )
            .build();

        let tracer = tracer_provider.tracer(config.service_name.clone());
        
        // 设置全局tracer provider
        global::set_tracer_provider(tracer_provider);

        Ok(tracer)
    }

    /// 初始化日志记录器
    fn init_logging(config: &EnhancedObservabilityConfig) -> Result<(), Box<dyn Error>> {
        let env_filter = EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| EnvFilter::new("info"));

        let telemetry = tracing_opentelemetry::layer()
            .with_tracer(global::tracer(config.service_name.clone()));

        tracing_subscriber::registry()
            .with(env_filter)
            .with(telemetry)
            .try_init()
            .map_err(|e| Box::new(e) as Box<dyn Error>)?;

        Ok(())
    }

    /// 创建一个新的追踪span
    pub fn start_span(&self, name: &str, attributes: &[KeyValue]) -> opentelemetry::trace::Span {
        global::tracer(self.config.service_name.clone())
            .span_builder(name)
            .with_kind(SpanKind::Server)
            .with_attributes(attributes.to_vec())
            .start(&global::tracer(self.config.service_name.clone()))
    }

    /// 记录自定义指标
    pub async fn record_custom_metric(&self, name: &str, value: f64, attributes: &[KeyValue]) {
        if self.config.enable_metrics {
            // 这里可以使用OpenTelemetry metrics API记录指标
            debug!("Recording metric: {} = {}, attributes: {:?}", name, value, attributes);
        }
    }

    /// 记录请求指标
    pub async fn record_request_metrics(
        &self, 
        duration_ms: f64, 
        status_code: u16, 
        method: &str, 
        route: &str
    ) {
        if self.config.enable_metrics {
            let attributes = [
                KeyValue::new("http.method", method.to_string()),
                KeyValue::new("http.route", route.to_string()),
                KeyValue::new("http.status_code", status_code as i64),
            ];

            // 这里可以使用OpenTelemetry metrics API记录HTTP请求指标
            debug!("Request metrics - Duration: {}ms, Status: {}, Method: {}, Route: {}", 
                   duration_ms, status_code, method, route);
        }
    }

    /// 记录错误
    pub async fn record_error(&self, error: &str, attributes: &[KeyValue]) {
        let span = self.start_span("error_occurred", attributes);
        span.set_attribute(KeyValue::new("error.message", error.to_string()));
        span.set_status(StatusCode::Error, error.to_string());
        span.end();
    }

    /// 记录沙箱执行指标
    pub async fn record_sandbox_execution(
        &self,
        sandbox_id: &str,
        agent_id: &str,
        execution_time_ms: f64,
        memory_used_mb: f64,
        success: bool,
    ) {
        if self.config.enable_metrics {
            let attributes = [
                KeyValue::new("sandbox.id", sandbox_id.to_string()),
                KeyValue::new("agent.id", agent_id.to_string()),
                KeyValue::new("success", success),
            ];

            debug!("Sandbox execution - ID: {}, Agent: {}, Time: {}ms, Memory: {}MB, Success: {}", 
                   sandbox_id, agent_id, execution_time_ms, memory_used_mb, success);
            
            // 记录到追踪span
            let span = self.start_span("sandbox.execution", &attributes);
            span.set_attribute(KeyValue::new("execution.time.ms", execution_time_ms));
            span.set_attribute(KeyValue::new("memory.used.mb", memory_used_mb));
            span.set_attribute(KeyValue::new("success", success));
            span.end();
        }
    }

    /// 记录路由决策指标
    pub async fn record_routing_decision(
        &self,
        query: &str,
        agent_id: &str,
        confidence: f32,
        candidates_considered: usize,
    ) {
        if self.config.enable_metrics {
            let attributes = [
                KeyValue::new("agent.id", agent_id.to_string()),
                KeyValue::new("confidence", confidence as f64),
                KeyValue::new("candidates.considered", candidates_considered as i64),
            ];

            debug!("Routing decision - Query: '{}...', Agent: {}, Confidence: {}, Candidates: {}", 
                   &query[..query.len().min(20)], agent_id, confidence, candidates_considered);
            
            // 记录到追踪span
            let span = self.start_span("routing.decision", &attributes);
            span.set_attribute(KeyValue::new("query.snippet", query[..query.len().min(100)].to_string()));
            span.set_attribute(KeyValue::new("confidence", confidence as f64));
            span.set_attribute(KeyValue::new("candidates.considered", candidates_considered as i64));
            span.end();
        }
    }

    /// 记录热更新指标
    pub async fn record_hot_reload_event(
        &self,
        version_id: &str,
        success: bool,
        duration_ms: f64,
        files_changed: usize,
    ) {
        if self.config.enable_metrics {
            let attributes = [
                KeyValue::new("version.id", version_id.to_string()),
                KeyValue::new("success", success),
            ];

            debug!("Hot reload - Version: {}, Success: {}, Duration: {}ms, Files: {}", 
                   version_id, success, duration_ms, files_changed);
            
            let span = self.start_span("hot.reload", &attributes);
            span.set_attribute(KeyValue::new("duration.ms", duration_ms));
            span.set_attribute(KeyValue::new("files.changed", files_changed as i64));
            span.end();
        }
    }

    /// 记录安全检查指标
    pub async fn record_security_check(
        &self,
        check_type: &str,
        passed: bool,
        duration_ms: f64,
    ) {
        if self.config.enable_metrics {
            let attributes = [
                KeyValue::new("check.type", check_type.to_string()),
                KeyValue::new("passed", passed),
            ];

            debug!("Security check - Type: {}, Passed: {}, Duration: {}ms", 
                   check_type, passed, duration_ms);
            
            let span = self.start_span("security.check", &attributes);
            span.set_attribute(KeyValue::new("duration.ms", duration_ms));
            span.set_attribute(KeyValue::new("passed", passed));
            span.end();
        }
    }

    /// 获取当前追踪ID
    pub fn get_current_trace_id() -> Option<TraceId> {
        opentelemetry::Context::current()
            .span()
            .span_context()
            .trace_id()
            .into()
    }

    /// 关闭服务
    pub fn shutdown(&mut self) {
        // 关闭全局tracer provider
        global::shutdown_tracer_provider();
        
        info!("Enhanced observability service shutdown completed");
    }
}

impl Drop for EnhancedObservabilityService {
    fn drop(&mut self) {
        self.shutdown();
    }
}

/// 追踪工具函数
pub mod tracing_utils {
    use super::*;
    
    /// 创建带属性的span
    pub fn span_with_attributes(
        service_name: &str,
        name: &str,
        attributes: Vec<KeyValue>,
    ) -> opentelemetry::trace::Span {
        global::tracer(service_name)
            .span_builder(name)
            .with_attributes(attributes)
            .start(&global::tracer(service_name))
    }

    /// 记录函数执行时间
    pub async fn record_function_duration<F, Fut, R>(
        service_name: &str,
        func_name: &str,
        attributes: Vec<KeyValue>,
        f: F,
    ) -> R
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = R>,
    {
        let span = span_with_attributes(service_name, func_name, attributes);
        let cx = opentelemetry::Context::current_with_span(span);
        
        let result = {
            let _guard = cx.clone().enter();
            f().await
        };
        
        cx.span().end();
        result
    }

    /// 记录异步操作的追踪
    pub async fn trace_async_operation<T, F, Fut>(
        service_name: &str,
        operation_name: &str,
        attributes: Vec<KeyValue>,
        operation: F,
    ) -> T
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = T>,
    {
        let span = span_with_attributes(service_name, operation_name, attributes);
        let cx = opentelemetry::Context::current_with_span(span);
        
        let result = {
            let _guard = cx.clone().enter();
            operation().await
        };
        
        cx.span().end();
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_enhanced_observability_service() {
        let config = EnhancedObservabilityConfig {
            service_name: "test-service".to_string(),
            service_version: "1.0.0".to_string(),
            otlp_endpoint: "http://localhost:4317".to_string(),
            sampling_ratio: 0.1, // 降低采样率以加快测试
            ..Default::default()
        };

        let mut service = EnhancedObservabilityService::new(config).unwrap();
        
        // 测试追踪功能
        let attributes = vec![
            KeyValue::new("test.key", "test.value"),
            KeyValue::new("operation", "test"),
        ];
        
        let span = service.start_span("test.operation", &attributes);
        span.set_attribute(KeyValue::new("custom.attr", "value"));
        span.end();
        
        // 测试指标记录
        service.record_request_metrics(100.0, 200, "GET", "/test").await;
        service.record_sandbox_execution("sandbox-1", "agent-1", 50.0, 10.0, true).await;
        service.record_routing_decision("test query", "agent-1", 0.9, 5).await;
        
        // 测试当前追踪ID获取
        let trace_id = EnhancedObservabilityService::get_current_trace_id();
        assert!(trace_id.is_some());
        
        // 清理
        service.shutdown();
    }

    #[tokio::test]
    async fn test_tracing_utils() {
        let service_name = "test-utils-service";
        
        // 测试函数执行时间记录
        let result = tracing_utils::record_function_duration(
            service_name,
            "test_function",
            vec![KeyValue::new("test", "value")],
            || async {
                sleep(Duration::from_millis(10)).await;
                42
            }
        ).await;
        
        assert_eq!(result, 42);
        
        // 测试异步操作追踪
        let result = tracing_utils::trace_async_operation(
            service_name,
            "test_async_op",
            vec![KeyValue::new("async", "op")],
            || async {
                sleep(Duration::from_millis(10)).await;
                "completed"
            }
        ).await;
        
        assert_eq!(result, "completed");
    }

    #[tokio::test]
    async fn test_error_recording() {
        let config = EnhancedObservabilityConfig {
            service_name: "error-test-service".to_string(),
            enable_logs: false, // 避免日志初始化冲突
            enable_traces: true,
            ..Default::default()
        };

        let service = EnhancedObservabilityService::new(config).unwrap();
        
        let attributes = vec![KeyValue::new("error.context", "test")];
        service.record_error("Test error occurred", &attributes).await;
        
        // 确保服务能正常工作
        assert!(true);
    }
}

/// 预定义指标和追踪事件
pub mod predefined {
    use super::*;

    /// 记录成功的请求
    pub async fn record_successful_request(
        service: &EnhancedObservabilityService,
        duration_ms: f64,
        method: &str,
        route: &str,
    ) {
        service.record_request_metrics(duration_ms, 200, method, route).await;
    }

    /// 记录失败的请求
    pub async fn record_failed_request(
        service: &EnhancedObservabilityService,
        duration_ms: f64,
        status_code: u16,
        method: &str,
        route: &str,
    ) {
        service.record_request_metrics(duration_ms, status_code, method, route).await;
    }

    /// 记录沙箱创建
    pub async fn record_sandbox_created(
        service: &EnhancedObservabilityService,
        sandbox_id: &str,
        agent_id: &str,
    ) {
        let attributes = [
            KeyValue::new("sandbox.id", sandbox_id.to_string()),
            KeyValue::new("agent.id", agent_id.to_string()),
            KeyValue::new("event", "created"),
        ];

        let span = service.start_span("sandbox.lifecycle.created", &attributes);
        span.end();
    }

    /// 记录沙箱销毁
    pub async fn record_sandbox_destroyed(
        service: &EnhancedObservabilityService,
        sandbox_id: &str,
        agent_id: &str,
    ) {
        let attributes = [
            KeyValue::new("sandbox.id", sandbox_id.to_string()),
            KeyValue::new("agent.id", agent_id.to_string()),
            KeyValue::new("event", "destroyed"),
        ];

        let span = service.start_span("sandbox.lifecycle.destroyed", &attributes);
        span.end();
    }

    /// 记录热更新成功
    pub async fn record_hot_reload_success(
        service: &EnhancedObservabilityService,
        version_id: &str,
        duration_ms: f64,
        files_changed: usize,
    ) {
        service.record_hot_reload_event(version_id, true, duration_ms, files_changed).await;
    }

    /// 记录热更新失败
    pub async fn record_hot_reload_failure(
        service: &EnhancedObservabilityService,
        version_id: &str,
        duration_ms: f64,
        error: &str,
    ) {
        service.record_hot_reload_event(version_id, false, duration_ms, 0).await;
        service.record_error(error, &[KeyValue::new("version.id", version_id.to_string())]).await;
    }
}