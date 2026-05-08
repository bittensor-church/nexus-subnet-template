# Setting up production deployment

This document describes how to wire up the production deployment workflow for a subnet built on this template.
The end goal is "operator runs one `curl ... | bash` and gets a healthy validator".

## Branch convention

Two parallel branches per environment:

- `deploy-build-<env>` — pushing here triggers `.github/workflows/build.yml`, which builds the validator
  image and pushes it to `ghcr.io/<owner>/<repo>-<env>:v0-latest`. **No deploy happens.**
- `deploy-config-<env>` — holds the operator-facing config (`envs/deployed/docker-compose.yml`,
  `installer/install.sh`, `installer/update_compose.sh`). Operator hosts cron-pull this branch every 15
  minutes and reconcile the local stack. **No build happens.**

`<env>` is typically `prod` or `staging`. The two are independent — you can build a new `staging` image
without touching `prod` config and vice versa.

## One-time setup after forking the template

1. Replace `<OWNER>/<REPO>` and `<OWNER>/<SUBNET>` placeholders in:
   - `installer/install.sh`
   - `installer/update_compose.sh`
   - `tools/update_compose_digest.py` (REPOSITORY_PREFIX)
   - `envs/deployed/docker-compose.yml` (image: line)
   - `installer/README.md` and `README.md` examples

   Verify with:
   ```sh
   grep -rn '<OWNER>/<REPO>\|<OWNER>/<SUBNET>' installer/ tools/ envs/ .github/
   ```

2. GHCR access:
   - For public images: the default `GITHUB_TOKEN` granted to Actions has `packages: write` and is enough.
   - For private images: create a PAT with `read:packages` and configure the production hosts to log in
     to GHCR with it (`docker login ghcr.io`).

3. Create the build branch and push:
   ```sh
   git checkout -b deploy-build-prod main
   git push -u origin deploy-build-prod
   ```
   Watch `.github/workflows/build.yml` succeed and confirm the image appears in
   `https://github.com/<OWNER>/<REPO>/pkgs/container/<repo>-prod`.

4. Pin the digest into the deployed compose:
   ```sh
   git checkout -b deploy-config-prod main
   uv run --with - tools/update_compose_digest.py
   git add envs/deployed/docker-compose.yml
   git commit -m "chore: pin validator digest"
   git push -u origin deploy-config-prod
   ```

5. On the operator host:
   ```sh
   curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-prod/installer/install.sh | bash
   ```
   (See `installer/README.md` for prerequisites and prompts.)

## Steady-state release flow

Whenever you ship a new validator version:

1. Merge changes into `main` (or wherever your trunk is).
2. Fast-forward `deploy-build-prod` to the trunk and push — the CI builds and pushes a new image.
3. Run `tools/update_compose_digest.py` locally, commit the new digest, and push to `deploy-config-prod`.
4. Within 15 minutes the cron on each operator host pulls the new compose and reconciles `docker compose up -d`.

## Verification

After step 5 above, on the operator host:

```sh
cd ~/nexus-subnet-validator
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=200 pylon
crontab -l | grep NEXUS_SUBNET_VALIDATOR_UPDATE
```

The `pylon` healthcheck must report healthy before `app` starts (compose `depends_on`). On-chain checks
(weights, axon info) follow the same path you used during localnet validation — see
`localnet/README.md`.

## Things to watch for

- The hardcoded `<OWNER>/<REPO>` is intentionally invalid — `curl` returns 404 if forgotten. Don't grep-replace
  with a placeholder that *also* looks like a real path.
- Wallets are mounted **read-only**. The container does not create them — they must already live under the
  configured `HOST_WALLET_DIR` on the host.
- Images are pinned by digest, not tag. `:v0-latest` is only used as the digest source. Operator hosts pull
  the compose by digest reference and never run an unpinned tag.
