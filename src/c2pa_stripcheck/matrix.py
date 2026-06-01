"""Aggregate probe results into a versioned behavior matrix.

The matrix is the crowd-maintained artifact: one row per platform, each with its
latest verdict, plus metadata (schema version, generated timestamp, tool
version). It serializes to JSON and feeds the Markdown/badge renderers.
"""

from __future__ import annotations

import datetime as _dt
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__
from .classify import Verdict
from .probe import ProbeResult

#: Bump when the JSON shape changes incompatibly.
SCHEMA_VERSION = 1


@dataclass
class Matrix:
    rows: list[ProbeResult] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION
    tool_version: str = __version__
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = (
                _dt.datetime.now(_dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat()
            )

    def add(self, result: ProbeResult) -> None:
        self.rows.append(result)

    def counts(self) -> dict[str, int]:
        """Count of each verdict across rows (includes UNTESTED/ERROR)."""
        return dict(Counter(r.verdict for r in self.rows))

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "generated_at": self.generated_at,
            "counts": self.counts(),
            "rows": [r.to_dict() for r in self.rows],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    def write_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json() + "\n", encoding="utf-8")
        return p

    @classmethod
    def from_dict(cls, data: dict) -> "Matrix":
        rows = [ProbeResult(**r) for r in data.get("rows", [])]
        return cls(
            rows=rows,
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            tool_version=data.get("tool_version", __version__),
            generated_at=data.get("generated_at", ""),
        )

    @classmethod
    def load_json(cls, path: str | Path) -> "Matrix":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _badge_color(counts: dict[str, int]) -> str:
    """Pick a shields.io color summarizing the overall picture."""
    stripped = counts.get(Verdict.STRIPPED.value, 0)
    preserved = counts.get(Verdict.PRESERVED.value, 0)
    if stripped and not preserved:
        return "red"
    if stripped and preserved:
        return "yellow"
    if preserved and not stripped:
        return "brightgreen"
    return "lightgrey"


def badge_data(matrix: Matrix) -> dict:
    """Return shields.io-style endpoint JSON summarizing the matrix."""
    counts = matrix.counts()
    tested = sum(
        counts.get(v.value, 0)
        for v in Verdict
    )
    preserved = counts.get(Verdict.PRESERVED.value, 0)
    message = f"{preserved}/{tested} preserve" if tested else "no data"
    return {
        "schemaVersion": 1,
        "label": "C2PA preserved",
        "message": message,
        "color": _badge_color(counts),
    }


def write_badge(matrix: Matrix, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(badge_data(matrix), indent=2) + "\n", encoding="utf-8")
    return p
