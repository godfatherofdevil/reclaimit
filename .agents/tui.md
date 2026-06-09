# TUI Agent Notes

- TUI owns presentation only.
- Screens should cover devices, pairing state, source/destination browsing, sync plan preview, transfer progress, conflicts, and diagnostics.
- Workers emit typed events; the TUI subscribes and renders status, progress, warnings, errors, and completion.
- Keep real device access behind services so TUI tests can use fakes.

