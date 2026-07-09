"""Invariant query tool — machine-readable TAS invariant index lookup (Task 3).

Parses ``tests/invariants.md`` and exposes a CLI and importable API so that
tools and CI pipelines can look up invariant enforcement automatically without
parsing Markdown by hand.

Usage (CLI)::

    python invariant_query.py list
    python invariant_query.py show W1
    python invariant_query.py search "HMAC"
    python invariant_query.py layer 3
    python invariant_query.py json

Usage (API)::

    from invariant_query import InvariantIndex
    idx = InvariantIndex()
    inv = idx.get("W1")
    print(inv.formal_statement)
    print(inv.test_classes)
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


_DEFAULT_INDEX = pathlib.Path(__file__).parent / "tests" / "invariants.md"

# Pattern matching a Markdown table row with 4 pipe-separated cells
_ROW_RE = re.compile(r"^\|\s*\*\*([^*]+)\*\*(?:[^|]*)?\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|")
_LAYER_RE = re.compile(r"^##\s+Layer\s+(\d+)\s+[—–-]\s+(.+?)\s*$")
_CROSS_RE = re.compile(r"^##\s+Cross-cutting", re.IGNORECASE)


@dataclass
class InvariantRecord:
    """A single TAS invariant entry parsed from ``invariants.md``."""

    id: str
    layer: int
    layer_name: str
    formal_statement: str
    source_module: str
    test_classes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


class InvariantIndex:
    """Parsed, queryable index of all TAS invariants.

    Parameters
    ----------
    index_path:
        Path to ``tests/invariants.md``.  Defaults to the bundled copy.
    """

    def __init__(self, index_path: str | pathlib.Path = _DEFAULT_INDEX) -> None:
        self._path = pathlib.Path(index_path)
        self._records: Dict[str, InvariantRecord] = {}
        self._parse()

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get(self, invariant_id: str) -> Optional[InvariantRecord]:
        """Return the record for *invariant_id* (case-insensitive), or None."""
        return self._records.get(invariant_id.upper())

    def list_all(self) -> List[InvariantRecord]:
        """Return all invariants ordered by (layer, id)."""
        return sorted(self._records.values(), key=lambda r: (r.layer, r.id))

    def by_layer(self, layer: int) -> List[InvariantRecord]:
        """Return all invariants in *layer*."""
        return [r for r in self.list_all() if r.layer == layer]

    def search(self, query: str) -> List[InvariantRecord]:
        """Return invariants whose id, statement, or source module match *query* (case-insensitive)."""
        q = query.lower()
        return [
            r for r in self.list_all()
            if q in r.id.lower()
            or q in r.formal_statement.lower()
            or q in r.source_module.lower()
            or any(q in tc.lower() for tc in r.test_classes)
        ]

    def to_json(self) -> str:
        """Return the full index as a JSON string."""
        return json.dumps([r.to_dict() for r in self.list_all()], indent=2)

    def __len__(self) -> int:
        return len(self._records)

    # ------------------------------------------------------------------
    # Parser
    # ------------------------------------------------------------------

    def _parse(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"Invariant index not found: {self._path}")

        current_layer = 0
        current_layer_name = "Unknown"
        cross_cutting = False

        for line in self._path.read_text(encoding="utf-8").splitlines():
            # Detect layer heading
            m_layer = _LAYER_RE.match(line)
            if m_layer:
                current_layer = int(m_layer.group(1))
                current_layer_name = m_layer.group(2).strip()
                cross_cutting = False
                continue

            if _CROSS_RE.match(line):
                cross_cutting = True
                current_layer = 99
                current_layer_name = "Cross-cutting"
                continue

            # Parse table row
            m_row = _ROW_RE.match(line)
            if not m_row:
                continue

            raw_id = m_row.group(1).strip()
            # Extract just the invariant code (e.g. "W1" from "W1 — HMAC integrity")
            inv_id_match = re.match(r"^([A-Z][A-Za-z0-9_]+(?:\s[0-9]+)?)", raw_id)
            if not inv_id_match:
                continue
            inv_id = inv_id_match.group(1).replace(" ", "").upper()

            formal = m_row.group(2).strip()
            source = m_row.group(3).strip()
            test_raw = m_row.group(4).strip()

            # Parse test class references: "TestFoo, TestBar (file.py)"
            test_classes = _parse_test_classes(test_raw)

            self._records[inv_id] = InvariantRecord(
                id=inv_id,
                layer=current_layer,
                layer_name=current_layer_name,
                formal_statement=formal,
                source_module=source,
                test_classes=test_classes,
            )


def _parse_test_classes(raw: str) -> List[str]:
    """Extract test class names from a raw test-class cell string."""
    classes: List[str] = []
    # Remove backticks and asterisks
    cleaned = re.sub(r"[`*]", "", raw)
    # Split on commas, strip parenthetical file refs
    for part in cleaned.split(","):
        part = part.strip()
        # Remove trailing " (filename.py)" references
        part = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        if part:
            classes.append(part)
    return classes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="invariant_query",
        description="Query the TAS invariant index (tests/invariants.md).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all invariants (id, layer, source module).")

    show = sub.add_parser("show", help="Show full details for one invariant.")
    show.add_argument("id", help="Invariant ID (e.g. W1, C2, X5).")

    search = sub.add_parser("search", help="Search invariants by keyword.")
    search.add_argument("query", help="Search term (case-insensitive).")

    layer = sub.add_parser("layer", help="List invariants in a specific layer.")
    layer.add_argument("number", type=int, help="Layer number (1–8, or 99 for cross-cutting).")

    sub.add_parser("json", help="Dump the full index as JSON.")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    idx = InvariantIndex()

    if args.command == "list":
        for r in idx.list_all():
            print(f"{r.id:<8} layer={r.layer:<3} source={r.source_module}")
        print(f"\n{len(idx)} invariants total.")

    elif args.command == "show":
        r = idx.get(args.id)
        if r is None:
            print(f"Unknown invariant: {args.id!r}", file=sys.stderr)
            return 1
        print(f"ID:             {r.id}")
        print(f"Layer:          {r.layer} — {r.layer_name}")
        print(f"Source module:  {r.source_module}")
        print(f"Test classes:   {', '.join(r.test_classes) or '(none)'}")
        print(f"Statement:\n  {r.formal_statement}")

    elif args.command == "search":
        results = idx.search(args.query)
        if not results:
            print(f"No invariants match {args.query!r}.")
        for r in results:
            print(f"{r.id:<8} {r.formal_statement[:80]}")
        print(f"\n{len(results)} result(s).")

    elif args.command == "layer":
        results = idx.by_layer(args.number)
        if not results:
            print(f"No invariants in layer {args.number}.")
        for r in results:
            print(f"{r.id:<8} {r.source_module:<30} {r.formal_statement[:60]}")
        print(f"\n{len(results)} invariant(s) in layer {args.number}.")

    elif args.command == "json":
        print(idx.to_json())

    return 0


if __name__ == "__main__":
    sys.exit(main())
