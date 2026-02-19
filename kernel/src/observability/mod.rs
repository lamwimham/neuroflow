//! 可观测性基础设施模块
//! 
//! 提供OpenTelemetry链路追踪和Prometheus指标收集功能

pub mod tracer;
pub mod simple;
pub mod service;
pub mod demo;

pub use tracer::init_tracer;
pub use simple::{SimpleMetrics, RequestTimer};
pub use service::{ObservabilityService, ObservabilityConfig};
pub use demo::demo_observability;