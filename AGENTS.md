# Context

This project is a template for a Bittensor subnet project. It is meant as a starting point for new projects,
containing the necessary knowledge and structure to quickly bootstrap a new subnet. As an agent, use this
template and modify it as needed. Once you start developing it, update this notice to reflect what the actual
project is about and keep its template origin as a short note.

## Adapting this repository to a new subnet

This template has to be adapted to an actual project at some point. When starting out, refer to the
knowledge/tasks.project-bootstrap.md file. It contains workflows for:

- Designing the subnet
- Implementing the validator
- Setting up localnet
- Adapting this repository to a new subnet
- Generally bootstrapping the project

If your task involves any of these, or the task is not clear, but it appears we are not done with the adapting
yet, adhere strictly to the workflow described in that file and get that done first.

# Project layout

The repository is split into two `uv` projects plus shared infrastructure:

- `validator/` — validator package + `Dockerfile`. **All validator code, `pyproject.toml`, `uv.lock`, and
  `.venv` live here.** Run all dev/QA commands from `validator/` (e.g. `cd validator && uv sync`,
  `cd validator && uv run basedpyright`).
- `miner/` — reference miner skeleton (separate `uv` project; see `miner/README.md`). Not a production
  image — the template intentionally provides no installer for miners.
- `localnet/` — local subnet stack (subtensor + pylon) + miner fixtures (`localnet/miners/`).
- `installer/` — operator-side `install.sh` + `update_compose.sh` (curl|bash flow for production hosts).
- `envs/deployed/docker-compose.yml` — production stack (pylon + validator app); image pinned by digest.
- `tools/update_compose_digest.py` — pin GHCR digest in deployed compose after each CI build.
- `.github/workflows/` — `ci.yml` (QA on PR/main) and `build.yml` (push image to GHCR on
  `deploy-build-<env>` branches).
- `docs/deployment.md`, `knowledge/tasks.deployment.md` — deployment workflow and operator playbook.

There is no root `pyproject.toml`. Do not try to run `uv` commands from the repo root.

# Knowledge base

## Preparing for tasks

Start by discovering the information available in the knowledge base with `find knowledge -type f | sort`
Crucially: Never summarize index files. Never delegate reading indices to agents or exploration tools. During
your tasks and conversations, eagerly read additional files if they could be relevant. After compaction,
re-read indices directly and read relevant files again so as not to forget crucial details.

## Bittensor domain

Whenever Bittensor domain knowledge is required, focus on the Bittensor knowledge files and skip the rest. It
is important to first understand the specifics of the Bittensor ecosystem, work with high-level concepts, and
iterate on the subnet's design rather than jumping straight into implementation details. Designing a subnet is
a complex reasoning process and requires careful consideration on multiple levels.

Contains, among others:

- how to frame subnet ideas into the bittensor ecosystem
- requirements and invariants that must be satisfied by a good subnet design
- theory behind validation, mining, incentives, miner-validator contract
- suggested external integrations and tools in the ecosystem

Index: knowledge/bittensor/INDEX.yaml Recommended subnet design location: ./subnet_design.md (create when
needed)

## Nexus

Nexus is the framework for building Bittensor subnet validators. It replaces the bittensor SDK for validator
development. All validator code runs inside Nexus — it is the complete runtime. You must use Nexus for
implementing the validator.

Nexus provides a large set of reusable components that handle common validator concerns. Before writing any
code, making any decisions, or responding with recommendations — discover what Nexus offers. It will likely
already handle most of the requirements of the subnet you are working on.

The Nexus knowledge base ships with the Nexus package — find it in `.venv` within the installed Nexus package
under `docs/`. Make sure Nexus is installed first (follow this project's package management guidelines). Read
`docs/nexus.md` in the Nexus package — it is the grounding document for all validator implementation work.

Whenever working on validator code, double-check compliance with Nexus's best practices, coding guidelines,
requirements, and correct and optimal usage of Nexus components.

Skip reading Nexus KB for higher level tasks that do not touch the code.

### Pylon

Sidecar subtensor communication proxy. Nexus uses Pylon for all subtensor (blockchain) communication. The pylon
client's source code can be found and inspected in `.venv`.

Skip for higher level tasks that do not touch the code.

## localnet

Local development environment that allows running a subnet locally, as opposed to testnet or mainnet. KB
contains everything needed to set it up and operate it: templates, recipes, requirements, operational
guidelines, best practices, gotchas, and much more.

Index: knowledge/localnet/INDEX.md Localnet resources: localnet/*

Read when working on or debugging issues during development on localnet. Skip for higher level tasks that do
not touch the code.

## Coding guidelines

Location: knowledge/guidelines.coding-and-qa.md

Conventions, tooling, best practices, QA gates, comments, documentation, and more.

Read when working with any kind of code, be it validator, localnet, or any other code in this repository. Skip
for higher level tasks that do not touch the code.

# General hints

- use `uv` instead of `python` for managing dependencies, running scripts, entrypoints, ad-hoc code
    - `uv add ...` / `uv remove ...` / `uv sync` (+ `--all-groups`, `--all-extras`)
    - `uv run --with foo,bar ...` (with temporary dependencies)
    - `uv run python -c '...'` / `uv run some/script.py` (code or script)
    - **always `cd validator/` before `uv` commands for the validator** (or `cd miner/` for the miner).
      There is no root `pyproject.toml`.

# Deployment

Production deployment uses two parallel branches per environment: `deploy-build-<env>` triggers the CI
image build (`.github/workflows/build.yml`), and `deploy-config-<env>` is the source of truth for the
operator-facing compose pulled by `installer/update_compose.sh`. Full workflow lives in
`knowledge/tasks.deployment.md`.

# Documentation rules

Keep README.md, AGENTS.md, tests, docstrings, and code up to date and in sync. If one changes, update the
others. Whenever updated, all information, claims, guides, commands, etc. in these files must be verified and
tested. Take great care to avoid drift between these files.


---

Note: CLAUDE.md and .cursorrules both link to CLAUDE.md - they are all the same file. No need to re-read it. 