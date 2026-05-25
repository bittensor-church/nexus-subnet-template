# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bittensor",
#     "bittensor-wallet",
#     "python-dotenv",
# ]
# ///
"""
Localnet bootstrap script.

Sets up the local subnet infrastructure:
- Transfers TAO from Alice (pre-funded devnet account) to owner and validator wallets
- Creates and activates subnet (netuid 2, since netuid 1 is owned by zero-key and is unusable)
- Registers and stakes validator neuron

register_subnet has no netuid parameter — the chain auto-assigns the next free slot. We
assume it matches NETUID from localnet/.env and abort if not, so pylon/validator/monitor
don't end up pointed at a different subnet than the one we configured.

Prerequisites: subtensor must be running (cd localnet && docker compose up).

Usage: uv run localnet/bootstrap.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import bittensor as bt
from bittensor.core.extrinsics.pallets import Sudo
from bittensor.utils.balance import Balance
from bittensor_wallet import Keypair, Wallet
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

WALLETS_DIR = Path(__file__).parent / "wallets"
SUBTENSOR_NETWORK = "ws://127.0.0.1:9944"
VALIDATOR_STAKE_TAO = 1000.0
FUND_AMOUNT_TAO = 10_000.0

EXPECTED_NETUID = int(os.environ["NETUID"])
SUBNET_TEMPO = int(os.environ["SUBNET_TEMPO"])

# Disabled until we have support for fast blocks in pylon
SUBNET_COMMIT_REVEAL_ENABLED = False

# AdminFreezeWindow gates subnet-owner admin extrinsics during the last N blocks of each
# tempo. Disabled on localnet so bootstrap/operator hyperparameter calls are never rejected
# with AdminActionProhibitedDuringWeightsWindow, otherwise the random rejections get annoying fast.
ADMIN_FREEZE_WINDOW = 0


def wait_for_subtensor(network: str, retries: int = 30, delay: float = 2.0) -> bt.Subtensor:
    """Wait for the local subtensor to become reachable."""
    for attempt in range(retries):
        try:
            sub = bt.Subtensor(network=network)
            block = sub.get_current_block()
            print(f"Connected to subtensor at block {block}")
            return sub
        except Exception:
            print(f"Waiting for subtensor... (attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    print("Failed to connect to subtensor. Is docker compose running?")
    sys.exit(1)


def get_alice_wallet() -> Wallet:
    """Create a wallet backed by Alice's well-known devnet keypair."""
    alice_kp = Keypair.create_from_uri("//Alice")
    wallet = Wallet(name="alice", path=str(WALLETS_DIR))
    wallet.set_coldkey(keypair=alice_kp, encrypt=False, overwrite=True)
    wallet.set_coldkeypub(keypair=alice_kp, overwrite=True)
    wallet.set_hotkey(keypair=alice_kp, encrypt=False, overwrite=True)
    return wallet


def get_or_create_wallet(name: str) -> Wallet:
    """Create a wallet if it doesn't exist, using localnet wallets directory."""
    wallet = Wallet(name=name, path=str(WALLETS_DIR))
    wallet.create_if_non_existent(coldkey_use_password=False, hotkey_use_password=False)
    return wallet


def fund_wallet(subtensor: bt.Subtensor, alice: Wallet, target: Wallet) -> None:
    """Transfer TAO from Alice to a target wallet if balance is low."""
    balance = subtensor.get_balance(target.coldkey.ss58_address)
    if balance > Balance.from_tao(100.0):
        print(f"  {target.name} already funded (balance: {balance})")
        return
    print(f"  Funding {target.name} with {FUND_AMOUNT_TAO} TAO from Alice...")
    response = subtensor.transfer(
        wallet=alice,
        destination_ss58=target.coldkey.ss58_address,
        amount=Balance.from_tao(FUND_AMOUNT_TAO),
        wait_for_inclusion=True,
        wait_for_finalization=True,
        mev_protection=False,
    )
    if not response.success:
        print(f"  Transfer failed: {response.message}")
        sys.exit(1)
    print(f"  {target.name} funded")


def get_subnet_owner_coldkey(subtensor: bt.Subtensor, netuid: int) -> str | None:
    """Return owner coldkey of an existing subnet, or None if it doesn't exist.

    Avoids `subtensor.all_subnets()`, which currently raises ZeroDivisionError on freshly
    created subnets when alpha_in is 0 (bittensor 10.3.1 bug).
    """
    if not subtensor.subnet_exists(netuid=netuid):
        return None
    return subtensor.subnet(netuid=netuid).owner_coldkey


