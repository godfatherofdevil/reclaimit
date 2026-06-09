from __future__ import annotations

from reclaimit.mobiledevice.dependencies import (
    LIBIMOBILEDEVICE_BIN_DIR_ENV,
    lookup_native_command,
    lookup_native_library,
    native_command_candidates,
)
from reclaimit.services import Doctor


def test_doctor_prefers_env_command_path_before_path(monkeypatch, tmp_path) -> None:
    env_bin = tmp_path / "env-bin"
    path_bin = tmp_path / "path-bin"
    env_bin.mkdir()
    path_bin.mkdir()
    env_command = env_bin / "idevice_id"
    path_command = path_bin / "idevice_id"
    env_command.write_text("#!/bin/sh\n")
    path_command.write_text("#!/bin/sh\n")
    env_command.chmod(0o755)
    path_command.chmod(0o755)
    monkeypatch.setenv(LIBIMOBILEDEVICE_BIN_DIR_ENV, str(env_bin))
    monkeypatch.setenv("PATH", str(path_bin))

    result = _doctor_result("idevice_id")

    assert result.ok is True
    assert result.path == str(env_command)
    assert result.source == "env"
    assert "source: env" in result.message


def test_command_lookup_uses_path_only_when_env_is_unset(monkeypatch, tmp_path) -> None:
    path_bin = tmp_path / "path-bin"
    path_bin.mkdir()
    path_command = path_bin / "idevice_id"
    path_command.write_text("#!/bin/sh\n")
    path_command.chmod(0o755)
    monkeypatch.delenv(LIBIMOBILEDEVICE_BIN_DIR_ENV, raising=False)
    monkeypatch.setenv("PATH", str(path_bin))

    result = lookup_native_command("idevice_id")

    assert result.ok is True
    assert result.path == str(path_command)
    assert result.source == "PATH"
    assert native_command_candidates("idevice_id") == [path_command]


def test_missing_command_mentions_env_override(monkeypatch) -> None:
    monkeypatch.delenv(LIBIMOBILEDEVICE_BIN_DIR_ENV, raising=False)
    monkeypatch.setenv("PATH", "")

    result = lookup_native_command("idevice_id")

    assert result.ok is False
    assert LIBIMOBILEDEVICE_BIN_DIR_ENV in result.message


def test_library_lookup_ignores_command_bin_dir_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(LIBIMOBILEDEVICE_BIN_DIR_ENV, str(tmp_path))
    monkeypatch.setattr(
        "reclaimit.mobiledevice.dependencies.find_library",
        lambda name: "libimobiledevice-1.0.so.6" if name == "imobiledevice-1.0" else None,
    )

    result = lookup_native_library(
        "libimobiledevice",
        ["imobiledevice-1.0", "imobiledevice", "libimobiledevice-1.0.so"],
    )

    assert result.ok is True
    assert result.path == "libimobiledevice-1.0.so.6"
    assert result.source == "system-library"
    assert str(tmp_path) not in result.message


def _doctor_result(name: str):
    return next(result for result in Doctor().run() if result.name == name)
