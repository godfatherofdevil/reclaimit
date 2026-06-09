"""Typer command line entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from reclaimit.core.models import ConflictPolicy, SyncDirection, SyncPlanEntry
from reclaimit.core.planner import SyncPlanner
from reclaimit.core.scanner import scan_local_media
from reclaimit.mobiledevice import LibIMobileDeviceClient
from reclaimit.services import DeviceAccessService, DiscoveryService, Doctor
from reclaimit.tui.app import run_tui

app = typer.Typer(help="Bidirectional iOS media sync for Linux and Unix-like systems.")
console = Console()


@app.command()
def tui() -> None:
    """Open the terminal UI."""
    run_tui()


@app.command()
def devices() -> None:
    """List visible iOS devices."""
    service = DiscoveryService(LibIMobileDeviceClient())
    try:
        found = service.list_devices()
    except Exception as exc:  # noqa: BLE001 - CLI reports expected native gap cleanly.
        console.print(f"[yellow]Device discovery unavailable:[/yellow] {exc}")
        raise typer.Exit(code=1) from exc

    table = Table("UDID", "Name", "Paired", "Trusted")
    for device in found:
        table.add_row(device.udid, device.name or "", str(device.paired), str(device.trusted))
    console.print(table)


@app.command()
def pair(udid: str = typer.Argument(..., help="Device UDID to pair.")) -> None:
    """Pair or trust an iOS device."""
    service = DeviceAccessService(LibIMobileDeviceClient())
    try:
        device = service.pair(udid)
    except Exception as exc:  # noqa: BLE001
        console.print(
            "[red]Pairing failed:[/red] "
            f"{exc} Unlock the device and accept the trust prompt if prompted."
        )
        raise typer.Exit(code=1) from exc
    console.print(_device_access_message("Paired", device))


@app.command()
def connect(udid: str = typer.Argument(..., help="Device UDID to connect.")) -> None:
    """Validate trusted access to an iOS device."""
    service = DeviceAccessService(LibIMobileDeviceClient())
    try:
        device = service.connect(udid)
    except Exception as exc:  # noqa: BLE001
        console.print(
            "[red]Connection failed:[/red] "
            f"{exc} Unlock the device and accept the trust prompt if prompted."
        )
        raise typer.Exit(code=1) from exc
    console.print(_device_access_message("Connected", device))


@app.command()
def scan(path: Path = typer.Argument(..., help="Local directory to scan.")) -> None:
    """Scan a local directory for media files."""
    scan_path = path.expanduser()
    if not scan_path.exists():
        console.print(f"[red]Scan path does not exist:[/red] {scan_path}")
        raise typer.Exit(code=1)
    if not scan_path.is_dir():
        console.print(f"[red]Scan path is not a directory:[/red] {scan_path}")
        raise typer.Exit(code=1)

    catalog = scan_local_media(scan_path)
    table = Table("Path", "Kind", "Size", "Modified")
    for item in catalog.items:
        modified_at = item.modified_at.isoformat() if item.modified_at else ""
        table.add_row(item.identity, item.kind.value, str(item.size), modified_at)
    console.print(table)


@app.command()
def sync(
    source: Path = typer.Argument(..., help="Source directory to scan."),
    target: Path = typer.Argument(..., help="Target directory to scan."),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Plan only or execute transfers."),
) -> None:
    """Plan or execute a sync."""
    if not dry_run:
        console.print("[red]Sync execution is not implemented yet.[/red]")
        raise typer.Exit(code=1)

    source_path = source.expanduser()
    target_path = target.expanduser()
    _require_directory(source_path, "Source")
    _require_directory(target_path, "Target")

    planner = SyncPlanner()
    source_catalog = scan_local_media(source_path)
    target_catalog = scan_local_media(target_path)
    plan = planner.plan(
        source_catalog,
        target_catalog,
        direction=SyncDirection.BIDIRECTIONAL,
        conflict_policy=ConflictPolicy.SKIP,
        dry_run=True,
    )
    table = Table("Action", "Path", "Destination Path", "Reason")
    for entry in plan.entries:
        table.add_row(
            entry.action.value,
            _entry_path(entry),
            _entry_destination_path(entry),
            entry.reason,
        )
    console.print(table)


@app.command()
def doctor() -> None:
    """Check native dependencies and local device access prerequisites."""
    table = Table("Check", "Status", "Message")
    failed = False
    for result in Doctor().run():
        failed = failed or not result.ok
        table.add_row(result.name, "ok" if result.ok else "missing", result.message)
    console.print(table)
    if failed:
        raise typer.Exit(code=1)


def _require_directory(path: Path, label: str) -> None:
    if not path.exists():
        console.print(f"[red]{label} path does not exist:[/red] {path}")
        raise typer.Exit(code=1)
    if not path.is_dir():
        console.print(f"[red]{label} path is not a directory:[/red] {path}")
        raise typer.Exit(code=1)


def _entry_path(entry: SyncPlanEntry) -> str:
    item = entry.source or entry.target
    return item.identity if item else ""


def _entry_destination_path(entry: SyncPlanEntry) -> str:
    if entry.destination_path:
        return str(entry.destination_path)
    if entry.action.value.endswith("_to_target") and entry.source:
        return entry.source.identity
    if entry.action.value.endswith("_to_source") and entry.target:
        return entry.target.identity
    return ""


def _device_access_message(prefix: str, device: object) -> str:
    name = getattr(device, "name", None)
    udid = getattr(device, "udid")
    paired = getattr(device, "paired")
    trusted = getattr(device, "trusted")
    label = f"{name} ({udid})" if name else udid
    return f"{prefix} {label} paired={paired} trusted={trusted}"


if __name__ == "__main__":
    app()
