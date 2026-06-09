"""Device access service."""

from reclaimit.core.interfaces import DeviceClient
from reclaimit.core.models import Device


class DeviceAccessService:
    def __init__(self, client: DeviceClient) -> None:
        self._client = client

    def connect(self, udid: str) -> Device:
        return self._client.connect(udid)

    def pair(self, udid: str) -> Device:
        return self._client.pair(udid)

    def disconnect(self, udid: str) -> None:
        self._client.disconnect(udid)
