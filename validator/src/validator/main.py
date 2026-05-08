from __future__ import annotations

from pathlib import Path

import click
from dotenv import load_dotenv

from validator.runtime import Validator
from validator.settings import Settings


@click.command()
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
def main(env_file: Path | None) -> None:
    load_dotenv(env_file)
    Validator.run(settings_class=Settings)


if __name__ == "__main__":
    main()
