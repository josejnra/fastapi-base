from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider  # noqa: PLC2701
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,  # noqa: PLC2701
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler  # noqa: PLC2701
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor  # noqa: PLC2701
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import get_settings
from app.core.logger import logger

resource = Resource.create(
    attributes={"service.name": "fastapi-base", "service.instance.id": "instance-1"}
)

# tracer init
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

trace_console_exporter = ConsoleSpanExporter()
trace_console_processor = BatchSpanProcessor(trace_console_exporter)
tracer_provider.add_span_processor(trace_console_processor)

trace_otlp_exporter = OTLPSpanExporter(
    endpoint=f"{get_settings().OTEL_COLLECTOR_URL}:4317", insecure=True
)
trace_otlp_processor = BatchSpanProcessor(trace_otlp_exporter)
tracer_provider.add_span_processor(trace_otlp_processor)

tracer = trace.get_tracer("fastapi.base.tracer")

# meter init
meter_console_exporter = ConsoleMetricExporter()
meter_console_metric_reader = PeriodicExportingMetricReader(meter_console_exporter)

meter_otlp_exporter = OTLPMetricExporter(
    endpoint=f"{get_settings().OTEL_COLLECTOR_URL}:4317", insecure=True
)
meter_otlp_metric_reader = PeriodicExportingMetricReader(meter_otlp_exporter)

meter_provider = MeterProvider(
    metric_readers=[meter_console_metric_reader, meter_otlp_metric_reader],
    resource=resource,
)
metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter("fastapi.base.meter")


# log init
log_provider = LoggerProvider(resource=resource)
set_logger_provider(log_provider)

log_otlp_exporter = OTLPLogExporter(
    endpoint=f"{get_settings().OTEL_COLLECTOR_URL}:4317", insecure=True
)
log_provider.add_log_record_processor(BatchLogRecordProcessor(log_otlp_exporter))

handler = LoggingHandler(logger_provider=log_provider)

# Attach OTLP handler to root logger
logger.add(
    handler,
    enqueue=True,
)

# https://github.com/grafana/loki-fundamentals/blob/intro-to-otel/completed/app.py
