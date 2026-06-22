"""Structured logging configuration for the validator.

Routes all stdlib logging (Nexus internals, httpx, and the validator's own
modules) and any native ``structlog`` loggers through a single
``structlog.stdlib.ProcessorFormatter``. The renderer, the root level, and the
per-logger level overrides are all driven by :class:`LoggingSettings`, which
reads ``VALIDATOR_LOGGING_``-prefixed environment variables.
"""

from __future__ import annotations

import enum
import logging.config
from typing import Any, Final

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict
from structlog.processors import CallsiteParameterAdder
from structlog.types import Processor


class LogFormat(enum.StrEnum):
    """Renderer selection for the validator's log output."""

    CONSOLE = "console"
    JSON = "json"


class LoggingSettings(BaseSettings):
    """Configuration for the validator's structured logging.

    All fields are overridable via ``VALIDATOR_LOGGING_``-prefixed environment
    variables; the defaults reproduce the validator's production logging
    behaviour. ``levels`` maps individual logger names to their level and is
    read from a single JSON-encoded environment variable
    (for example ``VALIDATOR_LOGGING_LEVELS='{"httpx":"WARNING"}'``).
    """

    model_config = SettingsConfigDict(env_prefix="VALIDATOR_LOGGING_", extra="ignore")

    format: LogFormat = LogFormat.JSON
    root_level: str = "INFO"
    levels: dict[str, str] = {"httpx": "WARNING", "httpcore": "WARNING"}


_SHARED_PROCESSORS: Final[list[Processor]] = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
]
"""Processors applied to both native structlog and foreign stdlib records."""


def _build_dict_config(settings: LoggingSettings) -> dict[str, Any]:
    """Build the :func:`logging.config.dictConfig` mapping for the given settings."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(),
                ],
                "foreign_pre_chain": _SHARED_PROCESSORS,
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.format_exc_info,
                    structlog.processors.JSONRenderer(),
                ],
                "foreign_pre_chain": _SHARED_PROCESSORS,
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": settings.format.value,
            },
        },
        "root": {
            "handlers": ["default"],
            "level": settings.root_level,
        },
        "loggers": {name: {"level": level} for name, level in settings.levels.items()},
    }


def _configure_structlog() -> None:
    """Route native ``structlog`` loggers through the stdlib ``ProcessorFormatter``."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def configure_logging(settings: LoggingSettings) -> None:
    """Install the global logging configuration.

    Applies a stdlib :func:`logging.config.dictConfig` whose single stream
    handler renders pretty console output when ``settings.format`` is
    :attr:`LogFormat.CONSOLE` and line-delimited JSON when it is
    :attr:`LogFormat.JSON`, sets the root logger to ``settings.root_level``,
    applies the per-logger overrides from ``settings.levels``, and points native
    ``structlog`` loggers at the same formatter. Uses
    ``disable_existing_loggers=False`` so handlers added by other libraries (for
    example Sentry's logging integration) are preserved.

    Args:
        settings: Resolved logging configuration controlling renderer, root
            level, and per-logger level overrides.
    """
    logging.config.dictConfig(_build_dict_config(settings))
    _configure_structlog()
