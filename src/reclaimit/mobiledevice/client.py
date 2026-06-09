"""FFI-oriented device client.

This module is intentionally the only place in the project that should load or call
libimobiledevice APIs directly.
"""

from __future__ import annotations

import sys
from typing import Any, Protocol

import cffi

from reclaimit.core.interfaces import DeviceClient
from reclaimit.core.models import Device
from reclaimit.exceptions import FFIError
from reclaimit.mobiledevice.dependencies import libimobiledevice_library_candidates


_LIBIMOBILEDEVICE_CDEF = """
typedef int idevice_error_t;
typedef int lockdownd_error_t;
typedef struct idevice_private *idevice_t;
typedef struct lockdownd_client_private *lockdownd_client_t;

idevice_error_t idevice_get_device_list(char ***devices, int *count);
idevice_error_t idevice_device_list_free(char **devices);
idevice_error_t idevice_new(idevice_t *device, const char *udid);
idevice_error_t idevice_free(idevice_t device);
lockdownd_error_t lockdownd_client_new(
    idevice_t device,
    lockdownd_client_t *client,
    const char *label
);
lockdownd_error_t lockdownd_client_new_with_handshake(
    idevice_t device,
    lockdownd_client_t *client,
    const char *label
);
lockdownd_error_t lockdownd_client_free(lockdownd_client_t client);
lockdownd_error_t lockdownd_pair(lockdownd_client_t client, void *options);
"""

_SUCCESS = 0
_NO_DEVICE = -3
_LOCKDOWN_LABEL = b"reclaimit"


class _NativeLibrary(Protocol):
    def idevice_get_device_list(self, devices: Any, count: Any) -> int: ...

    def idevice_device_list_free(self, devices: Any) -> int: ...

    def idevice_new(self, device: Any, udid: bytes) -> int: ...

    def idevice_free(self, device: Any) -> int: ...

    def lockdownd_client_new(self, device: Any, client: Any, label: bytes) -> int: ...

    def lockdownd_client_new_with_handshake(
        self,
        device: Any,
        client: Any,
        label: bytes,
    ) -> int: ...

    def lockdownd_client_free(self, client: Any) -> int: ...

    def lockdownd_pair(self, client: Any, options: Any) -> int: ...


class _NativeBindings:
    def __init__(self, ffi: cffi.FFI, library: _NativeLibrary) -> None:
        self.ffi = ffi
        self.library = library


class LibIMobileDeviceClient(DeviceClient):
    """Thin native adapter for libimobiledevice.

    Native handles and allocated memory stay inside this boundary. Public callers
    receive project models or project exceptions only.
    """

    def __init__(
        self,
        library_path: str | None = None,
        *,
        _bindings: _NativeBindings | None = None,
    ) -> None:
        self.library_path = library_path
        self._bindings = _bindings

    def discover(self) -> list[Device]:
        bindings = self._load_bindings()
        ffi = bindings.ffi
        library = bindings.library
        devices_out = ffi.new("char ***")
        count_out = ffi.new("int *")

        status = library.idevice_get_device_list(devices_out, count_out)
        if status == _NO_DEVICE:
            return []
        if status != _SUCCESS:
            raise FFIError(f"libimobiledevice discovery failed with status {status}")

        devices = devices_out[0]
        if devices == ffi.NULL:
            return []

        try:
            return [
                Device(udid=ffi.string(devices[index]).decode("utf-8", errors="replace"))
                for index in range(count_out[0])
                if devices[index] != ffi.NULL
            ]
        finally:
            free_status = library.idevice_device_list_free(devices)
            if free_status != _SUCCESS:
                raise FFIError(
                    "libimobiledevice device list cleanup failed "
                    f"with status {free_status}"
                )

    def connect(self, udid: str) -> Device:
        bindings = self._load_bindings()
        device = _open_device(bindings, udid)
        lockdown_client = bindings.ffi.NULL

        try:
            lockdown_client = _open_lockdown_client(bindings, device, handshake=True)
            return Device(udid=udid, paired=True, trusted=True)
        finally:
            if lockdown_client != bindings.ffi.NULL:
                _free_lockdown_client(bindings, lockdown_client)
            _free_device(bindings, device)

    def pair(self, udid: str) -> Device:
        bindings = self._load_bindings()
        device = _open_device(bindings, udid)
        lockdown_client = bindings.ffi.NULL

        try:
            lockdown_client = _open_lockdown_client(bindings, device, handshake=False)
            status = bindings.library.lockdownd_pair(lockdown_client, bindings.ffi.NULL)
            if status != _SUCCESS:
                raise FFIError(_lockdown_failure("pairing failed", status))
        finally:
            if lockdown_client != bindings.ffi.NULL:
                _free_lockdown_client(bindings, lockdown_client)
            _free_device(bindings, device)

        return self.connect(udid)

    def disconnect(self, udid: str) -> None:
        """No-op until long-lived service sessions retain native handles."""
        return None

    def _load_bindings(self) -> _NativeBindings:
        if self._bindings is None:
            self._bindings = _load_native_bindings(self.library_path)
        return self._bindings


def _load_native_bindings(library_path: str | None) -> _NativeBindings:
    ffi = cffi.FFI()
    ffi.cdef(_LIBIMOBILEDEVICE_CDEF)

    errors: list[str] = []
    for candidate in _library_candidates(library_path):
        try:
            return _NativeBindings(ffi, ffi.dlopen(candidate))
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")

    detail = "; ".join(errors) if errors else "no library candidates were available"
    raise FFIError(f"could not load libimobiledevice: {detail}")


def _library_candidates(library_path: str | None) -> list[str]:
    if library_path:
        return [library_path]

    return libimobiledevice_library_candidates()


def _open_device(bindings: _NativeBindings, udid: str) -> Any:
    device_out = bindings.ffi.new("idevice_t *")
    status = bindings.library.idevice_new(device_out, udid.encode("utf-8"))
    if status != _SUCCESS:
        raise FFIError(f"libimobiledevice could not open device {udid}: status {status}")
    if device_out[0] == bindings.ffi.NULL:
        raise FFIError(f"libimobiledevice could not open device {udid}: no device handle")
    return device_out[0]


def _open_lockdown_client(
    bindings: _NativeBindings,
    device: Any,
    *,
    handshake: bool,
) -> Any:
    client_out = bindings.ffi.new("lockdownd_client_t *")
    if handshake:
        status = bindings.library.lockdownd_client_new_with_handshake(
            device,
            client_out,
            _LOCKDOWN_LABEL,
        )
        action = "trusted connection failed"
    else:
        status = bindings.library.lockdownd_client_new(device, client_out, _LOCKDOWN_LABEL)
        action = "lockdown connection failed"

    if status != _SUCCESS:
        raise FFIError(_lockdown_failure(action, status))
    if client_out[0] == bindings.ffi.NULL:
        raise FFIError(_lockdown_failure(action, "no lockdown client handle"))
    return client_out[0]


def _free_lockdown_client(bindings: _NativeBindings, client: Any) -> None:
    status = bindings.library.lockdownd_client_free(client)
    if status != _SUCCESS and sys.exception() is None:
        raise FFIError(f"libimobiledevice lockdown cleanup failed with status {status}")


def _free_device(bindings: _NativeBindings, device: Any) -> None:
    status = bindings.library.idevice_free(device)
    if status != _SUCCESS and sys.exception() is None:
        raise FFIError(f"libimobiledevice device cleanup failed with status {status}")


def _lockdown_failure(action: str, status: int | str) -> str:
    return (
        f"libimobiledevice {action}: status {status}. "
        "Unlock the device and accept the trust prompt if one is shown."
    )
