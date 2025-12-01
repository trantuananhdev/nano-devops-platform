import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def configure_tracer(service_name):
    """Configure OpenTelemetry tracer to export to Jaeger."""
    
    # Set up a resource to identify this service
    resource = Resource(attributes={
        "service.name": service_name,
    })

    # Set up a tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure the OTLP exporter to send spans to Jaeger
    # Assumes Jaeger is running on the host specified by JAEGER_HOST
    jaeger_host = os.getenv("JAEGER_HOST", "platform-jaeger")
    jaeger_port = os.getenv("JAEGER_PORT", "4317") # OTLP gRPC port
    
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{jaeger_host}:{jaeger_port}",
        insecure=True # Use insecure connection for local dev
    )

    # Use a BatchSpanProcessor to send spans in batches
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    print(f"[Tracing] Configured for service '{service_name}' sending to {jaeger_host}:{jaeger_port}")
