"""Monitoring and observability with OpenTelemetry"""

from typing import Dict, Any, Optional
from contextvars import ContextVar
import time
from functools import wraps
from app.core.logging_config import get_logger, get_metrics_collector

# Try to import OpenTelemetry (optional dependency)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("⚠️  OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk")

logger = get_logger("monitoring")
metrics = get_metrics_collector()


class PerformanceMonitor:
    """
    Performance monitoring for fraud detection operations

    Tracks:
    - API response times
    - Fraud detection processing times
    - Database query times
    - External API call times
    """

    def __init__(self):
        self.timings: Dict[str, list] = {
            "api_response_time": [],
            "fraud_detection_time": [],
            "db_query_time": [],
            "ml_prediction_time": [],
            "consortium_lookup_time": []
        }

    def track_timing(self, operation: str, duration_ms: float):
        """Track operation timing"""
        if operation not in self.timings:
            self.timings[operation] = []

        self.timings[operation].append(duration_ms)

        # Keep only last 1000 measurements
        if len(self.timings[operation]) > 1000:
            self.timings[operation] = self.timings[operation][-1000:]

        # Log slow operations
        if duration_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow operation detected: {operation}",
                extra={"duration_ms": duration_ms}
            )

    def get_statistics(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        if operation not in self.timings or not self.timings[operation]:
            return {}

        timings = self.timings[operation]
        timings_sorted = sorted(timings)

        return {
            "count": len(timings),
            "mean": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
            "p50": timings_sorted[len(timings) // 2],
            "p95": timings_sorted[int(len(timings) * 0.95)],
            "p99": timings_sorted[int(len(timings) * 0.99)]
        }

    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations"""
        return {
            operation: self.get_statistics(operation)
            for operation in self.timings.keys()
        }


# Singleton performance monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor singleton"""
    return _performance_monitor


def track_performance(operation: str):
    """
    Decorator to track function performance

    Usage:
        @track_performance("fraud_detection")
        def check_fraud(transaction):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _performance_monitor.track_timing(operation, duration_ms)
                logger.debug(
                    f"{operation} completed",
                    extra={"duration_ms": round(duration_ms, 2)}
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _performance_monitor.track_timing(operation, duration_ms)
                logger.debug(
                    f"{operation} completed",
                    extra={"duration_ms": round(duration_ms, 2)}
                )

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class AlertManager:
    """
    Alert manager for critical events

    In production, integrate with:
    - PagerDuty
    - Slack
    - Email
    - SMS
    """

    def __init__(self):
        self.alerts: list = []

    def send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send alert

        Args:
            severity: critical, high, medium, low
            title: Alert title
            message: Alert message
            metadata: Additional context
        """
        alert = {
            "timestamp": time.time(),
            "severity": severity,
            "title": title,
            "message": message,
            "metadata": metadata or {}
        }

        self.alerts.append(alert)

        # Log alert
        log_level = {
            "critical": logger.critical,
            "high": logger.error,
            "medium": logger.warning,
            "low": logger.info
        }.get(severity, logger.info)

        log_level(
            f"ALERT: {title}",
            extra={"alert_message": message, "alert_metadata": metadata}
        )

        # In production, send to external services
        # self._send_to_pagerduty(alert)
        # self._send_to_slack(alert)

    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts"""
        return self.alerts[-limit:]


# Singleton alert manager
_alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Get alert manager singleton"""
    return _alert_manager


# OpenTelemetry tracing setup (if available)
if OTEL_AVAILABLE:
    # Create tracer provider
    provider = TracerProvider()

    # Add console exporter for development
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Create tracer
    tracer = trace.get_tracer("sentinel")
else:
    tracer = None


def trace_operation(operation_name: str):
    """
    Decorator for distributed tracing

    Usage:
        @trace_operation("check_fraud")
        async def check_fraud(transaction):
            ...
    """
    def decorator(func):
        if not OTEL_AVAILABLE or tracer is None:
            return func

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_fraud_check(
    transaction_id: str,
    risk_score: int,
    decision: str,
    processing_time_ms: float,
    client_id: str
):
    """
    Log fraud check with structured data

    This creates a structured log entry that can be easily
    queried and analyzed by log aggregation systems
    """
    logger.info(
        "Fraud check completed",
        extra={
            "event": "fraud_check",
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "decision": decision,
            "processing_time_ms": processing_time_ms,
            "client_id": client_id
        }
    )

    # Update metrics
    metrics.increment("transactions_total")

    if risk_score >= 70:
        metrics.increment("transactions_high_risk")

    if decision == "decline":
        metrics.increment("transactions_declined")

    # Track performance
    _performance_monitor.track_timing("fraud_detection_time", processing_time_ms)

    # Alert on slow processing
    if processing_time_ms > 200:  # SLA is <100ms typically
        _alert_manager.send_alert(
            severity="medium",
            title="Slow fraud detection",
            message=f"Transaction {transaction_id} took {processing_time_ms:.2f}ms to process",
            metadata={
                "transaction_id": transaction_id,
                "processing_time_ms": processing_time_ms,
                "sla_threshold_ms": 100
            }
        )


def log_feedback(
    transaction_id: str,
    actual_outcome: str,
    predicted_outcome: str,
    client_id: str
):
    """Log fraud feedback"""
    is_correct = actual_outcome == predicted_outcome

    logger.info(
        "Fraud feedback received",
        extra={
            "event": "fraud_feedback",
            "transaction_id": transaction_id,
            "actual_outcome": actual_outcome,
            "predicted_outcome": predicted_outcome,
            "is_correct": is_correct,
            "client_id": client_id
        }
    )

    # Update metrics
    if actual_outcome == "fraud":
        metrics.increment("fraud_caught_total")
    elif predicted_outcome == "fraud" and actual_outcome == "legitimate":
        metrics.increment("false_positives_total")
