from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src" / "reclaimit"
MOBILEDEVICE_ROOT = SOURCE_ROOT / "mobiledevice"

FORBIDDEN_IMPORT_ROOTS = {"cffi", "ctypes", "libimobiledevice"}


def test_native_imports_are_confined_to_mobiledevice_package() -> None:
    violations: list[str] = []

    for path in _python_files_outside_mobiledevice():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden_module(alias.name):
                        violations.append(f"{_relative(path)}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if _is_forbidden_module(module):
                    violations.append(f"{_relative(path)}:{node.lineno} imports from {module}")

    assert violations == []


def test_cffi_ffi_calls_are_confined_to_mobiledevice_package() -> None:
    violations: list[str] = []

    for path in _python_files_outside_mobiledevice():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_cffi_ffi_call(node.func):
                violations.append(f"{_relative(path)}:{node.lineno} calls cffi.FFI")

    assert violations == []


def _python_files_outside_mobiledevice() -> list[Path]:
    return [
        path
        for path in SOURCE_ROOT.rglob("*.py")
        if not path.is_relative_to(MOBILEDEVICE_ROOT)
    ]


def _is_forbidden_module(module: str) -> bool:
    root = module.split(".", maxsplit=1)[0]
    return root in FORBIDDEN_IMPORT_ROOTS


def _is_cffi_ffi_call(func: ast.expr) -> bool:
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "FFI"
        and isinstance(func.value, ast.Name)
        and func.value.id == "cffi"
    )


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()
