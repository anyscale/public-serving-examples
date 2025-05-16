from typing import List

from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import SpanProcessor


def default_tracing_exporter() -> List[SpanProcessor]:
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",
        insecure=True,
    )
    return [BatchSpanProcessor(otlp_exporter), BatchSpanProcessor(ConsoleSpanExporter())]
