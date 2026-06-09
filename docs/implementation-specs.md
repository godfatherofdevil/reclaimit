# Implementation Specs

## Spec 1: Make `pytest` and `ruff check` the default quality gate

Goal: `make check` runs the full local gate without a device.

Scope:
- Update `Makefile` only.
- Keep Python 3.12, `venv`, and `pip`; do not add `uv`.

Implementation:
- Add a `lint` target that runs `.venv/bin/python -m ruff check src tests`.
- Add a `check` target that runs `test` and `lint`.
- Keep the existing `test` target running `.venv/bin/python -m pytest`.

Acceptance:
- `python -m venv .venv`
- `. .venv/bin/activate`
- `pip install -e ".[dev]" -r requirements-test.txt`
- `make check`
- The command exits 0 without requiring an iOS device.

## Spec 2: Add local media scanning into `MediaItem`

Goal: scan a local directory into a `Catalog` of `MediaItem` records.

Scope:
- Add scanner code under `src/reclaimit/core` or `src/reclaimit/services`.
- Do not call `libimobiledevice`.
- Use Pydantic domain models already in `src/reclaimit/core/models.py`.

Implementation:
- Implement a function that accepts a root path and returns `Catalog`.
- Include regular files only.
- Store each item path as a stable POSIX-style relative path prefixed with `/`.
- Populate `size`, `modified_at`, and `kind`.
- Classify `.jpg`, `.jpeg`, `.heic`, `.png` as `photo`; `.mov`, `.mp4`, `.m4v` as `video`; unknown extensions as `other`.
- Skip hidden directories and files by default.

Acceptance:
- Add tests with `tmp_path` fixtures.
- Verify nested files, hidden files, media-kind detection, size, and modified time.
- `python -m pytest tests/test_*scanner*.py`

## Spec 3: Make `reclaimit scan` use the local scanner

Goal: `reclaimit scan PATH` prints discovered `MediaItem` rows.

Scope:
- Update `src/reclaimit/cli.py`.
- Reuse the scanner from Spec 2.
- Do not require a connected iOS device.

Implementation:
- Change `scan` to accept a local path argument.
- Render a Rich table with path, kind, size, and modified time.
- Exit non-zero with a clear message when the path does not exist or is not a directory.

Acceptance:
- `reclaimit scan ./tests`
- Output includes at least one file path and kind.
- Add a CLI test using `CliRunner` and `tmp_path`.
- `python -m pytest tests/test_cli.py`

## Spec 4: Make `reclaimit sync --dry-run` plan from scanned catalogs

Goal: dry-run sync compares two real local directories and prints planned actions.

Scope:
- Update CLI behavior only.
- Reuse the planner in `src/reclaimit/core/planner.py`.
- Dry-run must not write, delete, or move files.

Implementation:
- Change `sync` to accept `SOURCE` and `TARGET` directory arguments.
- Scan both directories into catalogs.
- Keep `--dry-run` as the default.
- Keep `--execute` rejected or explicitly unimplemented until transfer execution exists.
- Render action, path, destination path, and reason.

Acceptance:
- Create a source-only file and run `reclaimit sync --dry-run SOURCE TARGET`.
- Output includes a copy action.
- File counts and file contents in both directories are unchanged after the command.
- Add a CLI test for the dry-run no-mutation guarantee.
- `python -m pytest tests/test_cli.py tests/test_planner.py`

## Spec 5: Enforce the `libimobiledevice` boundary

Goal: only `reclaimit.mobiledevice` imports or directly calls native `libimobiledevice`.

Scope:
- Add an automated test.
- Do not implement new native bindings in this spec.

Implementation:
- Add a test that scans `src/reclaimit` Python files.
- Permit `libimobiledevice`, `cffi`, and native symbol references only under `src/reclaimit/mobiledevice`.
- Permit docs and user-facing diagnostic strings outside that package only when they do not import or call native APIs.

Acceptance:
- The test fails if `cffi.FFI`, `ctypes`, or direct `libimobiledevice` imports appear outside `src/reclaimit/mobiledevice`.
- Existing diagnostics still pass.
- `python -m pytest tests/test_mobiledevice_boundary.py`

## Spec 6: Implement the first `reclaimit.mobiledevice` FFI discovery adapter

Goal: `LibIMobileDeviceClient.discover()` returns connected devices through native FFI.

Scope:
- Edit only `src/reclaimit/mobiledevice` and related tests.
- Use `cffi`; do not use subprocess for discovery.
- Normalize native failures into `FFIError`.

