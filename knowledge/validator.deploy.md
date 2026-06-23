# Validator deploy procedures

This document describes how the **subnet developer** ships changes to operators.

The deploy is split into **three independent procedures**:

1. **Build a new validator image** — pure CI action, produces an artifact in
   the registry. Nothing changes for the operator. Can be run many times
   without ever promoting.
2. **Promote a validator build** — pins a specific built image into
   `envs/deployed/docker-compose.yml` and ships it to operators. Comes after
   procedure 1.
3. **Promote a non-validator service** (e.g. pylon) — pins a new version of
   another service in `envs/deployed/docker-compose.yml` and ships it. Fully
   independent of procedures 1 and 2; can be triggered by an upstream hotfix
   or required by procedure 2 (when the new validator uses features from a
   newer pylon).

In a typical release that introduces a validator-side feature requiring a new
pylon you run procedure 1, then procedure 3 (to land the pylon bump), then
procedure 2 (to land the validator bump with smoke test on the new pylon). In
the most common case — a plain validator bump — you run procedure 1 followed
by procedure 2 only. A pure pylon hotfix is procedure 3 alone.

## The pinning rule (read this first)

> **All image references — in `envs/deployed/docker-compose.yml`, in `docker
> pull` commands, in smoke tests, anywhere — must use `@sha256:<digest>`, the
> Docker manifest digest reported by the registry.**
>
> Tags like `:v0-latest`, `:sha-<commit>`, `:1.4.0`, `:latest` are **mutable
> from the registry's perspective** — anyone with push rights to that
> repository can later re-point the tag at different bytes. They are used
> **once**, to look up the corresponding digest, and then thrown away. Once
> you have a digest, the registry is contractually obliged to serve those
> exact bytes forever.

This rule applies to the validator image we build ourselves **and** to every
third-party image in the stack (pylon, anything else). There is no "but this
tag is semver, so it's safe" exception — the registry doesn't care about
semver.

> Observability sidecars currently ship pinned only by tag (`cadvisor:v0.40.0`,
> `node-exporter:latest`, `bittensor_prometheus:latest`, `grafana/alloy:v1.15.1`)
> rather than by digest. This is a known gap, not an endorsement: when hardening
> the deploy, pin these by `@sha256` too via Procedure 3. The `alloy` traces
> sidecar (see the tracing notes below) follows the same convention as the rest
> of the metrics stack for now.

## The traces sidecar (Alloy)

`envs/deployed/docker-compose.yml` runs a `grafana/alloy` sidecar that tail-samples the
validator's OpenTelemetry spans and forwards them to an OTLP/HTTP upstream. Its config lives
next to the compose file in `envs/deployed/alloy/config.alloy` and is synced to operator hosts
by the same `update_compose.sh` cron job (it now fetches both files). **`TRACES_UPSTREAM_URL` /
`TRACES_UPSTREAM_USER` / `TRACES_UPSTREAM_PASSWORD` are required by the sidecar** — Alloy
refuses to build its exporter without an endpoint and credentials, so with any of them
empty the sidecar crash-loops on startup. Bumping the Alloy image or editing the Alloy
config is a Procedure 3 change (non-validator service) and ships on `deploy-config-<env>`.

> TODO: the intended upstream is the observability proxy (today the Prometheus proxy), mirroring
> metrics — once it supports traces, point the exporter at it and the proxy will add the operator
> `hotkey` label. For now `TRACES_UPSTREAM_URL` can target a Tempo backend (or any OTLP upstream)
> directly.

## Branches and what they do

Two independent branches drive the deploy. They are **not** the same thing —
different consumers, different roles:

- `deploy-build-<env>` — triggers the `build-validator.yml` GitHub Actions
  workflow, which builds the validator image and pushes it to the configured
  registry as `<image_registry>/<github_org>/<image_basename>-<env>:v0-latest`
  and `...:sha-<commit>`. Nothing else reads this branch — it exists to fire CI.
  Used by procedure 1.
- `deploy-config-<env>` — the source of truth for what the **operator** pulls.
  Their cron-driven `update_compose.sh` reads `envs/deployed/docker-compose.yml`
  from this branch and restarts the stack if it changed. The first-time
  `installer/install.sh` is also fetched from here. Used by procedures 2 and 3.

## Procedure 1 — Build a new validator image

Trigger: the developer wants CI to produce a fresh validator image from
`master` (or any working branch). This is just CI — nothing is decided about
operators here.

The default environment is `production` (the branch suffix and the validator's
OTel `deployment.environment.name` attribute share this single value); for other
environments substitute `<env>` consistently.

1. Confirm the source branch is green locally (QA gates), `validator/Dockerfile`
   builds, and the container starts.
2. Fast-forward push the source branch to `deploy-build-<env>`:

   ```sh
   git push origin master:deploy-build-production
   ```

   The `build-validator.yml` workflow (triggered on `deploy-build-*`) builds
   the image and pushes it to the registry as `:v0-latest` and `:sha-<commit>`.
3. Verify in GitHub Actions that the job succeeded and the image landed in the
   registry under `:sha-<commit>`.

