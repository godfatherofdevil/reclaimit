# Packaging

Initial package targets are native Debian and RPM packages.

## Layout

Packages install Reclaimit under:

- `/opt/reclaimit/venv`
- `/usr/bin/reclaimit`

The launcher executes `/opt/reclaimit/venv/bin/reclaimit`.

## Native Dependencies

Packages declare distro dependencies for:

- `libimobiledevice`
- `usbmuxd`
- Python runtime compatible with Python 3.12 or newer

The package build installs Python dependencies into the app-owned virtualenv with `pip`. Native system libraries are not bundled initially.

## Local Builds

Debian:

```bash
packaging/scripts/build-deb.sh
```

RPM:

```bash
packaging/scripts/build-rpm.sh
```

Build scripts are placeholders until release metadata and distro build environments are finalized.

