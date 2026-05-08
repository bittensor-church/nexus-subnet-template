# Deployment overview

This template ships a deploy-by-push workflow modeled on the InfiniteHash subnet:

```
┌────────────────────────┐    push    ┌─────────────────────┐    push     ┌─────────────────────────┐
│ developer commits to   │──────────▶│  CI: build.yml      │──image──▶│ ghcr.io/...-<env>:v0-latest│
│ deploy-build-<env>     │            │  push to GHCR       │             └────────────┬────────────┘
└────────────────────────┘            └─────────────────────┘                          │
                                                                              update_compose_digest.py
                                                                                       │
                                                                                       ▼
┌────────────────────────┐    pull    ┌─────────────────────┐    push     ┌─────────────────────────┐
│ host: cron */15 min    │──────────▶│ deploy-config-<env> │◀──────────│ developer commits         │
│ runs update_compose.sh │            │ envs/deployed/...   │             │ pinned digest             │
└──────────┬─────────────┘            └─────────────────────┘             └───────────────────────────┘
           │
           ▼
   docker compose up -d
```

Two parallel branches per environment:

- `deploy-build-<env>` triggers `.github/workflows/build.yml`. No deploy.
- `deploy-config-<env>` is consumed by `installer/update_compose.sh` on operator hosts. No build.

Validator and pylon images in the deployed compose are pinned by digest. The validator digest is refreshed
with `tools/update_compose_digest.py`; the pylon digest is updated deliberately when upgrading the sidecar.

For the operator one-liner and post-fork checklist, see `../installer/README.md`.
For the full subnet-author workflow (first-time setup, steady-state release), see
`../knowledge/tasks.deployment.md`.
