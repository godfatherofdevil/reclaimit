# Architecture Agent Notes

- Keep dependency direction one-way: presentation -> workers/services -> core/mobiledevice/storage.
- `core` must not import `services`, `mobiledevice`, `workers`, or UI modules.
- Add interfaces in `core.interfaces` when a boundary needs a contract.
- Use Pydantic `BaseModel` for public domain and event contracts shared across layers.
- Providers should implement `MediaProvider`; do not special-case photos or documents in the planner.

