from __future__ import annotations

import cffi
import pytest

from reclaimit.exceptions import FFIError
from reclaimit.mobiledevice.client import (
    LibIMobileDeviceClient,
    _LIBIMOBILEDEVICE_CDEF,
    _NativeBindings,
)


def test_discover_returns_devices_from_native_list() -> None:
    ffi = _native_ffi()
    library = FakeLibIMobileDevice(ffi, ["first-udid", "second-udid"])

    devices = LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).discover()

    assert [device.udid for device in devices] == ["first-udid", "second-udid"]
    assert library.freed is True


def test_discover_returns_empty_list_when_native_list_is_null() -> None:
    ffi = _native_ffi()
    library = FakeLibIMobileDevice(ffi, [], null_devices=True)

    devices = LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).discover()

    assert devices == []
    assert library.freed is False


def test_discover_raises_ffi_error_when_library_is_missing() -> None:
    with pytest.raises(FFIError, match="could not load libimobiledevice"):
        LibIMobileDeviceClient("/missing/libimobiledevice.so").discover()


def test_discover_returns_empty_list_when_native_reports_no_device() -> None:
    ffi = _native_ffi()
    library = FakeLibIMobileDevice(ffi, [], status=-3)

    devices = LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).discover()

    assert devices == []
    assert library.freed is False


def test_discover_raises_ffi_error_for_nonzero_native_status() -> None:
    ffi = _native_ffi()
    library = FakeLibIMobileDevice(ffi, [], status=-2)

    with pytest.raises(FFIError, match="status -2"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).discover()

    assert library.freed is False


def test_connect_returns_trusted_device_and_cleans_up_handles() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi)

    device = LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).connect("udid-1")

    assert device.udid == "udid-1"
    assert device.paired is True
    assert device.trusted is True
    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new_with_handshake",
        "lockdownd_client_free",
        "idevice_free",
    ]


def test_connect_raises_when_idevice_new_fails_without_cleanup() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi, idevice_new_statuses=[-2])

    with pytest.raises(FFIError, match="could not open device udid-1: status -2"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).connect("udid-1")

    assert library.calls == ["idevice_new:udid-1"]


def test_connect_cleans_device_when_handshake_fails() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi, handshake_statuses=[-21])

    with pytest.raises(FFIError, match="trusted connection failed: status -21"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).connect("udid-1")

    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new_with_handshake",
        "idevice_free",
    ]


def test_pair_pairs_validates_and_cleans_up_handles() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi)

    device = LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).pair("udid-1")

    assert device.udid == "udid-1"
    assert device.paired is True
    assert device.trusted is True
    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new",
        "lockdownd_pair",
        "lockdownd_client_free",
        "idevice_free",
        "idevice_new:udid-1",
        "lockdownd_client_new_with_handshake",
        "lockdownd_client_free",
        "idevice_free",
    ]


def test_pair_cleans_up_when_pair_call_fails() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi, pair_statuses=[-5])

    with pytest.raises(FFIError, match="pairing failed: status -5"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).pair("udid-1")

    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new",
        "lockdownd_pair",
        "lockdownd_client_free",
        "idevice_free",
    ]


def test_pair_cleans_up_when_validation_fails_after_pairing() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi, handshake_statuses=[-21])

    with pytest.raises(FFIError, match="trusted connection failed: status -21"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).pair("udid-1")

    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new",
        "lockdownd_pair",
        "lockdownd_client_free",
        "idevice_free",
        "idevice_new:udid-1",
        "lockdownd_client_new_with_handshake",
        "idevice_free",
    ]


def test_pair_cleans_device_when_lockdown_client_open_fails() -> None:
    ffi = _native_ffi()
    library = FakeAccessLibrary(ffi, lockdown_statuses=[-17])

    with pytest.raises(FFIError, match="lockdown connection failed: status -17"):
        LibIMobileDeviceClient(_bindings=_NativeBindings(ffi, library)).pair("udid-1")

    assert library.calls == [
        "idevice_new:udid-1",
        "lockdownd_client_new",
        "idevice_free",
    ]


