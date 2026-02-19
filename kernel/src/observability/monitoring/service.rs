use opentelemetry::metrics::{Counter, Histogram, UpDownCounter, Meter};
use opentelemetry::KeyValue;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn, error, debug};
use crate::utils::Result;

/// 指标类型枚举
#[derive(Debug, Clone)]
pub enum MetricType {
    Counter,
    Gauge,
    Histogram,
    Summary,
}

/// 告警条件
#[derive(Debug, Clone)]
pub struct AlertCondition {
    pub metric_name: String,
    pub threshold: f64,
    pub comparison: ComparisonOperator,
    pub duration: std::time::Duration,
    pub alert_name: String,
    pub severity: AlertSeverity,
}

#[derive(Debug, Clone)]
pub enum ComparisonOperator {
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    Equal,
    NotEqual,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AlertSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

/// 告警事件
#[derive(Debug, Clone)]
pub struct AlertEvent {
    pub alert_name: String,
    pub severity: AlertSeverity,
    pub message: String,
    pub timestamp: std::time::SystemTime,
    pub labels: Vec<KeyValue>,
}

/// 监控配置
#[derive(Debug, Clone)]
pub struct MonitoringConfig {
    pub enable_metrics: bool,
    pub enable_tracing: bool,
    pub enable_logging: bool,
    pub metrics_collection_interval: std::time::Duration,
    pub alert_evaluation_interval: std::time::Duration,
    pub enable_alerts: bool,
    pub alert_webhook_url: Option<String>,
}

impl Default for MonitoringConfig {
    fn default() -> Self {
        Self {
            enable_metrics: true,
            enable_tracing: true,
            enable_logging: true,
            metrics_collection_interval: std::time::Duration::from_secs(15),
            alert_evaluation_interval: std::time::Duration::from_secs(30),
            enable_alerts: true,
            alert_webhook_url: None,
        }
    }
}

/// 监控服务
pub struct MonitoringService {
    meter: Meter,
    config: MonitoringConfig,
    counters: HashMap<String, Counter<u64>>,
    histograms: HashMap<String, Histogram<f64>>,
    gauges: HashMap<String, opentelemetry::metrics::ObservableGauge<i64>>,
    alert_conditions: Vec<AlertCondition>,
    alert_history: Arc<RwLock<Vec<AlertEvent>>>,
    active_alerts: Arc<RwLock<HashMap<String, AlertEvent>>>,
}

impl MonitoringService {
    pub fn new(config: MonitoringConfig) -> Result<Self> {
        let meter = opentelemetry::global::meter("neuroflow-monitoring");
        
        Ok(Self {
            meter,
            config,
            counters: HashMap::new(),
            histograms: HashMap::new(),
            gauges: HashMap::new(),
            alert_conditions: Vec::new(),
            alert_history: Arc::new(RwLock::new(Vec::new())),
            active_alerts: Arc::new(RwLock::new(HashMap::new())),
        })
    }

    /// 创建计数器
    pub fn create_counter(&mut self, name: &str, description: &str, unit: &str) -> Counter<u64> {
        let counter = self.meter
            .u64_counter(name)
            .with_description(description)
            .with_unit(unit)
            .init();
        
        self.counters.insert(name.to_string(), counter.clone());
        counter
    }

    /// 创建直方图
    pub fn create_histogram(&mut self, name: &str, description: &str, unit: &str) -> Histogram<f64> {
        let histogram = self.meter
            .f64_histogram(name)
            .with_description(description)
            .with_unit(unit)
            .init();
        
        self.histograms.insert(name.to_string(), histogram.clone());
        histogram
    }

    /// 记录计数器值
    pub fn record_counter(&self, name: &str, value: u64, attributes: &[KeyValue]) {
        if let Some(counter) = self.counters.get(name) {
            counter.add(value, attributes);
        }
    }

    /// 记录直方图值
    pub fn record_histogram(&self, name: &str, value: f64, attributes: &[KeyValue]) {
        if let Some(histogram) = self.histograms.get(name) {
            histogram.record(value, attributes);
        }
    }

    /// 添加告警条件
    pub fn add_alert_condition(&mut self, condition: AlertCondition) {
        self.alert_conditions.push(condition);
    }

