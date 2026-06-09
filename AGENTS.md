# Reclaimit Agent Guide

## Mission

Build Reclaimit as a Python 3.12+ TUI client for bidirectional iOS media sync on Linux and Unix-like systems.

## Development Rules

- Target Python 3.12 and newer.
- Use `python -m venv` and `pip`; do not introduce `uv`.
- Use Pydantic models for public domain, event, diagnostic, and journal data.
- Keep the package in `src/reclaimit`.
- Prefer Typer for CLI commands, Rich for terminal rendering, and Textual if full-screen TUI behavior is needed.
- Keep tests runnable without a real iOS device by default.

## libimobiledevice Boundary

- `reclaimit.mobiledevice` is the only layer allowed to call `libimobiledevice` directly.
- Prefer native FFI through `cffi`.
- Normalize C/library failures into project exceptions.
- Use subprocess calls only for diagnostics or temporary unsupported coverage, and keep them out of core sync logic.

## Layer Ownership

- `core`: media models, catalogs, sync planning, conflict policies, dry-run semantics.
- `mobiledevice`: FFI adapters and native library error translation.
- `services`: device discovery, pairing, inventory, transfers, diagnostics.
- `workers`: cancellable scan/plan/transfer/verify orchestration and typed events.
- `tui`: presentation, keybindings, progress and error rendering.
- `storage`: SQLite catalog state, journals, checksums, and cache metadata.
- `config`: user config, profiles, ignore rules, and state paths.

## Packaging

- Ship native `.deb` and `.rpm` first.
- Packages install dependencies into `/opt/reclaimit/venv` using `pip` during package build.
- Packages declare system dependencies on `libimobiledevice` and `usbmuxd`; do not bundle them initially.

