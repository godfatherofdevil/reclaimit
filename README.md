# Reclaimit

Reclaimit is a Python 3.12+ terminal client for bidirectional iOS media sync on Linux and Unix-like systems.

The project is designed around a native `libimobiledevice` FFI boundary, testable fake device clients, and a TUI-first workflow for discovering devices, pairing, browsing media, planning syncs, executing transfers, resolving conflicts, and running diagnostics.

## Development

Use standard `venv` and `pip`:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Run smoke tests:

```bash
python -m pytest
```

Useful commands:

```bash
reclaimit devices
reclaimit sync --dry-run
reclaimit doctor
reclaimit tui
```

## Native Dependencies

Reclaimit does not bundle `libimobiledevice` or `usbmuxd`. Linux packages declare those as system dependencies, and `reclaimit doctor` reports missing libraries, daemon access problems, and pairing state issues.

## Packaging

Initial package targets are native `.deb` and `.rpm` artifacts. Packages install a Reclaimit-owned virtualenv under `/opt/reclaimit/venv` and expose `/usr/bin/reclaimit` as a launcher.

See [docs/packaging.md](/home/akumar/playground/oss/reclaimit/docs/packaging.md).