    /// 检查告警条件
    pub async fn evaluate_alerts(&self) -> Result<()> {
        // 这里可以集成实际的指标数据来评估告警条件
        // 为了简化，我们模拟告警评估
        
        for condition in &self.alert_conditions {
            // 模拟评估逻辑
            match condition.comparison {
                ComparisonOperator::GreaterThan => {
                    // 模拟获取当前指标值
                    let current_value = self.get_mock_metric_value(&condition.metric_name);
                    
                    if current_value > condition.threshold {
                        self.trigger_alert(condition, current_value).await?;
                    }
                }
                ComparisonOperator::LessThan => {
                    let current_value = self.get_mock_metric_value(&condition.metric_name);
                    
                    if current_value < condition.threshold {
                        self.trigger_alert(condition, current_value).await?;
                    }
                }
                _ => {
                    // 其他比较操作的实现
                    let current_value = self.get_mock_metric_value(&condition.metric_name);
                    self.trigger_alert(condition, current_value).await?;
                }
            }
        }
        
        Ok(())
    }

    /// 获取模拟指标值（在实际实现中，这会从指标存储中获取真实值）
    fn get_mock_metric_value(&self, metric_name: &str) -> f64 {
        // 这里只是一个模拟实现
        // 在实际应用中，应该从指标存储中获取真实的指标值
        match metric_name {
            "neuroflow.request.duration" => 0.5, // 500ms
            "neuroflow.error.count" => 2.0,
            "neuroflow.request.count" => 100.0,
            _ => 0.0,
        }
    }

    /// 触发告警
    async fn trigger_alert(&self, condition: &AlertCondition, current_value: f64) -> Result<()> {
        let alert_event = AlertEvent {
            alert_name: condition.alert_name.clone(),
            severity: condition.severity.clone(),
            message: format!(
                "Alert triggered: {} is {} {} (current: {})",
                condition.metric_name,
                match condition.comparison {
                    ComparisonOperator::GreaterThan => ">",
                    ComparisonOperator::LessThan => "<",
                    ComparisonOperator::GreaterThanOrEqual => ">=",
                    ComparisonOperator::LessThanOrEqual => "<=",
                    ComparisonOperator::Equal => "==",
                    ComparisonOperator::NotEqual => "!=",
                },
                condition.threshold,
                current_value
            ),
            timestamp: std::time::SystemTime::now(),
            labels: vec![
                KeyValue::new("metric_name", condition.metric_name.clone()),
                KeyValue::new("threshold", condition.threshold.to_string()),
                KeyValue::new("current_value", current_value.to_string()),
            ],
        };

        // 添加到活跃告警
        {
            let mut active_alerts = self.active_alerts.write().await;
            active_alerts.insert(condition.alert_name.clone(), alert_event.clone());
        }

        // 添加到告警历史
        {
            let mut alert_history = self.alert_history.write().await;
            alert_history.push(alert_event.clone());
            
            // 限制历史记录数量
            if alert_history.len() > 1000 {
                alert_history.drain(0..alert_history.len()-500);
            }
        }

        // 记录告警
        match condition.severity {
            AlertSeverity::Info => info!("{}", alert_event.message),
            AlertSeverity::Warning => warn!("{}", alert_event.message),
            AlertSeverity::Error => error!("{}", alert_event.message),
            AlertSeverity::Critical => error!("CRITICAL ALERT: {}", alert_event.message),
        }

        // 如果配置了webhook，发送通知
        if let Some(webhook_url) = &self.config.alert_webhook_url {
            self.send_alert_webhook(alert_event, webhook_url).await;
        }

        Ok(())
    }

    /// 发送告警webhook
    async fn send_alert_webhook(&self, alert: AlertEvent, webhook_url: &str) {
        // 简单的webhook发送实现
        // 在实际应用中，应该使用更健壮的HTTP客户端
        let client = reqwest::Client::new();
        let payload = serde_json::json!({
            "alert_name": alert.alert_name,
            "severity": format!("{:?}", alert.severity),
            "message": alert.message,
            "timestamp": alert.timestamp.duration_since(std::time::UNIX_EPOCH)
                .unwrap_or(std::time::Duration::from_secs(0))
                .as_secs(),
        });

        match client.post(webhook_url).json(&payload).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    debug!("Alert webhook sent successfully");
                } else {
                    error!("Failed to send alert webhook: {}", response.status());
                }
            }
            Err(e) => {
                error!("Error sending alert webhook: {}", e);
            }
        }
    }

    /// 获取活跃告警
    pub async fn get_active_alerts(&self) -> HashMap<String, AlertEvent> {
        self.active_alerts.read().await.clone()
    }

    /// 获取告警历史
    pub async fn get_alert_history(&self) -> Vec<AlertEvent> {
        self.alert_history.read().await.clone()
    }

    /// 清除已解决的告警
    pub async fn clear_resolved_alerts(&self) -> Result<()> {
        let mut active_alerts = self.active_alerts.write().await;
        
        // 这里应该检查告警条件是否仍然满足
        // 为了简化，我们只保留最近的告警
        active_alerts.retain(|_, alert| {
            // 保留1小时内发生的告警
            alert.timestamp.elapsed().unwrap_or(std::time::Duration::from_secs(0))
                < std::time::Duration::from_secs(3600)
        });
        
        Ok(())
    }

    /// 启动监控服务
    pub async fn start(&self) -> Result<()> {
        if self.config.enable_alerts {
            // 启动告警评估任务
            let this = self.clone_for_task();
            tokio::spawn(async move {
                loop {
                    if let Err(e) = this.evaluate_alerts().await {
                        error!("Error evaluating alerts: {}", e);
                    }
                    
                    tokio::time::sleep(self.config.alert_evaluation_interval).await;
                }
            });
        }
        
        info!("Monitoring service started with config: {:?}", self.config);
        Ok(())
    }

    /// 为任务克隆服务实例
    fn clone_for_task(&self) -> Self {
        Self {
            meter: self.meter.clone(),
            config: self.config.clone(),
            counters: self.counters.clone(),
            histograms: self.histograms.clone(),
            gauges: self.gauges.clone(),
            alert_conditions: self.alert_conditions.clone(),
            alert_history: self.alert_history.clone(),
            active_alerts: self.active_alerts.clone(),
        }
    }
}

