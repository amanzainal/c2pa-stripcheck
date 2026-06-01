"""Render a :class:`Matrix` to Markdown via jinja2, and to a rich console table."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .classify import Verdict
from .matrix import Matrix

_SYMBOLS = {
    Verdict.PRESERVED.value: "✅",
    Verdict.STRIPPED.value: "❌",
    Verdict.RE_SIGNED.value: "🔁",
    Verdict.SOFT_BINDING_RECOVERABLE.value: "🔗",
    "UNTESTED": "⏳",
    "ERROR": "⚠️",
}


def symbol(verdict: str) -> str:
    return _SYMBOLS.get(verdict, "•")


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("c2pa_stripcheck", "templates"),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.globals["symbol"] = symbol
    return env


def render_markdown(matrix: Matrix) -> str:
    """Render the full Markdown matrix report."""
    template = _env().get_template("matrix.md.j2")
    return template.render(
        tool_version=matrix.tool_version,
        schema_version=matrix.schema_version,
        generated_at=matrix.generated_at,
        counts=matrix.counts(),
        rows=matrix.rows,
    )


def write_markdown(matrix: Matrix, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_markdown(matrix), encoding="utf-8")
    return p


def render_console_table(matrix: Matrix):
    """Build a rich Table for terminal display."""
    from rich.table import Table

    table = Table(title="C2PA Content Credentials — Platform Behavior Matrix")
    table.add_column("Platform", style="bold")
    table.add_column("Verdict")
    table.add_column("Reader", style="dim")
    table.add_column("Soft-binding", style="dim")
    table.add_column("Reason", style="dim")

    style_by_verdict = {
        Verdict.PRESERVED.value: "green",
        Verdict.STRIPPED.value: "red",
        Verdict.RE_SIGNED.value: "yellow",
        Verdict.SOFT_BINDING_RECOVERABLE.value: "cyan",
        "UNTESTED": "dim",
        "ERROR": "magenta",
    }
    for r in matrix.rows:
        v_style = style_by_verdict.get(r.verdict, "")
        table.add_row(
            r.display_name,
            f"[{v_style}]{symbol(r.verdict)} {r.verdict}[/{v_style}]",
            r.reader,
            r.soft_binding_id or "—",
            r.reason,
        )
    return table
