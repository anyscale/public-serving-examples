from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased


def setup_opentelemetry(
    app: FastAPI,
    service_name: str,
    jaeger_host: Optional[str] = "jaeger",
    jaeger_port: Optional[int] = 14268,
    otlp_endpoint: Optional[str] = None,
    sampling_ratio: float = 1.0,
    console_export: bool = False,
):
    """
    Set up OpenTelemetry instrumentation for FastAPI.

    Args:
        app: FastAPI application to instrument
        service_name: Name of the service
        jaeger_host: Hostname of the Jaeger collector
        jaeger_port: Port of the Jaeger collector
        otlp_endpoint: Optional OTLP endpoint (e.g., "collector:4317")
        sampling_ratio: Sampling ratio for traces (0.0 to 1.0)
        console_export: Whether to export traces to console (for debugging)
    """
    # Set up resource
    resource = Resource.create({SERVICE_NAME: service_name})

    # Set up tracer provider with sampling
    sampler = TraceIdRatioBased(sampling_ratio)
    tracer_provider = TracerProvider(resource=resource, sampler=sampler)

    # Set up Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Set up OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set up console exporter for debugging if requested
    if console_export:
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI application
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)


def get_tracer(name: str):
    """Get a tracer for a specific component."""
    return trace.get_tracer(name)
