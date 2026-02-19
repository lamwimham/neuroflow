pub mod service;
pub use service::{
    MonitoringService, MonitoringConfig, AlertCondition, AlertEvent, 
    AlertSeverity, ComparisonOperator, MetricType, predefined_metrics
};