class FakeLibIMobileDevice:
    def __init__(
        self,
        ffi: cffi.FFI,
        udids: list[str],
        *,
        status: int = 0,
        free_status: int = 0,
        null_devices: bool = False,
    ) -> None:
        self._ffi = ffi
        self._status = status
        self._free_status = free_status
        self._null_devices = null_devices
        self._udids = [ffi.new("char[]", udid.encode()) for udid in udids]
        self._device_list = ffi.new("char *[]", len(self._udids) + 1)
        for index, udid in enumerate(self._udids):
            self._device_list[index] = udid
        self._device_list[len(self._udids)] = ffi.NULL
        self.freed = False

    def idevice_get_device_list(self, devices, count) -> int:
        if self._status != 0:
            return self._status

        count[0] = len(self._udids)
        devices[0] = self._ffi.NULL if self._null_devices else self._device_list
        return 0

    def idevice_device_list_free(self, devices) -> int:
        self.freed = True
        return self._free_status


class FakeAccessLibrary:
    def __init__(
        self,
        ffi: cffi.FFI,
        *,
        idevice_new_statuses: list[int] | None = None,
        lockdown_statuses: list[int] | None = None,
        handshake_statuses: list[int] | None = None,
        pair_statuses: list[int] | None = None,
    ) -> None:
        self._ffi = ffi
        self._idevice_new_statuses = idevice_new_statuses or [0]
        self._lockdown_statuses = lockdown_statuses or [0]
        self._handshake_statuses = handshake_statuses or [0]
        self._pair_statuses = pair_statuses or [0]
        self._handles = []
        self.calls: list[str] = []

    def idevice_get_device_list(self, devices, count) -> int:
        devices[0] = self._ffi.NULL
        count[0] = 0
        return 0

    def idevice_device_list_free(self, devices) -> int:
        return 0

    def idevice_new(self, device, udid: bytes) -> int:
        self.calls.append(f"idevice_new:{udid.decode()}")
        status = self._pop_status(self._idevice_new_statuses)
        if status == 0:
            device[0] = self._new_handle("idevice")
        return status

    def idevice_free(self, device) -> int:
        self.calls.append("idevice_free")
        return 0

    def lockdownd_client_new(self, device, client, label: bytes) -> int:
        self.calls.append("lockdownd_client_new")
        assert label == b"reclaimit"
        status = self._pop_status(self._lockdown_statuses)
        if status == 0:
            client[0] = self._new_handle("lockdown")
        return status

    def lockdownd_client_new_with_handshake(self, device, client, label: bytes) -> int:
        self.calls.append("lockdownd_client_new_with_handshake")
        assert label == b"reclaimit"
        status = self._pop_status(self._handshake_statuses)
        if status == 0:
            client[0] = self._new_handle("lockdown")
        return status

    def lockdownd_client_free(self, client) -> int:
        self.calls.append("lockdownd_client_free")
        return 0

    def lockdownd_pair(self, client, options) -> int:
        self.calls.append("lockdownd_pair")
        assert options == self._ffi.NULL
        return self._pop_status(self._pair_statuses)

    def _new_handle(self, kind: str):
        handle = self._ffi.new_handle({"kind": kind, "index": len(self._handles)})
        self._handles.append(handle)
        return self._ffi.cast(f"{kind if kind == 'idevice' else 'lockdownd_client'}_t", handle)

    @staticmethod
    def _pop_status(statuses: list[int]) -> int:
        if len(statuses) == 1:
            return statuses[0]
        return statuses.pop(0)


def _native_ffi() -> cffi.FFI:
    ffi = cffi.FFI()
    ffi.cdef(_LIBIMOBILEDEVICE_CDEF)
    return ffi
