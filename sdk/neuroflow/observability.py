"""
OpenTelemetry集成模块
提供分布式追踪和指标收集功能
"""

import os
from typing import Optional, Dict, Any
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import SpanKind
from opentelemetry.metrics import Counter, Histogram
import logging


class ObservabilityConfig:
    """可观测性配置"""
    
    def __init__(
        self,
        service_name: str = "neuroflow-python-sdk",
        otlp_endpoint: str = "http://localhost:4318",
        traces_enabled: bool = True,
        metrics_enabled: bool = True,
        logs_enabled: bool = True,
    ):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.traces_enabled = traces_enabled
        self.metrics_enabled = metrics_enabled
        self.logs_enabled = logs_enabled


class ObservabilityProvider:
    """可观测性提供者"""
    
    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        self.tracer = None
        self.meter = None
        self._initialized = False
        
        # 指标对象
        self.agent_invocations_counter: Optional[Counter] = None
        self.agent_duration_histogram: Optional[Histogram] = None
    
    def initialize(self):
        """初始化可观测性系统"""
        if self._initialized:
            return
            
        resource = Resource.create({
            "service.name": self.config.service_name,
            "service.version": "0.1.0",
        })
        
        # 初始化追踪
        if self.config.traces_enabled:
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # 添加OTLP导出器
            span_exporter = OTLPSpanExporter(endpoint=f"{self.config.otlp_endpoint}/v1/traces")
            span_processor = self.tracer_provider.add_span_processor(
                span_exporter
            )
            
            self.tracer = trace.get_tracer(self.config.service_name)
        
        # 初始化指标
        if self.config.metrics_enabled:
            self.meter_provider = MeterProvider(resource=resource)
            metrics.set_meter_provider(self.meter_provider)
            
            # 添加OTLP导出器
            metric_exporter = OTLPMetricExporter(endpoint=f"{self.config.otlp_endpoint}/v1/metrics")
            self.meter_provider.add_metric_reader(metric_exporter)
            
            self.meter = self.meter_provider.get_meter(self.config.service_name)
            
            # 创建常用指标
            self.agent_invocations_counter = self.meter.create_counter(
                name="neuroflow.agent.invocations",
                description="Agent调用次数",
                unit="1",
            )
            
            self.agent_duration_histogram = self.meter.create_histogram(
                name="neuroflow.agent.duration",
                description="Agent处理时长",
                unit="seconds",
            )
        
        # 初始化日志记录
        if self.config.logs_enabled:
            LoggingInstrumentor().instrument()
        
        # 自动检测requests库
        RequestsInstrumentor().instrument()
        
        self._initialized = True
        logging.info(f"Observability initialized for service: {self.config.service_name}")
    
    def start_agent_span(self, agent_name: str, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """开始Agent操作的追踪Span"""
        if not self.tracer:
            return None
            
        span_attributes = {
            "agent.name": agent_name,
            "operation.type": operation,
        }
        
        if attributes:
            span_attributes.update(attributes)
        
        return self.tracer.start_as_current_span(
            name=f"{agent_name}.{operation}",
            kind=SpanKind.SERVER,
            attributes=span_attributes
        )
    
    def record_agent_metrics(self, agent_name: str, duration: float, success: bool = True):
        """记录Agent指标"""
        if self.agent_invocations_counter:
            self.agent_invocations_counter.add(
                1,
                attributes={
                    "agent.name": agent_name,
                    "success": str(success).lower(),
                }
            )
        
        if self.agent_duration_histogram:
            self.agent_duration_histogram.record(
                duration,
                attributes={
                    "agent.name": agent_name,
                }
            )
    
    def shutdown(self):
        """关闭可观测性系统"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
        
        if self.meter_provider:
            self.meter_provider.shutdown()


# 全局可观测性提供者
_global_observability: Optional[ObservabilityProvider] = None


def get_observability_provider() -> Optional[ObservabilityProvider]:
    """获取全局可观测性提供者"""
    return _global_observability


def initialize_observability(config: Optional[ObservabilityConfig] = None):
    """初始化全局可观测性系统"""
    global _global_observability
    
    if config is None:
        config = ObservabilityConfig()
    
    _global_observability = ObservabilityProvider(config)
    _global_observability.initialize()


def shutdown_observability():
    """关闭全局可观测性系统"""
    global _global_observability
    
    if _global_observability:
        _global_observability.shutdown()
        _global_observability = None