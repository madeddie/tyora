import pytest

from tyora import tyora


def test_parse_args_missing_args() -> None:
    with pytest.raises(SystemExit):
        _ = tyora.parse_args()


def test_parse_args_command() -> None:
    args = tyora.parse_args(["list"])
    assert args.cmd == "list"


# TODO: functions that use user input or read or write files
def test_create_config() -> None: ...


def test_write_config() -> None: ...


def test_read_config() -> None: ...


def test_get_cookiejar() -> None: ...
