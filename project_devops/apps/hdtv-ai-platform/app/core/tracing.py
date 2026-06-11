"""
T-28: OpenTelemetry tracing for HDTV AI Platform.

Adapted from platform/observability/tracing.py — adds:
  - Conditional enable via settings.tracing_enabled (default False, safe for dev)
  - Config via Pydantic Settings (jaeger_host, jaeger_port from .env)
  - FastAPI auto-instrumentation (opt-in via TRACING_ENABLED=true)
  - Graceful no-op when opentelemetry packages not installed
  - Service version label from app_name setting

Usage (in main.py create_app()):
    from app.core.tracing import configure_tracer
    if settings.tracing_enabled:
        configure_tracer(settings.app_name)

OTLP gRPC destination: platform-jaeger:4317 (Jaeger all-in-one in observability stack)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def configure_tracer(service_name: str) -> bool:
    """Configure OpenTelemetry tracer to export to Jaeger via OTLP gRPC.

    Args:
        service_name: Service name label in Jaeger UI (e.g. "hdtv-ai-platform")

    Returns:
        True if tracing was configured, False if opentelemetry packages not installed.

    The tracer is a module-level singleton — safe to call multiple times
    (subsequent calls are no-ops if provider is already set).
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    except ImportError:
        logger.warning(
            "[Tracing] opentelemetry packages not installed — tracing disabled. "
            "Install: opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
        )
        return False

    # Idempotency: skip if a real provider is already set
    existing = trace.get_tracer_provider()
    if not isinstance(existing, type(trace.ProxyTracerProvider())):
        # A real provider (not the default proxy) is already configured
        logger.debug("[Tracing] TracerProvider already configured — skipping")
        return True

    from app.core.config import get_settings
    cfg = get_settings()

    resource = Resource(attributes={
        "service.name":    service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production" if not cfg.debug else "development",
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    jaeger_endpoint = f"{cfg.jaeger_host}:{cfg.jaeger_port}"
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=jaeger_endpoint,
            insecure=True,      # Internal network only — no TLS needed
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        logger.info(
            "[Tracing] Configured for service '%s' → OTLP gRPC %s",
            service_name, jaeger_endpoint,
        )
        return True
    except Exception as exc:
        logger.warning("[Tracing] Failed to connect OTLP exporter to %s: %s", jaeger_endpoint, exc)
        return False


def instrument_fastapi(app: "FastAPI") -> bool:
    """Add FastAPI OpenTelemetry auto-instrumentation middleware.

    Instruments all routes with automatic span creation.
    Must be called after configure_tracer() and after app routers are registered.

    Args:
        app: The FastAPI application instance.

    Returns:
        True if instrumented, False if opentelemetry-instrumentation-fastapi not installed.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("[Tracing] FastAPI auto-instrumentation enabled")
        return True
    except ImportError:
        logger.warning(
            "[Tracing] opentelemetry-instrumentation-fastapi not installed — "
            "route-level spans disabled. "
            "Install: opentelemetry-instrumentation-fastapi"
        )
        return False
    except Exception as exc:
        logger.warning("[Tracing] FastAPI instrumentation failed: %s", exc)
        return False
