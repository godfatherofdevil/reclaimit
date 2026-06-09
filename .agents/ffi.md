# FFI Agent Notes

- Only `src/reclaimit/mobiledevice` may call `libimobiledevice`.
- Prefer `cffi` and keep C declarations close to the adapter using them.
- Wrap native handles in Python classes with explicit close/disconnect behavior.
- Normalize all native status codes into `ReclaimitError` subclasses before leaving the module.
- Use fake `DeviceClient` implementations for service and worker tests.
- Return project Pydantic models from adapters rather than raw native data.

