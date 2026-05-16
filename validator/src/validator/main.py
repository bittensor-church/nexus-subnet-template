"""Demo Nexus validator: every new block, ping a miner over HTTP and log the response."""

from __future__ import annotations

from datetime import timedelta
from ipaddress import IPv4Address
from pathlib import Path

import click
from dotenv import load_dotenv
from nexus.v1 import (
    AsyncHttpNeuronCommunicator,
    NexusValidator,
    Port,
    RoundRobinNeuronRouter,
    miners_only,
)
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from validator.payload import PingInput, PingPayloadCreator, PongOutput
from validator.response_logger import ErrorLoggerNode, ResponseLoggerNode


class Settings(BaseSettings):
    """Runtime configuration for the demo validator."""

    model_config = SettingsConfigDict(env_prefix="VALIDATOR_", extra="ignore")

    netuid: int = Field(validation_alias=AliasChoices("VALIDATOR_NETUID", "NETUID"))
    callback_host: str = "127.0.0.1"
    callback_port: int = 8001
    send_timeout: timedelta = timedelta(seconds=2)
    total_processing_timeout: timedelta = timedelta(seconds=10)
    max_in_flight: int = 4


class Validator(NexusValidator):
    """Demo validator wiring: subnet clock → ping payload → miner router → HTTP communicator → logger."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

        payload_creator = PingPayloadCreator("ping-payload-creator")
        router = RoundRobinNeuronRouter[PingInput](
            "miner-router",
            netuid=settings.netuid,
            neuron_filter=miners_only,
        )
        communicator = AsyncHttpNeuronCommunicator[PingInput, PongOutput](
            "miner-communicator",
            target_path="/task",
            send_timeout=settings.send_timeout,
            total_processing_timeout=settings.total_processing_timeout,
            max_in_flight=settings.max_in_flight,
            callback_bind_ip=IPv4Address("0.0.0.0"),
            callback_port=Port(settings.callback_port),
            callback_path="/callback",
            callback_base_url=f"http://{settings.callback_host}:{settings.callback_port}",
            input_model=PingInput,
            output_model=PongOutput,
        )
        response_logger = ResponseLoggerNode("response-logger")
        error_logger = ErrorLoggerNode("error-logger")

        self.connect(self.subnet_clock.source, payload_creator.input)
        self.connect(payload_creator.created_payload, router.input)
        self.connect(router.routed, communicator.input)
        self.connect(communicator.processed, response_logger.sink)
        self.connect(payload_creator.error, error_logger.sink)
        self.connect(router.error, error_logger.sink)
        self.connect(communicator.error, error_logger.sink)


@click.command()
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
def main(env_file: Path | None) -> None:
    """CLI entry point: load env from --env-file (if given) and run the validator."""
    load_dotenv(env_file)
    Validator.run(settings_class=Settings)


if __name__ == "__main__":
    main()
