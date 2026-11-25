"""Logging consumer actors for the demo pipeline's success and error sources."""

from __future__ import annotations

from typing import override

import structlog
from nexus.v1 import (
    Actor,
    ActorBuilder,
    ConsumerActor,
    Context,
    ContextStore,
    NexusException,
    Node,
    NodeSinks,
    NodeSources,
    PipeToBus,
    ProcessedInput,
    Routed,
    Sink,
    SinkName,
)

from validator.payload import PingInput, PongOutput

logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(__name__)


class ResponseLoggerNode(Node, ActorBuilder):
    """Sink-only node that logs successful and executor-failed miner responses.

    sink sink: ProcessedInput pairing the routed PingInput with PongOutput or NexusException
    """

    sink: Sink[ProcessedInput[Routed[PingInput], PongOutput]]

    def __init__(self, _id: str) -> None:
        super().__init__(_id)
        self.sink = Sink(f"{self.id}-sink", owner_node=self)

    @override
    def sinks(self) -> NodeSinks:
        return NodeSinks(sinks={SinkName("sink"): self.sink})

    @override
    def sources(self) -> NodeSources:
        return NodeSources(sources={})

    @override
    def build_actor(self, *, pipe_to_bus: PipeToBus, context_store: ContextStore) -> Actor:
        return ResponseLoggerActor(spec=self.sink, pipe_to_bus=pipe_to_bus, context_store=context_store)


class ResponseLoggerActor(ConsumerActor[ProcessedInput[Routed[PingInput], PongOutput]]):
    """Logs each miner response, distinguishing successful pongs from executor failures."""

    @override
    def _consume(self, ctx: Context, payload: ProcessedInput[Routed[PingInput], PongOutput]) -> None:
        target = payload.input.target
        result = payload.output
        if isinstance(result, NexusException):
            logger.warning(
                "miner_failed",
                hotkey=target.hotkey,
                uid=target.uid,
                block=payload.input.input.block_number,
                error=repr(result),
            )
            return
        logger.info(
            "pong_received",
            hotkey=target.hotkey,
            uid=target.uid,
            block=result.block_number,
            ping=result.ping,
        )


class ErrorLoggerNode(Node, ActorBuilder):
    """Sink-only node that logs framework/internal errors emitted by upstream actors.

    sink sink: NexusException from any upstream actor's error source
    """

    sink: Sink[NexusException]

    def __init__(self, _id: str) -> None:
        super().__init__(_id)
        self.sink = Sink(f"{self.id}-sink", owner_node=self)

    @override
    def sinks(self) -> NodeSinks:
        return NodeSinks(sinks={SinkName("sink"): self.sink})

    @override
    def sources(self) -> NodeSources:
        return NodeSources(sources={})

    @override
    def build_actor(self, *, pipe_to_bus: PipeToBus, context_store: ContextStore) -> Actor:
        return ErrorLoggerActor(spec=self.sink, pipe_to_bus=pipe_to_bus, context_store=context_store)


class ErrorLoggerActor(ConsumerActor[NexusException]):
    """Logs framework-level errors received from any upstream actor's error source."""

    @override
    def _consume(self, ctx: Context, payload: NexusException) -> None:
        logger.error("pipeline_error", context_id=str(ctx.id), error=repr(payload), exc_info=payload)
