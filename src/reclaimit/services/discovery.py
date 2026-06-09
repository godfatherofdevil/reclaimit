"""Device discovery service."""

from reclaimit.core.interfaces import DeviceClient
from reclaimit.core.models import Device


class DiscoveryService:
    def __init__(self, client: DeviceClient) -> None:
        self._client = client

    def list_devices(self) -> list[Device]:
        return self._client.discover()

