"""Command-line interface for c2pa-stripcheck.

Subcommands:
  run        Probe platforms (use --demo for the fully-offline synthetic run).
  matrix     Re-render an existing matrix.json to Markdown / badge.
  list       List known platform adapters and their status.
  readers    Show which manifest readers are available in this environment.

The demo path requires no network, accounts, or GPU.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from . import __version__
from .adapters import list_adapters
from .matrix import Matrix, write_badge
from .report import render_console_table, write_markdown
from .runner import run_demo, run_platforms
from .verify import available_readers

console = Console()


def _emit_outputs(matrix: Matrix, out_dir: Path, *, quiet: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = matrix.write_json(out_dir / "matrix.json")
    md_path = write_markdown(matrix, out_dir / "MATRIX.md")
    badge_path = write_badge(matrix, out_dir / "badge.json")
    if not quiet:
        console.print(render_console_table(matrix))
        console.print()
        console.print(f"[green]Wrote[/green] {json_path}")
        console.print(f"[green]Wrote[/green] {md_path}")
        console.print(f"[green]Wrote[/green] {badge_path}")


def cmd_run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    if args.demo:
        console.print("[bold]Running offline demo with synthetic fixtures...[/bold]")
        matrix = run_demo()
    else:
        if not args.platforms:
            console.print(
                "[red]error:[/red] specify --platform NAME (repeatable) or use "
                "--demo. Real adapters are stubs; see CONTRIBUTING.md."
            )
            return 2
        if not args.asset:
            console.print(
                "[red]error:[/red] --asset PATH (a signed asset) is required when "
                "not using --demo."
            )
            return 2
        if not Path(args.asset).exists():
            console.print(f"[red]error:[/red] asset not found: {args.asset}")
            return 2
        matrix = run_platforms(args.platforms, args.asset)
    _emit_outputs(matrix, out_dir, quiet=args.quiet)
    return 0


def cmd_matrix(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.exists():
        console.print(f"[red]error:[/red] not found: {src}")
        return 2
    matrix = Matrix.load_json(src)
    _emit_outputs(matrix, Path(args.out), quiet=args.quiet)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    from rich.table import Table

    table = Table(title="Known platform adapters")
    table.add_column("Name", style="bold")
    table.add_column("Display")
    table.add_column("Kind")
    table.add_column("Needs account")
    table.add_column("Notes", style="dim")
    for a in list_adapters():
        table.add_row(
            a["name"],
            a["display_name"],
            a["kind"],
            "yes" if a["requires_account"] else "no",
            a["notes"],
        )
    console.print(table)
    console.print(
        "\n[dim]All real adapters are stubs in v0. Implement one or record "
        "observed behavior — see CONTRIBUTING.md.[/dim]"
    )
    return 0


def cmd_readers(args: argparse.Namespace) -> int:
    readers = available_readers()
    console.print("[bold]Available manifest readers (best first):[/bold]")
    for r in readers:
        console.print(f"  • {r}")
    console.print(
        "\n[dim]c2pa-python (optional extra) and c2patool (CLI) give cryptographic "
        "verification; the builtin scanner is always available for offline "
        "structural detection.[/dim]"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="c2pa-stripcheck",
        description="Does platform X strip your C2PA Content Credentials?",
    )
    parser.add_argument(
        "--version", action="version", version=f"c2pa-stripcheck {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="probe platforms (use --demo for offline)")
    p_run.add_argument(
        "--demo",
        action="store_true",
        help="run fully offline against synthetic fixtures (no accounts/network)",
    )
    p_run.add_argument(
        "--platform",
        dest="platforms",
        action="append",
        default=[],
        metavar="NAME",
        help="real platform to probe (repeatable); ignored with --demo",
    )
    p_run.add_argument(
        "--asset", metavar="PATH", help="signed asset to upload (real runs)"
    )
    p_run.add_argument(
        "--out", default="runs/latest", help="output directory (default: runs/latest)"
    )
    p_run.add_argument("--quiet", action="store_true", help="suppress console output")
    p_run.set_defaults(func=cmd_run)

    p_matrix = sub.add_parser("matrix", help="re-render an existing matrix.json")
    p_matrix.add_argument("input", help="path to a matrix.json")
    p_matrix.add_argument("--out", default="runs/latest", help="output directory")
    p_matrix.add_argument("--quiet", action="store_true")
    p_matrix.set_defaults(func=cmd_matrix)

    p_list = sub.add_parser("list", help="list known platform adapters")
    p_list.set_defaults(func=cmd_list)

    p_readers = sub.add_parser("readers", help="show available manifest readers")
    p_readers.set_defaults(func=cmd_readers)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
