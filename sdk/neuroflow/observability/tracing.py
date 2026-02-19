"""
NeuroFlow Python SDK - Observability Module

OpenTelemetry integration for distributed tracing, metrics, and logging.

Features:
- Distributed tracing for LLM calls, tool execution, A2A communication
- Metrics collection (request count, latency, error rate)
- Structured logging
- Export to Jaeger, Prometheus, Grafana

Usage:
    from neuroflow.observability import TracingService, MetricsCollector
    
    # Initialize tracing
    tracing = TracingService(
        service_name="neuroflow-agent",
        exporter_endpoint="http://localhost:4317",
    )
    await tracing.start()
    
    # Create span
    with tracing.span("tool_execution", tool_name="search"):
        result = await execute_tool()
    
    # Collect metrics
    metrics = MetricsCollector()
    metrics.increment("tool_invocations", tags={"tool": "search"})
    metrics.histogram("tool_latency", latency_ms, tags={"tool": "search"})
    
    await tracing.stop()
"""

import asyncio
import time
import json
import logging
from typing import Any, Dict, List, Optional, ContextManager
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import os

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Span kind"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class SpanContext:
    """Span context"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None


@dataclass
class Span:
    """Distributed tracing span"""
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error
    error_message: Optional[str] = None
    
    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms(),
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
            "error_message": self.error_message,
        }


class SpanExporter:
    """Base class for span exporters"""
    
    async def export(self, span: Span) -> None:
        """Export span"""
        raise NotImplementedError
    
    async def flush(self) -> None:
        """Flush pending spans"""
        pass


class ConsoleSpanExporter(SpanExporter):
    """Console span exporter for debugging"""
    
    async def export(self, span: Span) -> None:
        """Export to console"""
        print(f"[TRACE] {span.name}")
        print(f"  Trace ID: {span.context.trace_id}")
        print(f"  Span ID: {span.context.span_id}")
        print(f"  Duration: {span.duration_ms():.2f}ms")
        print(f"  Status: {span.status}")
        if span.attributes:
            print(f"  Attributes: {span.attributes}")
        if span.events:
            print(f"  Events: {span.events}")


class OTLPSpanExporter(SpanExporter):
    """OTLP span exporter for Jaeger/Tempo"""
    
    def __init__(self, endpoint: str = "http://localhost:4317"):
        self.endpoint = endpoint
        self._session: Optional[Any] = None
        self._pending_spans: List[Span] = []
    
    async def export(self, span: Span) -> None:
        """Export via OTLP"""
        self._pending_spans.append(span)
        
        # Batch export
        if len(self._pending_spans) >= 10:
            await self._flush_batch()
    
    async def _flush_batch(self) -> None:
        """Flush batch of spans"""
        if not self._pending_spans:
            return
        
        try:
            # Convert to OTLP format
            otlp_spans = [self._convert_to_otlp(span) for span in self._pending_spans]
            
            # Send to collector
            if not self._session:
                import aiohttp
                self._session = aiohttp.ClientSession()
            
            await self._session.post(
                f"{self.endpoint}/v1/traces",
                json={"resource_spans": otlp_spans},
                headers={"Content-Type": "application/json"},
            )
            
            self._pending_spans.clear()
            
        except Exception as e:
            logger.error(f"Failed to export spans: {e}")
    
    def _convert_to_otlp(self, span: Span) -> Dict[str, Any]:
        """Convert span to OTLP format"""
        # Simplified OTLP conversion
        return {
            "trace_id": span.context.trace_id,
            "span_id": span.context.span_id,
            "name": span.name,
            "start_time_unix_nano": int(span.start_time * 1e9) if span.start_time else 0,
            "end_time_unix_nano": int(span.end_time * 1e9) if span.end_time else 0,
            "attributes": [
                {"key": k, "value": {"string_value": str(v)}}
                for k, v in span.attributes.items()
            ],
        }
    
    async def flush(self) -> None:
        """Flush pending spans"""
        await self._flush_batch()


class TracingService:
    """
    Distributed tracing service
    
    Usage:
        tracing = TracingService(service_name="neuroflow")
        await tracing.start()
        
        with tracing.span("operation") as span:
            span.set_attribute("key", "value")
            await do_work()
        
        await tracing.stop()
    """
    
    def __init__(
        self,
        service_name: str,
        exporter: Optional[SpanExporter] = None,
        exporter_endpoint: Optional[str] = None,
        sample_rate: float = 1.0,
    ):
        self.service_name = service_name
        self.sample_rate = sample_rate
        
        # Create exporter
        if exporter:
            self.exporter = exporter
        elif exporter_endpoint:
            self.exporter = OTLPSpanExporter(exporter_endpoint)
        else:
            self.exporter = ConsoleSpanExporter()
        
        self._active_spans: Dict[str, Span] = {}
        self._span_stack: List[Span] = []
        self._is_running = False
    
    async def start(self) -> None:
        """Start tracing service"""
        self._is_running = True
        logger.info(f"Tracing service started: {self.service_name}")
    
    async def stop(self) -> None:
        """Stop tracing service"""
        self._is_running = False
        
        # Flush all spans
        await self.exporter.flush()
        
        logger.info("Tracing service stopped")
    
    def start_span(
        self,
        name: str,
        parent: Optional[Span] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ) -> Span:
        """Start a new span"""
        import uuid
        
        # Check sampling
        if self.sample_rate < 1.0 and hash(name) % 100 > self.sample_rate * 100:
            return None
        
        # Generate IDs
        trace_id = parent.context.trace_id if parent else str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_span_id = parent.context.span_id if parent else None
        
        # Create span
        span = Span(
            name=name,
            context=SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
            ),
            kind=kind,
            start_time=time.time(),
        )
        
        self._active_spans[span_id] = span
        self._span_stack.append(span)
        
        return span
    
    def end_span(self, span: Span, status: str = "ok", error: Optional[str] = None) -> None:
        """End a span"""
        span.end_time = time.time()
        span.status = status
        span.error_message = error
        
        # Export
        asyncio.create_task(self.exporter.export(span))
        
        # Remove from active
        if span.context.span_id in self._active_spans:
            del self._active_spans[span.context.span_id]
        
        # Remove from stack
        if span in self._span_stack:
            self._span_stack.remove(span)
    
    @contextmanager
    def span(
        self,
        name: str,
        parent: Optional[Span] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ) -> ContextManager[Span]:
        """Context manager for span"""
        span = self.start_span(name, parent, kind)
        
        try:
            yield span
            if span:
                self.end_span(span, status="ok")
        except Exception as e:
            if span:
                self.end_span(span, status="error", error=str(e))
            raise
    
    def get_current_span(self) -> Optional[Span]:
        """Get current active span"""
        return self._span_stack[-1] if self._span_stack else None
    
    def inject_context(self, span: Span) -> Dict[str, str]:
        """Inject span context into headers"""
        return {
            "traceparent": f"00-{span.context.trace_id}-{span.context.span_id}-01",
        }
    
    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract span context from headers"""
        traceparent = headers.get("traceparent", "")
        
        if not traceparent:
            return None
        
        try:
            parts = traceparent.split("-")
            if len(parts) == 4:
                return SpanContext(
                    trace_id=parts[1],
                    span_id=parts[2],
                    parent_span_id=None,
                )
        except:
            pass
        
        return None