Procedure ends here. The artifact exists in the registry; the operator sees
nothing new.

## Procedure 2 — Promote a validator build

Trigger: the developer wants operators to start running a specific image that
was already built in procedure 1.

**Prerequisite:** if this validator release relies on a feature only present
in a newer pylon (or any other service), run **procedure 3 first** for that
service. Otherwise the smoke test in step 2 below would test against the wrong
stack.

1. **Look up the Docker digest of the image built in procedure 1** — without
   pulling it:

   ```sh
   docker buildx imagetools inspect \
     <image_registry>/<github_org>/<image_basename>-production:sha-<commit> \
     --format '{{json .Manifest.Digest}}'
   ```

   Save the resulting `sha256:<digest>`. From this point on, the tag
   `:sha-<commit>` is **never used again** — every subsequent command refers
   to the image by its digest.

2. Smoke test under `envs/deployed/docker-compose.yml` with a real `.env`.
   Pull and run **by digest only**:

   ```sh
   docker pull <image_registry>/<github_org>/<image_basename>-production@sha256:<digest>
   ```

   Bring up the full stack and confirm validator and pylon are healthy. This
   is where you decide whether this particular image is promotable.

3. On `master`, edit `envs/deployed/docker-compose.yml`, the `validator`
   service's `image:` field:

   ```yaml
   image: <image_registry>/<github_org>/<image_basename>-${ENVIRONMENT:?}@sha256:<digest>
   ```

4. Commit (e.g. `chore(deploy): pin production validator to <digest-prefix>`), push
   `master`, then fast-forward `master` → `deploy-config-production`:

   ```sh
   git push origin master:deploy-config-production
   ```

   From this point, the cron-driven `update_compose.sh` on operator hosts will
   pick up the new `docker-compose.yml` and — because the `image:` digest
   changed — restart the stack onto the pinned image.

5. (Recommended for material changes.) Smoke test on a clean Linux host: run
   the `curl ... | bash` command from `installer/README.md`, confirm validator
   and pylon are healthy, the cron line tagged with `cron_tag` is in place,
   and `docker inspect` of the running validator container shows the exact
   digest you pinned in step 3.

## Procedure 3 — Promote a non-validator service (e.g. pylon)

Trigger is one of:

- Procedure 2 needs a newer pylon (or other service) — validator started using
  a feature available from, say, `pylon 1.4.0`.
- The developer explicitly wants to bump a service (e.g. upstream CVE hotfix
  for pylon), independently of any validator build.

This procedure does not depend on procedures 1 or 2 and can be run on its own.

Note: `envs/deployed/docker-compose.yml` ships from this template with a real
pylon digest already pinned (not a placeholder). At template bootstrap time
this procedure is therefore optional — only run it if the freshly built
validator needs a newer pylon than the one the template ships with.

1. Pick the target upstream tag (e.g. `backenddevelopersltd/bittensor-pylon:1.4.0`).
2. **Look up the Docker digest for that tag** — without pulling it:

   ```sh
   docker buildx imagetools inspect \
     backenddevelopersltd/bittensor-pylon:1.4.0 \
     --format '{{json .Manifest.Digest}}'
   ```

   Save the resulting `sha256:<digest>`. From here on, the tag `:1.4.0` is
   **never used again**.

3. Smoke test the full stack under `envs/deployed/docker-compose.yml` with a
   real `.env`, pulling the new service **by digest only**:

   ```sh
   docker pull backenddevelopersltd/bittensor-pylon@sha256:<digest>
   ```

   Use the currently pinned validator and any other currently pinned services.
   For pylon, confirm basic health endpoints respond and that the validator
   can talk to it under the operator's open-access token.

4. On `master`, edit `envs/deployed/docker-compose.yml`, the relevant service's
   `image:` field:

   ```yaml
   image: backenddevelopersltd/bittensor-pylon@sha256:<digest>
   ```

5. Commit (e.g. `chore(deploy): pin production pylon to <digest-prefix>`), push
   `master`, then fast-forward `master` → `deploy-config-production`:

   ```sh
   git push origin master:deploy-config-production
   ```

If procedure 2 needs an accompanying service bump, run procedure 3 first
(landing the service digest commit on `master`), then procedure 2 (the smoke
test runs against the already-pinned new service). If you prefer, both digest
edits can sit in a single commit; the requirement is that the smoke test in
procedure 2 step 2 happens against the stack the operator will end up running.

## Other environments

Mirror the same flow with a matching pair of branches — `deploy-build-<env>`
triggers a CI build of `<image_basename>-<env>:v0-latest`, and
`deploy-config-<env>` is what `installer/install.sh ... <env>` reads from.
Operators select the environment with the `ENV_NAME` argument to `install.sh`.

## After done

The template-bootstrap workflow is complete. Day-to-day releases are
independent runs of procedures 1, 2, and 3 — not always in a fixed pair. Pick
the procedures the change actually requires:

- New validator code only → 1 then 2.
- New validator code that depends on a newer pylon → 1, 3, 2.
- Pylon hotfix only → 3.
- Test build, not yet promoting → 1.

Further changes to the subnet itself fall outside this document.
