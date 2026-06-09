# Media Sync Behavior

The sync planner compares source and target catalogs by stable item identity.

Change detection uses checksum when both sides have one. If checksums are not available, the planner falls back to size and modified time.

Conflict policies:

- `skip`: leave both sides unchanged and report a conflict.
- `overwrite_local`: copy the device/source item over the local/target item.
- `overwrite_device`: copy the local/target item over the device/source item.
- `copy_as_new`: preserve both copies by writing a conflict-copy path.

Dry runs must produce the same plan entries as executable runs without mutating either side.

Deletes are represented as catalog tombstones so the planner can distinguish a known deletion from a file that has not been seen before.