@dataclass
class MetricPoint:
    """Metric data point"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "counter"  # counter, gauge, histogram


class MetricsCollector:
    """
    Metrics collector
    
    Usage:
        metrics = MetricsCollector()
        
        # Counter
        metrics.increment("requests_total", tags={"method": "GET"})
        
        # Gauge
        metrics.gauge("active_connections", 42)
        
        # Histogram
        metrics.histogram("request_latency", 123.45, tags={"endpoint": "/api"})
    """
    
    def __init__(self):
        self._metrics: List[MetricPoint] = []
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
    
    def increment(self, name: str, value: float = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter"""
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value
        
        self._metrics.append(MetricPoint(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metric_type="counter",
        ))
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set gauge value"""
        key = self._make_key(name, tags)
        self._gauges[key] = value
        
        self._metrics.append(MetricPoint(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metric_type="gauge",
        ))
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record histogram value"""
        key = self._make_key(name, tags)
        
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        
        self._metrics.append(MetricPoint(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metric_type="histogram",
        ))
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Make metric key"""
        if not tags:
            return name
        
        tags_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tags_str}}}"
    
    def get_metrics(self) -> List[MetricPoint]:
        """Get all metrics"""
        return self._metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {
                key: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "mean": sum(values) / len(values) if values else 0,
                }
                for key, values in self._histograms.items()
            },
        }


class StructuredLogger:
    """
    Structured logger
    
    Usage:
        logger = StructuredLogger("neuroflow")
        
        # Info with context
        logger.info("Request received", request_id="123", method="GET")
        
        # Error with exception
        logger.error("Request failed", exc_info=e)
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs) -> None:
        """Info log"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Warning log"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Error log"""
        if exc_info:
            kwargs["exception"] = str(exc_info)
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Debug log"""
        self.logger.debug(message, extra=kwargs)


class JsonFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format as JSON"""
        log_data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["msg", "args", "levelname", "levelno", "pathname", "filename",
                          "module", "lineno", "funcName", "created", "message"]:
                log_data[key] = value
        
        return json.dumps(log_data)


__all__ = [
    "SpanKind",
    "Span",
    "SpanContext",
    "SpanExporter",
    "ConsoleSpanExporter",
    "OTLPSpanExporter",
    "TracingService",
    "MetricsCollector",
    "StructuredLogger",
]
