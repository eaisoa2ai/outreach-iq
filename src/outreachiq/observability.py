"""Tracing setup. Uses the real OpenTelemetry API — not a bespoke timing
shim — so the exact same instrumentation in campaign.py/workflow.py/tools.py
works unchanged whether spans print to the console (the default, zero
external infrastructure) or ship to a real collector.

Point OTEL_EXPORTER_OTLP_ENDPOINT at a collector (Jaeger, Tempo, Honeycomb,
...) to switch from console output to real distributed tracing with no code
changes — only that one environment variable.
"""
from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

_initialized = False


def _init_tracing() -> None:
    global _initialized
    if _initialized:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": "outreachiq"}))

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer() -> trace.Tracer:
    _init_tracing()
    return trace.get_tracer("outreachiq")
