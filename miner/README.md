# Miner reference

> This is **not a production-ready miner image**. It is a reference skeleton showing how a miner integrates
> with a validator built on this template. Subnet miners are typically operated by independent actors who
> build their own miner software; this folder exists to document the validator's expected miner interface.

## What's here

- `src/miner_reference/template.py` — minimal HTTP miner accepting validator requests on `TARGET_PATH` and
  posting the result back to the supplied `callback_url`.

## What this is NOT

- It is **not** the same as `../localnet/miners/miner.template.py`, which is a localnet test fixture that
  creates wallets, funds them from Alice, and self-registers miners on the local chain.
- There is **no** `installer/` workflow for the miner in this template. Miner deployment is intentionally
  left to subnet operators.

## Local sanity check

```sh
cd miner
uv sync
uv run python -c "from miner_reference import template; print(template.MINER_NAME)"
```

## Adapting to your subnet

Edit `template.py`:

- `MINER_NAME` — identifier reported in logs / wallet name.
- `TARGET_PATH` — must match the validator's expected endpoint (see `nexus.v1` `AsyncHttpNeuronCommunicator`).
- `handle_request()` — implement your subnet's miner-side logic.

This skeleton only models the HTTP request/callback contract. Registering axon info, managing wallets, and
operating a long-running miner process are intentionally left to the subnet-specific miner implementation.

Once you have a working miner, package and deploy it however you prefer — Docker image, raw `uv run`,
systemd unit, etc.
