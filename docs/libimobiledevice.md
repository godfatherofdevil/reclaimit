# libimobiledevice Integration

Production device access belongs in `reclaimit.mobiledevice`.

Rules:

- Prefer `cffi` for native bindings.
- Keep C handles and memory ownership inside the adapter.
- Translate native status codes into `ReclaimitError` subclasses.
- Keep subprocess probes limited to `doctor` and temporary diagnostics.
- Test service and worker behavior through fake `DeviceClient` and `MediaProvider` implementations.

Diagnostics:

- `reclaimit doctor` uses normal dynamic linker lookup for native libraries.
- Command tools are found through `PATH` by default.
- Set `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR` only when command tools such as `idevice_id`
  live outside `PATH`; the value should be the directory containing those tools.
- `RECLAIMIT_LIBIMOBILEDEVICE_BIN_DIR` does not affect native library lookup.

Initial required coverage:

- device discovery
- connect by UDID
- pair/trust
- service startup
- media inventory providers
- read/write streams for supported providers

Current access flow:

- `reclaimit connect UDID` opens an `idevice_t`, validates trust through a lockdown
  handshake, frees all native handles, and reports paired/trusted state.
- `reclaimit pair UDID` opens a non-handshake lockdown client, runs native pairing,
  frees those handles, then validates trust through the same connect path.
- `disconnect(UDID)` is idempotent and currently a no-op because access operations do
  not retain long-lived native handles. Service-session handles will be introduced with
  media provider startup.
