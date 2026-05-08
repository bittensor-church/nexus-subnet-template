# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "litestar[standard]",
#     "httpx",
#     "click",
#     "pydantic",
# ]
# ///
"""
Reference HTTP miner skeleton.

Models a miner accepting work from a validator via an HTTP POST request,
then POSTing the result back to the validator via a callback URL.

Usage: uv run python -m miner_reference.template --host 0.0.0.0 --port 8091
"""

from __future__ import annotations

from typing import Any

import click
import httpx
import uvicorn
from litestar import Litestar, post
from pydantic import BaseModel

MINER_NAME = "reference"

# Must match the validator's AsyncHttpNeuronCommunicator target_path.
TARGET_PATH = "/task"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8091
CALLBACK_TIMEOUT_SECONDS = 10.0


class RequestEnvelope(BaseModel):
    request_id: str
    callback_url: str
    input: dict[str, Any]


class ResponseEnvelope(BaseModel):
    request_id: str
    output: dict[str, Any] | None = None
    error: str | None = None


def handle_request(input_data: dict[str, Any]) -> dict[str, Any]:
    """Transform validator input into miner output."""
    return input_data


@post(TARGET_PATH)
async def handle_task(data: RequestEnvelope) -> None:
    """Receive a task from the validator, process it, and POST the result back."""
    print(f"[miner] Received request {data.request_id}")

    try:
        output = handle_request(data.input)
        response = ResponseEnvelope(request_id=data.request_id, output=output)
    except Exception as exc:
        response = ResponseEnvelope(request_id=data.request_id, error=str(exc))

    async with httpx.AsyncClient(timeout=CALLBACK_TIMEOUT_SECONDS) as client:
        try:
            callback_response = await client.post(str(data.callback_url), json=response.model_dump())
            callback_response.raise_for_status()
            print(f"[miner] Responded to {data.request_id}")
        except Exception as exc:
            print(f"[miner] Failed to callback for {data.request_id}: {exc}")


def create_app() -> Litestar:
    """Build the reference miner HTTP app."""
    return Litestar(route_handlers=[handle_task])


@click.command()
@click.option("--host", default=DEFAULT_HOST, show_default=True, help="Host interface for the miner HTTP server.")
@click.option("--port", default=DEFAULT_PORT, show_default=True, type=int, help="Port for the miner HTTP server.")
def main(host: str, port: int) -> None:
    print(f"[miner] Serving {MINER_NAME} on {host}:{port}{TARGET_PATH}")
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
