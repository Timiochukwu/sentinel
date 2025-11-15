"""Comprehensive logging and monitoring configuration"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from app.core.config import settings

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
client_id_var: ContextVar[str] = ContextVar('client_id', default='')


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging

    Outputs logs in JSON format for easy parsing by log aggregation systems
    (CloudWatch, Datadog, ELK, etc.)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        client_id = client_id_var.get()
        if client_id:
            log_data["client_id"] = client_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for development

    Makes logs easier to read in terminal
    """

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        level_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging():
    """
    Configure application logging

    Sets up:
    - Console handler (colored for development, JSON for production)
    - File handler with rotation
    - Log levels based on environment
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "development":
        # Colored output for development
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # JSON output for production
        console_formatter = JSONFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (only in production)
    if settings.ENVIRONMENT != "development":
        file_handler = RotatingFileHandler(
            'logs/sentinel.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Application logger
    app_logger = logging.getLogger("sentinel")
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    return app_logger


# Initialize logger
logger = setup_logging()


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter with extra context

    Usage:
        log = get_logger("fraud_detection")
        log.info("Transaction checked", extra={
            "transaction_id": "txn_123",
            "risk_score": 85
        })
    """

    def process(self, msg: str, kwargs: Any) -> tuple:
        """Add extra data to log record"""
        extra = kwargs.get('extra', {})

        # Add request context
        extra['request_id'] = request_id_var.get()
        extra['client_id'] = client_id_var.get()

        kwargs['extra'] = {'extra_data': extra}
        return msg, kwargs


def get_logger(name: str) -> LoggerAdapter:
    """
    Get logger with adapter

    Args:
        name: Logger name (usually module name)

    Returns:
        LoggerAdapter instance
    """
    base_logger = logging.getLogger(f"sentinel.{name}")
    return LoggerAdapter(base_logger, {})


# Metrics tracking
class MetricsCollector:
    """
    Simple metrics collector

    In production, use Prometheus or CloudWatch
    """

    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "transactions_total": 0,
            "transactions_high_risk": 0,
            "transactions_declined": 0,
            "api_requests_total": 0,
            "api_errors_total": 0,
            "fraud_caught_total": 0,
            "false_positives_total": 0,
        }

    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric"""
        if metric in self.metrics:
            self.metrics[metric] += value

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return self.metrics.copy()

    def reset(self):
        """Reset all metrics"""
        for key in self.metrics:
            self.metrics[key] = 0


# Singleton metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector singleton"""
    return _metrics_collector
