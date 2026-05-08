#!/usr/bin/env bash
# Validator one-liner installer.
#
# Idempotent: re-running keeps the existing .env, refreshes docker-compose.yml,
# and reinstalls the cron entry.
#
# FIXME(template): replace <OWNER>/<REPO> below with your fork after cloning the template.
# Sentinel <OWNER>/<REPO> is intentionally invalid so curl returns 404 if forgotten.

set -euo pipefail

GITHUB_URL="https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads"
CRON_MARKER="NEXUS_SUBNET_VALIDATOR_UPDATE"

ENV_NAME="${1:-prod}"
WORKING_DIRECTORY="${2:-${HOME}/nexus-subnet-validator/}"

mkdir -p "${WORKING_DIRECTORY}"
WORKING_DIRECTORY=$(realpath "${WORKING_DIRECTORY}")

ENV_FILE="${WORKING_DIRECTORY}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    echo "Creating .env file at ${ENV_FILE}..."

    read -r -p "Enter BITTENSOR_NETWORK [finney]: " BITTENSOR_NETWORK </dev/tty
    BITTENSOR_NETWORK=${BITTENSOR_NETWORK:-finney}

    while :; do
        read -r -p "Enter BITTENSOR_NETUID (required, no default): " BITTENSOR_NETUID </dev/tty
        BITTENSOR_NETUID=$(echo "${BITTENSOR_NETUID:-}" | tr -d '[:space:]')
        if [[ "${BITTENSOR_NETUID}" =~ ^[0-9]+$ ]]; then
            break
        fi
        echo "BITTENSOR_NETUID must be a non-negative integer."
    done

    read -r -p "Enter HOST_WALLET_DIR [${HOME}/.bittensor/wallets]: " HOST_WALLET_DIR </dev/tty
    HOST_WALLET_DIR=${HOST_WALLET_DIR:-${HOME}/.bittensor/wallets}

    read -r -p "Enter BITTENSOR_WALLET_NAME [validator]: " BITTENSOR_WALLET_NAME </dev/tty
    BITTENSOR_WALLET_NAME=${BITTENSOR_WALLET_NAME:-validator}

    read -r -p "Enter BITTENSOR_WALLET_HOTKEY_NAME [default]: " BITTENSOR_WALLET_HOTKEY_NAME </dev/tty
    BITTENSOR_WALLET_HOTKEY_NAME=${BITTENSOR_WALLET_HOTKEY_NAME:-default}

    read -r -p "Enter SUBNET_TEMPO [360]: " SUBNET_TEMPO </dev/tty
    SUBNET_TEMPO=${SUBNET_TEMPO:-360}
    SUBNET_TEMPO=$(echo "${SUBNET_TEMPO}" | tr -d '[:space:]')

    PYLON_OPEN_ACCESS_TOKEN=$(openssl rand -base64 64 | tr -d '\n\r\t ')
    PYLON_IDENTITY_TOKEN=$(openssl rand -base64 64 | tr -d '\n\r\t ')

    cat > "${ENV_FILE}" << EOL
BITTENSOR_NETWORK=${BITTENSOR_NETWORK}
BITTENSOR_NETUID=${BITTENSOR_NETUID}
HOST_WALLET_DIR=${HOST_WALLET_DIR}
BITTENSOR_WALLET_NAME=${BITTENSOR_WALLET_NAME}
BITTENSOR_WALLET_HOTKEY_NAME=${BITTENSOR_WALLET_HOTKEY_NAME}
SUBNET_TEMPO=${SUBNET_TEMPO}

VALIDATOR_PYLON_SERVICE_ADDRESS=http://pylon:8000
VALIDATOR_PYLON_IDENTITY_NAME=validator
VALIDATOR_PYLON_OPEN_ACCESS_TOKEN=${PYLON_OPEN_ACCESS_TOKEN}
VALIDATOR_PYLON_IDENTITY_TOKEN=${PYLON_IDENTITY_TOKEN}
EOL
    chmod 600 "${ENV_FILE}"
    echo ".env file created (mode 0600)."
else
    echo "Reusing existing .env at ${ENV_FILE}"
fi

UPDATE_SCRIPT="/tmp/nexus_subnet_validator_update_compose.sh"
echo "Fetching update_compose.sh and running it once..."
curl -fsS "${GITHUB_URL}/deploy-config-${ENV_NAME}/installer/update_compose.sh" > "${UPDATE_SCRIPT}"
chmod +x "${UPDATE_SCRIPT}"

if ! "${UPDATE_SCRIPT}" "${ENV_NAME}" "${WORKING_DIRECTORY}"; then
    echo "Error: update_compose.sh failed. Cron entry not installed."
    exit 1
fi

CRON_CMD="*/15 * * * * cd ${WORKING_DIRECTORY} && curl -fsS ${GITHUB_URL}/deploy-config-${ENV_NAME}/installer/update_compose.sh > ${UPDATE_SCRIPT} && chmod +x ${UPDATE_SCRIPT} && ${UPDATE_SCRIPT} ${ENV_NAME} ${WORKING_DIRECTORY} # ${CRON_MARKER}"

(crontab -l 2>/dev/null || echo "") | grep -v "${CRON_MARKER}" | { cat; echo "${CRON_CMD}"; } | crontab -

echo "Cron job installed (${CRON_MARKER}). Runs every 15 minutes."
echo "Environment:       ${ENV_NAME}"
echo "Working directory: ${WORKING_DIRECTORY}"
