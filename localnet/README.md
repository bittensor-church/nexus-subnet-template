# Localnet

Run a complete local subnet for development and testing.

## Prerequisites

- Docker and Docker Compose
- uv

## Setup (one-time)

```sh
cp localnet/.env.example localnet/.env
```

Both `docker compose` and `bootstrap.py` read this file; create it before any of the steps below.

## Quick start (tmux)

```sh
localnet/run-in-tmux.sh
```

Runs the full flow: copies `.env` if missing, brings up docker compose, syncs validator
and miner deps, runs bootstrap, and starts validator + miner side by side in a tmux session
named `localnet` (2 panes, horizontal split). Detach: `Ctrl-b d`. Re-attach: `tmux attach -t localnet`.

Stop everything (kill tmux session + `docker compose down`):

```sh
localnet/stop-tmux.sh
```

If a session named `localnet` already exists, `run-in-tmux.sh` fails fast — run `stop-tmux.sh` first.

The sections below describe the same flow done by hand.

## Start infrastructure

```sh
cd localnet && docker compose up -d
```

Starts a local subtensor blockchain (port 9944) and a pylon proxy (port 8000).

## Bootstrap chain state

```sh
uv run localnet/bootstrap.py
```

Creates owner and validator wallets, funds them from Alice (pre-funded devnet account), creates subnet (netuid 2), and registers + stakes the validator. Idempotent — safe to re-run.

## Running the validator

```sh
cd validator && uv sync && uv run validator --env-file ../localnet/.env
```

The `localnet/.env` is pre-configured to connect to the local pylon.

## Running the miner

```sh
cd miner && uv sync && uv run miner -n 1
```

This is the production miner from the `miner/` module. For simulating multiple miner profiles (honest, adversarial, etc.) against the validator, see "Miner fixtures" below.

## Miner fixtures

Good miner profiles only. Adversarial profiles are TODO.

Each miner profile is a standalone script in `localnet/miners/`. Copy `miner.template.py` to create a new profile:

Each instance finds a free port and self-registers on the subnet

### Creating a new profile

Copy the template and customize:

```sh
cp localnet/miners/miner.template.py localnet/miners/miner-yourname.py
# edit MINER_NAME, TARGET_PATH, handle_request(), anything else necessary for the subnet
```

## Resetting

Full reset — clears chain state. Restart any running miners and validators afterwards so they re-register against the fresh chain.

```sh
cd localnet && docker compose down && docker compose up -d
```

Restart chain only:

```sh
cd localnet && docker compose restart subtensor
```