def create_subnet(subtensor: bt.Subtensor, owner: Wallet) -> int:
    """Create a subnet at EXPECTED_NETUID if missing. Returns the netuid. Idempotent."""
    existing_owner = get_subnet_owner_coldkey(subtensor, EXPECTED_NETUID)
    if existing_owner is not None:
        if existing_owner == owner.coldkey.ss58_address:
            print(f"Subnet {EXPECTED_NETUID} already exists and is owned by us")
            return EXPECTED_NETUID
        print(
            f"Subnet {EXPECTED_NETUID} already exists but is owned by {existing_owner}, "
            f"not our owner ({owner.coldkey.ss58_address}). "
            f"Reset localnet (`cd localnet && docker compose down -v && rm -rf wallets/*/`) "
            f"or update NETUID in localnet/.env."
        )
        sys.exit(1)

    print("Creating subnet...")
    response = subtensor.register_subnet(
        wallet=owner,
        wait_for_inclusion=True,
        wait_for_finalization=True,
        mev_protection=False,
    )
    if not response.success:
        print(f"Subnet registration failed: {response.message}")
        sys.exit(1)

    # The chain auto-assigns the next free netuid; there's no extrinsic to request one.
    # Bail on mismatch so pylon/validator/monitor aren't silently misconfigured.
    new_owner = get_subnet_owner_coldkey(subtensor, EXPECTED_NETUID)
    if new_owner != owner.coldkey.ss58_address:
        print(
            f"Subnet at netuid {EXPECTED_NETUID} is owned by {new_owner}, expected {owner.coldkey.ss58_address}. "
            f"Chain may have assigned a different netuid. "
            f"Reset localnet (`cd localnet && docker compose down -v && rm -rf wallets/*/`) or update NETUID."
        )
        sys.exit(1)
    print(f"Subnet created with netuid {EXPECTED_NETUID}")
    return EXPECTED_NETUID


def activate_subnet(subtensor: bt.Subtensor, owner: Wallet, netuid: int) -> None:
    """Activate a subnet via start_call. Idempotent: noop if already active."""
    if subtensor.is_subnet_active(netuid=netuid):
        print(f"Subnet {netuid} already active")
        return

    current_block = subtensor.get_current_block()
    delay_blocks = subtensor.get_start_call_delay()
    target_block = current_block + delay_blocks + 1
    print(f"Waiting {delay_blocks} blocks to activate subnet (current: {current_block}, target: {target_block})...")
    subtensor.wait_for_block(target_block)

    print("Activating subnet...")
    response = subtensor.start_call(
        wallet=owner,
        netuid=netuid,
        wait_for_inclusion=True,
        wait_for_finalization=True,
        mev_protection=False,
    )
    if not response.success:
        print(f"Subnet activation failed: {response.message}")
        sys.exit(1)
    print(f"Subnet {netuid} activated")


def set_admin_freeze_window(subtensor: bt.Subtensor, sudo: Wallet, window: int) -> None:
    """Set chain-wide AdminFreezeWindow via Sudo. Requires the root key (Alice on localnet). Idempotent."""
    current = subtensor.get_admin_freeze_window()
    if current == window:
        print(f"  admin freeze window already {window}")
        return
    print(f"  Setting admin freeze window {current} -> {window} via sudo...")
    inner = subtensor.compose_call(
        call_module="AdminUtils",
        call_function="sudo_set_admin_freeze_window",
        call_params={"window": window},
    )
    response = subtensor.sign_and_send_extrinsic(
        call=Sudo(subtensor).sudo(inner),
        wallet=sudo,
        wait_for_inclusion=True,
        wait_for_finalization=True,
    )
    if not response.success:
        print(f"  set_admin_freeze_window failed: {response.message}")
        sys.exit(1)
    new_val = subtensor.get_admin_freeze_window()
    if new_val != window:
        print(f"  set_admin_freeze_window failed: on-chain value is {new_val}, expected {window}")
        sys.exit(1)
    print(f"  admin freeze window set to {window}")


def set_subnet_tempo(subtensor: bt.Subtensor, sudo: Wallet, netuid: int, tempo: int) -> None:
    """Set subnet tempo via Sudo. Requires the root key — not callable by subnet owners. Idempotent."""
    current = int(subtensor.get_hyperparameter("Tempo", netuid=netuid))
    if current == tempo:
        print(f"  tempo already {tempo}")
        return
    print(f"  Setting tempo {current} -> {tempo} via sudo...")
    inner = subtensor.compose_call(
        call_module="AdminUtils",
        call_function="sudo_set_tempo",
        call_params={"netuid": netuid, "tempo": tempo},
    )
    response = subtensor.sign_and_send_extrinsic(
        call=Sudo(subtensor).sudo(inner),
        wallet=sudo,
        wait_for_inclusion=True,
        wait_for_finalization=True,
    )
    if not response.success:
        print(f"  set_tempo failed: {response.message}")
        sys.exit(1)
    new_val = int(subtensor.get_hyperparameter("Tempo", netuid=netuid))
    if new_val != tempo:
        print(f"  set_tempo failed: on-chain value is {new_val}, expected {tempo}")
        sys.exit(1)
    print(f"  tempo set to {tempo}")


