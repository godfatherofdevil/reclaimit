"""Project-wide exception types."""


class ReclaimitError(Exception):
    """Base error for expected Reclaimit failures."""


class DeviceError(ReclaimitError):
    """Device discovery, connection, or pairing failed."""


class FFIError(DeviceError):
    """A native libimobiledevice call failed."""


class SyncPlanningError(ReclaimitError):
    """A sync plan cannot be produced safely."""


class TransferError(ReclaimitError):
    """A transfer operation failed."""

