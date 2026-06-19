import pytest

from pyfarm.core.config import (
    MissingEnvVar,
    interpolate_env_vars,
    load_profile,
    parse_env_file,
)


def test_interpolate_replaces_from_supplied_env():
    data = {"token": "${TOK}", "nested": ["${TOK}", 1]}
    out = interpolate_env_vars(data, env={"TOK": "secret"})
    assert out == {"token": "secret", "nested": ["secret", 1]}


def test_interpolate_missing_var_raises():
    with pytest.raises(MissingEnvVar):
        interpolate_env_vars("${ABSENT}", env={})


def test_non_strings_pass_through():
    assert interpolate_env_vars(42, env={}) == 42


def test_parse_env_file_handles_comments_quotes_and_export():
    text = "# comment\nexport A=1\nB=\"two words\"\nC='x'\n\nD=4\n"
    assert parse_env_file(text) == {"A": "1", "B": "two words", "C": "x", "D": "4"}


def test_load_profile_into_environ(tmp_path, monkeypatch):
    (tmp_path / "edge.env").write_text("TELEGRAM_BOT_TOKEN=abc123\n")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    loaded = load_profile("edge", profiles_dir=tmp_path)
    assert loaded == {"TELEGRAM_BOT_TOKEN": "abc123"}
    import os

    assert os.environ["TELEGRAM_BOT_TOKEN"] == "abc123"


def test_load_profile_none_is_noop():
    assert load_profile(None) == {}


def test_load_profile_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profile("nope", profiles_dir=tmp_path)