def set_commit_reveal_enabled(subtensor: bt.Subtensor, owner: Wallet, netuid: int, enabled: bool) -> None:
    """Toggle commit-reveal weight submission on a subnet. Idempotent.

    The AdminUtils extrinsic accepts subnet owner or root.
    """
    current = bool(subtensor.get_hyperparameter("CommitRevealWeightsEnabled", netuid=netuid))
    if current == enabled:
        print(f"  commit-reveal already {'enabled' if enabled else 'disabled'}")
        return
    print(f"  Setting commit-reveal {current} -> {enabled} as subnet owner...")
    call = subtensor.compose_call(
        call_module="AdminUtils",
        call_function="sudo_set_commit_reveal_weights_enabled",
        call_params={"netuid": netuid, "enabled": enabled},
    )
    response = subtensor.sign_and_send_extrinsic(
        call=call,
        wallet=owner,
        wait_for_inclusion=True,
        wait_for_finalization=True,
    )
    if not response.success:
        print(f"  set_commit_reveal failed: {response.message}")
        sys.exit(1)
    # ExtrinsicResponse.success reports inclusion, not inner dispatch — verify state.
    new_val = bool(subtensor.get_hyperparameter("CommitRevealWeightsEnabled", netuid=netuid))
    if new_val != enabled:
        print(f"  set_commit_reveal failed: on-chain value is {new_val}, expected {enabled}")
        sys.exit(1)
    print(f"  commit-reveal {'enabled' if enabled else 'disabled'}")


def register_neuron(subtensor: bt.Subtensor, wallet: Wallet, netuid: int) -> None:
    """Register a neuron if not already registered."""
    if subtensor.is_hotkey_registered(wallet.hotkey.ss58_address, netuid):
        print(f"  {wallet.name} already registered on subnet {netuid}")
        return
    print(f"  Registering {wallet.name} on subnet {netuid}...")
    response = subtensor.burned_register(
        wallet=wallet,
        netuid=netuid,
        wait_for_inclusion=True,
        wait_for_finalization=True,
        mev_protection=False,
    )
    if not response.success:
        print(f"  Registration failed: {response.message}")
        sys.exit(1)
    print(f"  {wallet.name} registered")


def stake_validator(subtensor: bt.Subtensor, wallet: Wallet, netuid: int) -> None:
    """Ensure the validator has the target localnet stake."""
    current_stake = subtensor.get_stake(
        coldkey_ss58=wallet.coldkey.ss58_address,
        hotkey_ss58=wallet.hotkey.ss58_address,
        netuid=netuid,
    )
    target_stake = Balance.from_tao(VALIDATOR_STAKE_TAO, netuid=netuid)
    if current_stake >= target_stake:
        print(f"  {wallet.name} already staked (stake: {current_stake})")
        return

    amount_to_add = Balance.from_tao(target_stake.tao - current_stake.tao)
    print(f"  Staking {amount_to_add} for {wallet.name}...")
    response = subtensor.add_stake(
        wallet=wallet,
        netuid=netuid,
        hotkey_ss58=wallet.hotkey.ss58_address,
        amount=amount_to_add,
        wait_for_inclusion=True,
        wait_for_finalization=True,
        mev_protection=False,
    )
    if not response.success:
        print(f"  Staking failed: {response.message}")
        sys.exit(1)
    print(f"  {wallet.name} staked")


def main() -> None:
    subtensor = wait_for_subtensor(SUBTENSOR_NETWORK)
    alice = get_alice_wallet()

    alice_balance = subtensor.get_balance(alice.coldkey.ss58_address)
    print(f"Alice balance: {alice_balance}")

    # Owner: creates and owns the subnet
    print("\n--- Setting up owner wallet ---")
    owner = get_or_create_wallet("owner")
    fund_wallet(subtensor, alice, owner)

    print("\n--- Creating subnet ---")
    netuid = create_subnet(subtensor, owner)

    print("\n--- Disabling admin freeze window ---")
    set_admin_freeze_window(subtensor, alice, ADMIN_FREEZE_WINDOW)

    print("\n--- Configuring subnet hyperparameters ---")
    set_subnet_tempo(subtensor, alice, netuid, SUBNET_TEMPO)
    set_commit_reveal_enabled(subtensor, owner, netuid, SUBNET_COMMIT_REVEAL_ENABLED)

    print("\n--- Activating subnet ---")
    activate_subnet(subtensor, owner, netuid)

    # Validator: registers and stakes
    print("\n--- Setting up validator ---")
    validator = get_or_create_wallet("validator")
    fund_wallet(subtensor, alice, validator)
    register_neuron(subtensor, validator, netuid)
    stake_validator(subtensor, validator, netuid)

    print("\n--- Bootstrap complete ---")
    print(f"Subnet:    {netuid}")
    print(f"Owner:     {owner.coldkey.ss58_address}")
    print(f"Validator: {validator.hotkey.ss58_address}")
    print(
        "\nNext: start the miner (cd miner && uv run miner) or a localnet fixture (uv run localnet/miners/<profile>.py)"
    )


if __name__ == "__main__":
    main()
