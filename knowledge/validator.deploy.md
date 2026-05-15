# Validator deploy procedure

This document describes how the **subnet developer** ships a validator release. The operator side
(running `install.sh` / cron-driven `update_compose.sh`) is out of scope here — see
`installer/README.md` for that.

## Branches and what they do

Two independent branches drive the deploy. They are **not** the same thing — different consumers,
different roles:

- `deploy-build-<env>` — triggers the `build-validator.yml` GitHub Actions workflow, which builds
  the validator image and pushes it to the configured registry as
  `<image_registry>/<github_org>/<image_basename>-<env>:v0-latest` and `...:sha-<commit>`. Nothing
  else reads this branch — it exists to fire CI.
- `deploy-config-<env>` — the source of truth for what the **operator** pulls. Their cron-driven
  `update_compose.sh` reads `envs/deployed/docker-compose.yml` from this branch and restarts the
  stack if it changed. The first-time `installer/install.sh` is also fetched from here.

## Why pin by image digest, not by tag

The validator image tags `:v0-latest` and `:sha-<commit>` are mutable — `:v0-latest` is rewritten
on every CI build, and even `:sha-<commit>` could theoretically be re-pushed. Operators must run
**exactly** the image the developer smoke-tested, so the production
`envs/deployed/docker-compose.yml` references the image by its **content-addressable digest**:

```yaml
image: <image_registry>/<github_org>/<image_basename>-<env>@sha256:<digest>
```

The `<digest>` here is the SHA256 of the **Docker image manifest** as reported by the registry —
not a git commit SHA. Once a digest is pinned, the registry will only ever serve those exact
bytes; operators are immune to a later `:v0-latest` re-tag. Bumping the validator on operators
is a deliberate act: a new digest pin commit on `master`, fast-forwarded to `deploy-config-<env>`.

## Promotion procedure (developer-side)

The default environment is `prod`; for other environments substitute `<env>` consistently.

1. Confirm `master` is green locally (QA gates), `validator/Dockerfile` builds, and the container
   starts. The operator-facing files (`installer/install.sh`, `installer/update_compose.sh`,
   `envs/deployed/docker-compose.yml`, `installer/README.md`) are consistent with the current
   validator code.
2. Fast-forward push `master` to `deploy-build-prod`:

   ```sh
   git push origin master:deploy-build-prod
   ```

   The `build-validator.yml` workflow (triggered on `deploy-build-*`) builds the image and pushes
   it to the registry as `:v0-latest` and `:sha-<commit>`. Verify in GitHub Actions that the job
   succeeded and that the image landed in the registry.
3. Pull the freshly built image locally by its commit-SHA tag and verify it starts under
   `envs/deployed/docker-compose.yml` with a real `.env`:

   ```sh
   docker pull <image_registry>/<github_org>/<image_basename>-prod:sha-<commit>
   ```

   Only continue once this passes.
4. Get the registry digest of the image you just verified and pin it in
   `envs/deployed/docker-compose.yml` on `master`:

   ```sh
   # one of these (the second works on a freshly pulled image):
   docker buildx imagetools inspect \
     <image_registry>/<github_org>/<image_basename>-prod:sha-<commit> \
     --format '{{json .Manifest.Digest}}'

   docker inspect --format='{{index .RepoDigests 0}}' \
     <image_registry>/<github_org>/<image_basename>-prod:sha-<commit>
   ```

   Edit the `validator` service in `envs/deployed/docker-compose.yml`:

   ```yaml
   image: <image_registry>/<github_org>/<image_basename>-${ENVIRONMENT:?}@sha256:<digest>
   ```

   Commit on `master` (e.g. `chore(deploy): pin prod validator to <digest-prefix>`) and push.
5. Fast-forward push `master` to `deploy-config-prod`:

   ```sh
   git push origin master:deploy-config-prod
   ```

   From this point, the cron-driven `update_compose.sh` on operator hosts will pick up the new
   `docker-compose.yml` and — because the `image:` digest changed — restart the stack onto the
   pinned image.
6. Smoke test on a clean Linux host (a fresh VM or container, not the developer's laptop):
   run the `curl ... | bash` command from `installer/README.md`, then confirm validator and
   pylon are healthy and the cron line tagged with `cron_tag` is in place. Sanity-check that
   `docker inspect` of the running validator container shows the digest you pinned in step 4.

## Other environments

Mirror the same flow with a matching pair of branches — `deploy-build-<env>` triggers a CI build
of `<image_basename>-<env>:v0-latest`, and `deploy-config-<env>` is what
`installer/install.sh ... <env>` reads from. Operators select the environment with the `ENV_NAME`
argument to `install.sh`.

## After done

The template-bootstrap workflow is complete. Subsequent releases are repeats of steps 2–5 above
(build → verify → pin digest → promote); further changes to the subnet itself fall outside this
document.