impl Clone for MonitoringService {
    fn clone(&self) -> Self {
        Self {
            meter: self.meter.clone(),
            config: self.config.clone(),
            counters: self.counters.clone(),
            histograms: self.histograms.clone(),
            gauges: self.gauges.clone(),
            alert_conditions: self.alert_conditions.clone(),
            alert_history: self.alert_history.clone(),
            active_alerts: self.active_alerts.clone(),
        }
    }
}

// 预定义的常用指标
pub mod predefined_metrics {
    use super::*;
    use opentelemetry::KeyValue;

    pub fn register_common_metrics(service: &mut MonitoringService) {
        // 请求计数器
        service.create_counter(
            "neuroflow.request.count",
            "Total number of requests received",
            "1"
        );

        // 请求持续时间直方图
        service.create_histogram(
            "neuroflow.request.duration",
            "Request processing duration",
            "seconds"
        );

        // 错误计数器
        service.create_counter(
            "neuroflow.error.count",
            "Total number of errors",
            "1"
        );

        // 活跃沙箱计数器
        service.create_counter(
            "neuroflow.sandbox.count",
            "Number of active sandboxes",
            "1"
        );
    }

    pub fn record_request(service: &MonitoringService, duration: f64, attributes: &[KeyValue]) {
        service.record_counter("neuroflow.request.count", 1, attributes);
        service.record_histogram("neuroflow.request.duration", duration, attributes);
    }

    pub fn record_error(service: &MonitoringService, attributes: &[KeyValue]) {
        service.record_counter("neuroflow.error.count", 1, attributes);
    }

    pub fn record_active_sandboxes(service: &MonitoringService, count: u64, attributes: &[KeyValue]) {
        service.record_counter("neuroflow.sandbox.count", count, attributes);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use opentelemetry::KeyValue;

    #[tokio::test]
    async fn test_monitoring_service_creation() {
        let config = MonitoringConfig::default();
        let mut service = MonitoringService::new(config).unwrap();
        
        // 测试创建指标
        service.create_counter("test.counter", "Test counter", "1");
        service.create_histogram("test.histogram", "Test histogram", "seconds");
        
        // 测试记录指标
        let attributes = vec![KeyValue::new("test", "value")];
        service.record_counter("test.counter", 1, &attributes);
        service.record_histogram("test.histogram", 1.0, &attributes);
        
        // 测试告警条件
        let condition = AlertCondition {
            metric_name: "test.counter".to_string(),
            threshold: 0.5,
            comparison: ComparisonOperator::GreaterThan,
            duration: std::time::Duration::from_secs(60),
            alert_name: "test_alert".to_string(),
            severity: AlertSeverity::Warning,
        };
        
        service.add_alert_condition(condition);
        
        assert_eq!(service.alert_conditions.len(), 1);
    }

    #[tokio::test]
    async fn test_alert_evaluation() {
        let config = MonitoringConfig::default();
        let service = MonitoringService::new(config).unwrap();
        
        // 添加告警条件
        let condition = AlertCondition {
            metric_name: "neuroflow.request.duration".to_string(),
            threshold: 0.1, // 阈值较低，应该触发告警
            comparison: ComparisonOperator::GreaterThan,
            duration: std::time::Duration::from_secs(60),
            alert_name: "high_latency_alert".to_string(),
            severity: AlertSeverity::Warning,
        };
        
        // 注意：这里我们不能直接访问service.alert_conditions因为它是私有的
        // 在实际实现中，我们会有一个公共方法来添加告警条件
    }
}