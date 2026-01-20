import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sentry_sdk
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from pythonjsonlogger import jsonlogger

from config import settings


class StructuredLogger:
    """Structured logging with JSON format and monitoring integration"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_metrics()
        self.setup_sentry()
    
    def setup_logging(self):
        """Setup structured logging with JSON formatter"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logHandler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        
        # File handler for persistent logs
        fileHandler = logging.FileHandler(log_dir / "sentinelrisk.log")
        fileHandler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        logger.addHandler(logHandler)
        logger.addHandler(fileHandler)
        
        self.logger = logging.getLogger("sentinelrisk")
    
    def setup_sentry(self):
        """Setup Sentry for error tracking"""
        if settings.SENTRY_DSN:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                traces_sample_rate=1.0,
                environment="production"
            )
            self.logger.info("Sentry initialized for error tracking")
    
    def setup_metrics(self):
        """Setup Prometheus metrics"""
        # Request metrics
        self.request_count = Counter(
            'sentinel_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'sentinel_request_duration_seconds',
            'Request duration',
            ['method', 'endpoint']
        )
        
        # Fraud detection metrics
        self.predictions_total = Counter(
            'sentinel_predictions_total',
            'Total fraud predictions',
            ['decision']
        )
        
        self.risk_score_histogram = Histogram(
            'sentinel_risk_score',
            'Risk score distribution',
            buckets=[0.001, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0]
        )
        
        # System metrics
        self.active_users = Gauge(
            'sentinel_active_users',
            'Number of active users'
        )
        
        self.database_connections = Gauge(
            'sentinel_database_connections',
            'Active database connections'
        )
    
    def log_request(self, request: Request, response: Response, duration: float):
        """Log HTTP request with metrics"""
        self.request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        self.request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        self.logger.info(
            "HTTP request completed",
            extra={
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
    
    def log_prediction(self, prediction_data: Dict[str, Any]):
        """Log fraud prediction with metrics"""
        decision = prediction_data.get("decision", "UNKNOWN")
        risk_score = prediction_data.get("risk_score", 0.0)
        
        self.predictions_total.labels(decision=decision).inc()
        self.risk_score_histogram.observe(risk_score)
        
        self.logger.info(
            "Fraud prediction completed",
            extra={
                "decision": decision,
                "risk_score": risk_score,
                "amount": prediction_data.get("amount"),
                "request_id": prediction_data.get("request_id"),
                "user_id": prediction_data.get("user_id"),
                "processing_time_ms": prediction_data.get("processing_time_ms")
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": event_type,
                "severity": "high",
                **details
            }
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log errors with context"""
        self.logger.error(
            f"Application error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            },
            exc_info=True
        )
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest()


class ModelMonitor:
    """Monitor model performance and detect drift"""
    
    def __init__(self):
        self.logger = logging.getLogger("model_monitor")
        self.prediction_count = 0
        self.risk_scores = []
        self.decisions = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
    
    def record_prediction(self, risk_score: float, decision: str):
        """Record prediction for monitoring"""
        self.prediction_count += 1
        self.risk_scores.append(risk_score)
        self.decisions[decision] = self.decisions.get(decision, 0) + 1
        
        # Check for anomalies every 100 predictions
        if self.prediction_count % 100 == 0:
            self.check_for_drift()
    
    def check_for_drift(self):
        """Check for model drift"""
        if len(self.risk_scores) < 10:
            return
        
        avg_risk = sum(self.risk_scores) / len(self.risk_scores)
        block_rate = self.decisions["BLOCK"] / self.prediction_count
        
        # Alert thresholds
        if avg_risk > 0.2:  # Unusually high average risk
            self.logger.warning(
                "High average risk score detected",
                extra={
                    "avg_risk": avg_risk,
                    "threshold": 0.2,
                    "prediction_count": self.prediction_count
                }
            )
        
        if block_rate > 0.15:  # Unusually high block rate
            self.logger.warning(
                "High block rate detected",
                extra={
                    "block_rate": block_rate,
                    "threshold": 0.15,
                    "prediction_count": self.prediction_count
                }
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        return {
            "prediction_count": self.prediction_count,
            "avg_risk_score": sum(self.risk_scores) / len(self.risk_scores) if self.risk_scores else 0,
            "decision_distribution": self.decisions.copy(),
            "recent_predictions": len(self.risk_scores)
        }


# Global instances
structured_logger = StructuredLogger()
model_monitor = ModelMonitor()
