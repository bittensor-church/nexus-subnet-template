from click.testing import CliRunner
from nexus.v1 import NexusValidator

from validator.main import main
from validator.runtime import Validator
from validator.settings import Settings


def test_cli_help() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "--env-file" in result.output


def test_validator_uses_nexus_base_class() -> None:
    assert issubclass(Validator, NexusValidator)


def test_settings_load_without_required_fields() -> None:
    settings = Settings()

    assert isinstance(settings, Settings)
