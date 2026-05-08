# Validator installer

One-liner installer for a validator built on this template.

## Quick install

After replacing `<OWNER>/<REPO>` placeholders (see *Post-fork checklist* below):

```sh
curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-prod/installer/install.sh | bash
```

This will:

1. Create a working directory (default: `~/nexus-subnet-validator/`).
2. Prompt for configuration (network, netuid, wallet name, hotkey, tempo) and write `~/nexus-subnet-validator/.env` (mode 0600).
3. Auto-generate `VALIDATOR_PYLON_OPEN_ACCESS_TOKEN` and `VALIDATOR_PYLON_IDENTITY_TOKEN` via `openssl rand`.
4. Run `update_compose.sh` once to fetch `envs/deployed/docker-compose.yml` and start the stack.
5. Install a `*/15 * * * *` cron entry that re-runs `update_compose.sh` to pull config updates.

## Custom install

```sh
curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-prod/installer/install.sh \
  | bash -s -- [ENV_NAME] [WORKING_DIRECTORY]
```

- `ENV_NAME` — environment label (default: `prod`); selects the `deploy-config-${ENV_NAME}` branch.
- `WORKING_DIRECTORY` — install location (default: `~/nexus-subnet-validator/`).

Example:

```sh
curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-staging/installer/install.sh \
  | bash -s -- staging /opt/my-subnet-validator
```

## Prerequisites

- `docker` with the [compose plugin](https://docs.docker.com/compose/install/linux/)
- `cron` running on the host
- `curl`, `bash`, `openssl`
- A wallet directory on the host (default: `~/.bittensor/wallets`) containing the validator's coldkey and hotkey

## Manual update

```sh
curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-prod/installer/update_compose.sh \
  | bash -s -- prod ~/nexus-subnet-validator
```

## Post-fork checklist

After cloning/forking this template you **must** replace the `<OWNER>/<REPO>` raw GitHub URL placeholders
and the `<OWNER_LOWER>/<REPO_LOWER>` GHCR image placeholders in:

- `installer/install.sh`
- `installer/update_compose.sh`
- `tools/update_compose_digest.py`
- `envs/deployed/docker-compose.yml`

Verify nothing was missed:

```sh
grep -rn '<OWNER>/<REPO>\|<OWNER_LOWER>/<REPO_LOWER>' README.md installer/ tools/ envs/ .github/ knowledge/tasks.deployment.md
```

The placeholder is intentionally invalid (a `curl` against it returns 404) so a forgotten replacement
fails fast instead of silently pulling someone else's config.

## How the deploy flow fits together

```
┌────────────────────────┐    push    ┌─────────────────────┐    push     ┌─────────────────────┐
│ developer commits to   │──────────▶│  CI: build.yml      │──image──▶│ ghcr.io/...-<env>:v0-latest│
│ deploy-build-<env>     │            │  push to GHCR       │             └──────────┬──────────┘
└────────────────────────┘            └─────────────────────┘                        │
                                                                            update_compose_digest.py
                                                                                     │
                                                                                     ▼
┌────────────────────────┐    pull    ┌─────────────────────┐    push     ┌─────────────────────┐
│ host: cron */15 min    │──────────▶│ deploy-config-<env> │◀──────────│ developer commits     │
│ runs update_compose.sh │            │ envs/deployed/...   │             │ pinned digest         │
└──────────┬─────────────┘            └─────────────────────┘             └───────────────────────┘
           │
           ▼
   docker compose up -d
```

See `../knowledge/tasks.deployment.md` for the full operator workflow.
