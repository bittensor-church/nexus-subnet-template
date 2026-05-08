# Nexus

> A proudly Bittensor-gnostic framework for building production-ready subnets.
>
> [Chi](https://github.com/unconst/Chi)'s brain, Nexus's backbone.

Subnets should be one-shotted, not hand-built. Nexus turns a subnet concept into a production-grade system — even from a
single LLM prompt.

## Usage

1. Clone this repo into your AI coding agent of choice
2. "How do I make [your subnet idea]?"

## What you get

<table>
<tr>
<td width="33%" valign="top">

**Chi**

- Idea → mechanism design
- Proven incentive patterns
- Trust & anti-gaming playbook
- Real subnet case studies

</td>
<td width="34%" valign="top">

**Nexus v0 (current)**

- Production-ready vibe-codable validator
- Transparently reliable subtensor communication
- Prebuilt blocks for common subnet patterns
- Localnet-backed setup for rapid prototyping and keeping your agents on track

</td>
<td width="33%" valign="top">

**Nexus (next steps)**

- Restart resiliency
- Miner <-> validator authentication and encryption
- Autoupdating and dynamic config
- Observability via metrics, Sentry, Grafana
- Supply chain: CI/CD, Docker, PyPI

See [the full comparison](https://bittensor-church.github.io/nexus-template/) for more.

</td>
</tr>
</table>


## Project layout

```
.
├── validator/       # validator package + Dockerfile (uv project, see validator/README.md)
├── miner/           # reference miner skeleton (uv project, see miner/README.md)
├── localnet/        # local subnet stack (subtensor + pylon) and miner fixtures
├── installer/       # operator-side install.sh + update_compose.sh (curl|bash)
├── envs/deployed/   # production docker-compose.yml (pulled by update_compose.sh on operator hosts)
├── tools/           # update_compose_digest.py: pin GHCR digest after each CI build
├── .github/         # CI: ruff/basedpyright/pytest + Docker build & push to GHCR
├── docs/            # short-form documentation (deployment.md, etc.)
└── knowledge/       # AI agent playbooks: bittensor, localnet, deployment, coding QA
```

The repository is **two `uv` projects**, not a single root project. Run dev commands from the relevant
subdirectory, e.g. `cd validator && uv sync`. There is no root `pyproject.toml`.

## Deployment

Operators install a validator with a single command (see `installer/README.md`):

```sh
curl -fsS https://raw.githubusercontent.com/<OWNER>/<REPO>/refs/heads/deploy-config-prod/installer/install.sh | bash
```

Subnet authors: see `knowledge/tasks.deployment.md` for the first-time setup and the steady-state release
flow (push to `deploy-build-<env>` → CI builds image → run `tools/update_compose_digest.py` → push pinned
digest to `deploy-config-<env>` → operator hosts cron-pull within 15 minutes).

## Post-fork checklist

After cloning/forking this template, replace the `<OWNER>/<REPO>` and `<OWNER>/<SUBNET>` placeholders
across:

- `installer/install.sh`
- `installer/update_compose.sh`
- `tools/update_compose_digest.py`
- `envs/deployed/docker-compose.yml`
- `installer/README.md` (and any other example URLs)

Verify with:

```sh
grep -rn '<OWNER>/<REPO>\|<OWNER>/<SUBNET>' installer/ tools/ envs/ .github/
```

The placeholder is intentionally invalid (returns 404 from `curl`) so a forgotten replacement fails fast.