Implementation:
- Load `libimobiledevice` from the configured `library_path` or default dynamic linker lookup.
- Bind the minimal discovery symbols needed to list UDIDs and free native memory.
- Return `Device` objects with `udid` populated.
- Keep native handles and memory ownership inside `reclaimit.mobiledevice`.
- Add fake-library tests so CI does not need a real iOS device or native library.

Acceptance:
- Unit tests cover success, no devices, missing library, and non-zero native status.
- Service-layer tests use fakes, not the real adapter.
- `python -m pytest tests/test_mobiledevice*.py`

## Spec 7: Build packages with `/opt/reclaimit/venv`

Goal: Debian and RPM package scripts create an app-owned virtualenv at `/opt/reclaimit/venv`.

Scope:
- Update files under `packaging/` only.
- Use `python -m venv` and `pip`.
- Do not bundle `libimobiledevice` or `usbmuxd`.

Implementation:
- Update Debian and RPM build scripts to create a staging virtualenv at `/opt/reclaimit/venv`.
- Install the project wheel and runtime dependencies into that virtualenv with `pip`.
- Keep `/usr/bin/reclaimit` as the launcher that executes `/opt/reclaimit/venv/bin/reclaimit`.
- Keep package metadata declaring system dependencies on `libimobiledevice` and `usbmuxd`.

Acceptance:
- `packaging/scripts/build-deb.sh` documents or performs the venv build.
- `packaging/scripts/build-rpm.sh` documents or performs the venv build.
- Built package contents include `/opt/reclaimit/venv/bin/reclaimit` and `/usr/bin/reclaimit`.
- `packaging/scripts/reclaimit-launcher` still execs `/opt/reclaimit/venv/bin/reclaimit "$@"`.

## Spec 8: Support explicit `libimobiledevice` tool overrides in `doctor`

Goal: `make doctor` keeps the existing `libimobiledevice` library discovery behavior by default, while allowing an explicit project-owned environment variable to override the directory used for `libimobiledevice` command-line tools.

Problem:
- `Doctor` currently relies on dynamic linker lookup through `ctypes.util.find_library`.
- Some development or packaging environments provide `libimobiledevice` command-line tools outside the process `PATH`.
- The result is a false negative for command diagnostics even though the user has working tools available.
- Reclaimit should not guess local install paths. Local layouts vary by machine, package manager, CI image, and shell setup.

Plan:
- Add one project-owned environment variable for an optional command binary directory.
- Use the override only when that environment variable is set.
- When the environment variable is unset, keep the current command lookup behavior through `PATH`.
- Keep `libimobiledevice` library lookup as-is by default.
- Keep native dependency lookup inside `reclaimit.mobiledevice`.
- Keep `Doctor` as a service-layer consumer of normalized lookup results.

Scope:
- Edit `src/reclaimit/mobiledevice/dependencies.py`, `src/reclaimit/services/diagnostics.py`, docs, and related tests.
- Do not introduce subprocess calls for core sync behavior.
- Do not move native lookup or library-name knowledge outside `reclaimit.mobiledevice`.
- Do not require a real iOS device or installed system library in tests.
- Do not document, suggest, or depend on any local default binary path.

Configuration:
- Add `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR`.
- When set, treat it as the preferred directory for command tools such as `idevice_id`.
- When unset, do not add any project-specific command directory candidates.
- System `PATH` remains the default command lookup.
- Dynamic linker lookup remains the default library lookup.
- The env var applies only to command lookup; it must not alter native library discovery.

Implementation:
- Add a Pydantic diagnostic/dependency model under `reclaimit.mobiledevice`, for example `NativeDependencyLookup`, with fields for `name`, `ok`, `path`, `source`, and `message`.
- Add helper functions in `reclaimit.mobiledevice.dependencies`:
  - `tool_bin_dir_from_env() -> Path | None`
  - `native_library_candidates(names: Sequence[str]) -> list[str]`
  - `native_command_candidates(command: str) -> list[Path]`
- Library candidate order:
  1. Results from `ctypes.util.find_library`.
  2. Existing soname fallbacks such as `libimobiledevice-1.0.so` and `libimobiledevice.so`.
- Command candidate order:
  1. `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR/<command>` when the env var is set.
  2. `shutil.which(command)`.
- Update `LibIMobileDeviceClient` to reuse the shared library-candidate helper instead of owning a separate candidate list.
- Update `Doctor.run()` to report:
  - `libimobiledevice` library lookup
  - `idevice_id` command lookup
  - `libusbmuxd` library lookup
  - `usbmuxd` command lookup
