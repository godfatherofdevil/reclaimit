from typer.testing import CliRunner

import reclaimit.cli as cli
from reclaimit.cli import app
from reclaimit.core.models import Device


def test_scan_prints_local_media_rows(tmp_path):
    image = tmp_path / "IMG_0001.JPG"
    image.write_bytes(b"image")

    result = CliRunner().invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert "/IMG_0001.JPG" in result.output
    assert "photo" in result.output


def test_sync_dry_run_plans_from_local_directories_without_mutation(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "IMG_0001.JPG"
    target_file = target / "IMG_0002.JPG"
    source_file.write_bytes(b"source image")
    target_file.write_bytes(b"target image")

    before = {
        "source": sorted(path.relative_to(source).as_posix() for path in source.rglob("*")),
        "target": sorted(path.relative_to(target).as_posix() for path in target.rglob("*")),
        "source_bytes": source_file.read_bytes(),
        "target_bytes": target_file.read_bytes(),
    }

    result = CliRunner().invoke(app, ["sync", "--dry-run", str(source), str(target)])

    assert result.exit_code == 0
    assert "copy_to_target" in result.output
    assert "/IMG_0001.JPG" in result.output
    assert before == {
        "source": sorted(path.relative_to(source).as_posix() for path in source.rglob("*")),
        "target": sorted(path.relative_to(target).as_posix() for path in target.rglob("*")),
        "source_bytes": source_file.read_bytes(),
        "target_bytes": target_file.read_bytes(),
    }


def test_tui_smoke():
    result = CliRunner().invoke(app, ["tui"])

    assert result.exit_code == 0
    assert "Reclaimit" in result.output


def test_pair_uses_device_access_service_without_loading_native_library(monkeypatch):
    monkeypatch.setattr(cli, "LibIMobileDeviceClient", lambda: FakeDeviceClient())

    result = CliRunner().invoke(app, ["pair", "udid-1"])

    assert result.exit_code == 0
    assert "Paired Test Phone (udid-1) paired=True trusted=True" in result.output


def test_connect_uses_device_access_service_without_loading_native_library(monkeypatch):
    monkeypatch.setattr(cli, "LibIMobileDeviceClient", lambda: FakeDeviceClient())

    result = CliRunner().invoke(app, ["connect", "udid-1"])

    assert result.exit_code == 0
    assert "Connected Test Phone (udid-1) paired=True trusted=True" in result.output


class FakeDeviceClient:
    def discover(self) -> list[Device]:
        return []

    def connect(self, udid: str) -> Device:
        return Device(udid=udid, name="Test Phone", paired=True, trusted=True)

    def pair(self, udid: str) -> Device:
        return Device(udid=udid, name="Test Phone", paired=True, trusted=True)

    def disconnect(self, udid: str) -> None:
        return None
