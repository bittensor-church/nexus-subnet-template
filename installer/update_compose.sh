#!/usr/bin/env bash
# Pulls envs/deployed/docker-compose.yml from the deploy-config-<env> branch
# and reconciles the running stack. Designed to be invoked by the cron entry
# installed by install.sh.
#
# FIXME(template): replace <OWNER>/<REPO> below with your fork after cloning the template.

set -euo pipefail

GITHUB_URL="https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads"

ENV_NAME="${1:-prod}"
WORKING_DIRECTORY="${2:-${HOME}/nexus-subnet-validator/}"

mkdir -p "${WORKING_DIRECTORY}"
cd "${WORKING_DIRECTORY}"

REMOTE_COMPOSE_PATH="envs/deployed/docker-compose.yml"
LOCAL_FILE="${WORKING_DIRECTORY}/docker-compose.yml"
TEMP_FILE="/tmp/nexus_subnet_compose_update.yml"

curl -fsS "${GITHUB_URL}/deploy-config-${ENV_NAME}/${REMOTE_COMPOSE_PATH}" > "${TEMP_FILE}"

if [ ! -f "${LOCAL_FILE}" ]; then
    echo "Local docker-compose.yml does not exist. Creating it."
    cat "${TEMP_FILE}" > "${LOCAL_FILE}"
    UPDATED=true
elif diff -q "${TEMP_FILE}" "${LOCAL_FILE}" > /dev/null; then
    echo "No changes detected in docker-compose.yml"
    UPDATED=false
else
    echo "Changes detected in docker-compose.yml. Updating..."
    cat "${TEMP_FILE}" > "${LOCAL_FILE}"
    UPDATED=true
fi

if [ "${UPDATED}" = true ]; then
    echo "Reconciling services..."
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose pull
        docker compose up -d --remove-orphans
    elif command -v docker-compose &> /dev/null; then
        docker-compose pull
        docker-compose up -d --remove-orphans
    else
        echo "Error: Neither docker compose nor docker-compose is available."
        exit 1
    fi
    echo "Services reconciled."
fi

echo "Update process completed for environment '${ENV_NAME}'."
