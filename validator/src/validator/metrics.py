"""Prometheus metrics surface for the validator.

Exposes a ``/metrics`` HTTP endpoint scraped by the local Prometheus container,
and hosts the registry where downstream code registers counters, gauges, and
histograms describing validator behavior. The HTTP server runs as a daemon
thread spawned from :func:`start_metrics_server`, so it lives alongside the
Nexus runtime without sharing its lifecycle.
"""

from __future__ import annotations

from prometheus_client import start_http_server


def start_metrics_server(port: int = 9080) -> None:
    """Start the Prometheus exposition server on ``port`` in a daemon thread."""
    start_http_server(port)
