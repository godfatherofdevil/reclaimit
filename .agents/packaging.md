# Packaging Agent Notes

- Build native `.deb` and `.rpm` packages first.
- Do not use `fpm` as the primary packaging path.
- Package Python dependencies into `/opt/reclaimit/venv` with `pip` during build.
- Support Python 3.12 and newer; do not pin package metadata to one Python minor without a compatibility reason.
- Expose `/usr/bin/reclaimit` as a small launcher.
- Declare, do not bundle, `libimobiledevice` and `usbmuxd` dependencies.
- `reclaimit doctor` must clearly report missing libraries, daemon access issues, and pairing state failures.