- Diagnostic messages should include the source of the match, for example `env`, `system-library`, or `PATH`.
- Missing command diagnostics should mention `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR`.
- Missing library diagnostics should not suggest a local binary directory or any local install path.

Acceptance:
- With `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR` set to a test directory containing fake command files, diagnostics report env-derived command paths before `PATH` paths.
- With the env var unset, command diagnostics use only the normal `PATH` behavior.
- With the env var set, library diagnostics still use the existing dynamic linker and soname behavior.
- Existing FFI discovery tests still cover missing library and fake native bindings without a real iOS device.
- `python -m pytest tests/test_mobiledevice*.py tests/test_cli.py`

## Spec 9: Implement native pair and connect flows

Goal: `reclaimit pair UDID` and `reclaimit connect UDID` use `libimobiledevice` FFI calls to pair/trust or validate access to a visible iOS device.

Problem:
- `DeviceClient` already defines `connect`, `pair`, and `disconnect`, and the CLI already exposes `pair`.
- `LibIMobileDeviceClient.connect()` and `LibIMobileDeviceClient.pair()` currently raise `FFIError`.
- Reclaimit needs a trusted-device gate before inventory, transfer, and TUI workflows can safely depend on device services.

Scope:
- Edit `src/reclaimit/mobiledevice`, `src/reclaimit/services`, `src/reclaimit/cli.py`, docs, and related tests.
- Keep all native C calls and native handle ownership inside `reclaimit.mobiledevice`.
- Use `cffi`; do not use `idevicepair`, `idevice_id`, or other subprocess calls for core pair/connect behavior.
- Do not implement media inventory, service startup for media providers, or transfer execution in this spec.
- Do not require a real iOS device, `usbmuxd`, or installed native libraries in tests.

Implementation:
- Extend `_LIBIMOBILEDEVICE_CDEF` with the minimal pair/connect symbols and opaque handle types:
  - `idevice_t`
  - `lockdownd_client_t`
  - `idevice_new`
  - `idevice_free`
  - `lockdownd_client_new`
  - `lockdownd_client_new_with_handshake`
  - `lockdownd_client_free`
  - `lockdownd_pair`
- Use a single private label constant such as `b"reclaimit"` for lockdown clients.
- Add private helpers in `reclaimit.mobiledevice.client` to:
  - open an `idevice_t` for one UDID
  - open a lockdown client with or without handshake
  - translate non-zero `idevice_error_t` and `lockdownd_error_t` statuses into `FFIError`
  - free any native handle that was successfully allocated, even when a later step fails
- Implement `connect(udid)` by creating an `idevice_t`, opening `lockdownd_client_new_with_handshake`, freeing the lockdown client and device handle, and returning `Device(udid=udid, paired=True, trusted=True)` on success.
- Implement `pair(udid)` by creating an `idevice_t`, opening `lockdownd_client_new`, calling `lockdownd_pair(client, NULL)`, freeing the lockdown client and device handle, then validating the result through the same handshake path used by `connect`.
- Keep `disconnect(udid)` idempotent. If this spec does not retain long-lived handles, document it as a no-op until service sessions are introduced.
- Add a service-layer wrapper, for example `DeviceAccessService`, that delegates `pair`, `connect`, and `disconnect` to `DeviceClient`.
- Update `reclaimit pair UDID` to use the service-layer wrapper instead of calling `LibIMobileDeviceClient` directly.
- Add `reclaimit connect UDID` that uses the same service-layer wrapper and prints the connected UDID/name plus paired/trusted state.
- Keep user-facing pairing failure messages actionable, especially when the device requires the user to unlock it or accept the trust prompt.
- Avoid adding mutable state to Pydantic domain models for native handles; handles must remain private implementation details.

Acceptance:
- Fake-library tests cover `connect` success, `idevice_new` failure, lockdown handshake failure, and cleanup after partial allocation.
- Fake-library tests cover `pair` success, pair failure, pair success followed by validation failure, and cleanup after every failure path.
- CLI tests cover `pair` and `connect` through fakes or monkeypatching and do not load the native library.
- Boundary tests still fail if `cffi`, `ctypes`, or direct `libimobiledevice` calls appear outside `src/reclaimit/mobiledevice`.
- Existing discovery, doctor, scanner, planner, and dry-run sync tests continue to pass without a real device.
- `python -m pytest tests/test_mobiledevice*.py tests/test_cli.py`
