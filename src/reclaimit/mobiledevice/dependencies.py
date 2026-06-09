"""Native dependency lookup helpers for the mobiledevice boundary."""

from __future__ import annotations

from ctypes import CDLL
from ctypes.util import find_library
from os import environ
from pathlib import Path
from shutil import which
from typing import Iterable, Sequence

from pydantic import BaseModel, ConfigDict


LIBIMOBILEDEVICE_BIN_DIR_ENV = "RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR"
_LIBIMOBILEDEVICE_LIBRARY_NAMES = [
    "imobiledevice-1.0",
    "imobiledevice",
    "libimobiledevice-1.0.so",
    "libimobiledevice.so",
]
_LIBUSBMUXD_LIBRARY_NAMES = ["usbmuxd", "libusbmuxd.so"]


class NativeDependencyLookup(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    ok: bool
    path: str | None
    source: str
    message: str


def find_native_library(name: str) -> str | None:
    """Return the dynamic linker name/path for a native library."""
    return find_library(name)


def tool_bin_dir_from_env() -> Path | None:
    """Return the explicit command-tool directory override, when configured."""
    value = environ.get(LIBIMOBILEDEVICE_BIN_DIR_ENV)
    if not value:
        return None
    return Path(value).expanduser()


def native_library_candidates(names: Sequence[str]) -> list[str]:
    """Return dynamic-linker matches followed by explicit soname fallbacks."""
    candidates = [find_native_library(name) for name in names]
    candidates.extend(names)
    return _unique_strings(candidate for candidate in candidates if candidate)


def native_command_candidates(command: str) -> list[Path]:
    """Return command lookup candidates from the env override, then PATH."""
    candidates: list[Path] = []
    if bin_dir := tool_bin_dir_from_env():
        candidates.append(bin_dir / command)

    if path := which(command):
        candidates.append(Path(path))

    return _unique_paths(candidates)


def libimobiledevice_library_candidates() -> list[str]:
    return native_library_candidates(_LIBIMOBILEDEVICE_LIBRARY_NAMES)


def lookup_libimobiledevice_library() -> NativeDependencyLookup:
    return lookup_native_library("libimobiledevice", _LIBIMOBILEDEVICE_LIBRARY_NAMES)


def lookup_libusbmuxd_library() -> NativeDependencyLookup:
    return lookup_native_library("libusbmuxd", _LIBUSBMUXD_LIBRARY_NAMES)


def lookup_idevice_id_command() -> NativeDependencyLookup:
    return lookup_native_command("idevice_id")


def lookup_usbmuxd_command() -> NativeDependencyLookup:
    return lookup_native_command("usbmuxd")


def lookup_native_library(name: str, candidate_names: Sequence[str]) -> NativeDependencyLookup:
    for candidate in _find_library_candidates(candidate_names):
        return NativeDependencyLookup(
            name=name,
            ok=True,
            path=candidate,
            source="system-library",
            message=f"{candidate} (source: system-library)",
        )

    for candidate in _unique_strings(candidate_names):
        if not _can_load_library(candidate):
            continue
        return NativeDependencyLookup(
            name=name,
            ok=True,
            path=candidate,
            source="soname-fallback",
            message=f"{candidate} (source: soname-fallback)",
        )

    return NativeDependencyLookup(
        name=name,
        ok=False,
        path=None,
        source="system-library",
        message=f"{name} was not found by the dynamic linker or soname fallback lookup",
    )


def lookup_native_command(command: str) -> NativeDependencyLookup:
    bin_dir = tool_bin_dir_from_env()
    env_path = bin_dir / command if bin_dir else None
    if env_path and env_path.is_file():
        return NativeDependencyLookup(
            name=command,
            ok=True,
            path=str(env_path),
            source="env",
            message=f"{env_path} (source: env)",
        )

    if path := which(command):
        return NativeDependencyLookup(
            name=command,
            ok=True,
            path=path,
            source="PATH",
            message=f"{path} (source: PATH)",
        )

    return NativeDependencyLookup(
        name=command,
        ok=False,
        path=None,
        source="PATH",
        message=(
            f"{command} is not on PATH"
            f"; set {LIBIMOBILEDEVICE_BIN_DIR_ENV} to the directory containing {command}"
        ),
    )


def _find_library_candidates(names: Sequence[str]) -> list[str]:
    return _unique_strings(candidate for candidate in (find_native_library(name) for name in names) if candidate)


def _can_load_library(candidate: str) -> bool:
    try:
        CDLL(candidate)
    except OSError:
        return False
    return True


def _unique_strings(candidates: Iterable[str]) -> list[str]:
    unique_candidates: list[str] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def _unique_paths(candidates: Sequence[Path]) -> list[Path]:
    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates
