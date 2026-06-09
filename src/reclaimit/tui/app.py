"""Minimal TUI entrypoint until full Textual screens land."""

from rich.console import Console
from rich.panel import Panel


def run_tui() -> None:
    console = Console()
    console.print(
        Panel(
            "Reclaimit\n\nDevice discovery, pairing, media browsing, sync planning, "
            "transfer progress, conflicts, and diagnostics will live here.",
            title="Reclaimit",
        )
    )

