"""Local diagnostics for native dependencies and device access."""

from __future__ import annotations

from reclaimit.mobiledevice import NativeDependencyLookup
from reclaimit.mobiledevice.dependencies import (
    lookup_idevice_id_command,
    lookup_libimobiledevice_library,
    lookup_libusbmuxd_library,
    lookup_usbmuxd_command,
)


class Doctor:
    def run(self) -> list[NativeDependencyLookup]:
        return [
            lookup_libimobiledevice_library(),
            lookup_idevice_id_command(),
            lookup_libusbmuxd_library(),
            lookup_usbmuxd_command(),
        ]
