"""Payload models and the BlockBeat-to-PingInput payload creator for the demo pipeline."""

from __future__ import annotations

from typing import override

from nexus.v1 import (
    Actor,
    ActorBuilder,
    BlockBeat,
    Context,
    ContextStore,
    PayloadCreator,
    PipeToBus,
    TransformActor,
)
from pydantic import BaseModel


class PingInput(BaseModel):
    """Payload sent by the validator to a miner as a ping for the current block."""

    block_number: int
    ping: str = "ping"


class PongOutput(BaseModel):
    """Payload returned by the miner echoing the validator's ping for a block."""

    block_number: int
    ping: str


class PingPayloadCreator(PayloadCreator[BlockBeat, PingInput], ActorBuilder):
    """Maps a BlockBeat into a PingInput carrying the new block's number.

    sink input: BlockBeat from the validator's subnet clock
    source created_payload: PingInput addressed to a miner
    source error: payload creation failures
    """

    @override
    def build_actor(self, *, pipe_to_bus: PipeToBus, context_store: ContextStore) -> Actor:
        return PingPayloadCreatorActor(spec=self, pipe_to_bus=pipe_to_bus, context_store=context_store)


class PingPayloadCreatorActor(TransformActor[BlockBeat, PingInput]):
    """Actor that translates each BlockBeat into a PingInput for the miner."""

    @override
    def _transform(self, ctx: Context, payload: BlockBeat) -> PingInput:
        return PingInput(block_number=int(payload.block_number))
