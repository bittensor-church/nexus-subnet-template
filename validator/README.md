# Validator

Bittensor subnet validator built on the [Nexus](https://github.com/bittensor-church/bittensor-nexus-library) framework.

This is a sub-project of the `nexus-subnet-template` repository. It is a self-contained `uv` project — all
commands below assume `cwd = validator/`.

## Layout

```
validator/
├── pyproject.toml
├── uv.lock
├── Dockerfile           # multi-stage uv build, runtime: `python -m validator`
├── src/validator/
│   ├── main.py          # click entrypoint
│   ├── settings.py      # Settings(BaseSettings)
│   ├── runtime.py       # Validator(NexusValidator)
│   └── __main__.py      # `python -m validator`
└── tests/
```

## Local development

```sh
cd validator
uv sync --all-groups
uv run python -m validator --help
```

To run against a local subnet (see `../localnet/README.md` for the localnet setup):

```sh
uv run python -m validator --env-file ../localnet/.env
```

## QA gates

All must pass. Run from `validator/`:

```sh
uv run ruff check --fix && uv run ruff format
uv run basedpyright
uv run pytest -q --tb=line -r f
```

## Building the container image

```sh
docker build -t nexus-validator:dev .
docker run --rm nexus-validator:dev python -m validator --help
```

The production deployment uses an image built by GitHub Actions on push to `deploy-build-<env>` and pinned
by digest in `../envs/deployed/docker-compose.yml`. See `../installer/README.md` and
`../knowledge/tasks.deployment.md` for the full deployment workflow.
