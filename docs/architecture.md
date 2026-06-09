# Architecture

Reclaimit uses strict layer boundaries so device access, sync correctness, runtime orchestration, and presentation can evolve independently.

## Dependency Direction

`tui` and `cli` depend on `workers` and `services`.

`workers` depend on `core`, `services`, and `storage`.

`services` depend on `core` interfaces and `mobiledevice` adapters.

`core` depends only on Python standard library domain types.

`mobiledevice` is the only layer allowed to call `libimobiledevice` APIs directly.

## v1 Media Surfaces

Photos, videos, music-like files where accessible, and app document containers are exposed through one `MediaProvider` interface. Providers may land incrementally without changing the planner or TUI.

