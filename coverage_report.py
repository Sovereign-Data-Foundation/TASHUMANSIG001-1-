"""Invariant coverage reporter — shifts the headline from test count to
architectural guarantees.

For every named TAS invariant, this tool reports:
- how many tests directly enforce it (via its registered test classes),
- how many of those are mutation sentinels (from test_regression_mutations.py),
- which test classes provide the coverage,
- a ✅ / ⚠️  status (covered vs uncovered).

Usage::

    python coverage_report.py              # human-readable table
    python coverage_report.py --json       # machine-readable JSON
    python coverage_report.py --summary    # one-liner counts only
    python coverage_report.py --by-layer   # group output by layer

Exit code is 0 iff every invariant has at least one test.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


_TESTS_DIR = pathlib.Path(__file__).parent / "tests"
_MUTATION_FILE = "test_regression_mutations.py"


# ---------------------------------------------------------------------------
# Step 1: collect test counts from source files
# ---------------------------------------------------------------------------


def _count_methods_in_class(tree: ast.Module, class_name: str) -> int:
    """Return the number of test_* methods inside *class_name* in *tree*."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return sum(
                1 for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
            )
    return 0


def _count_module_level_tests(tree: ast.Module) -> int:
    """Return module-level test_* functions (some files use module-level tests)."""
    return sum(
        1 for node in ast.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        for ast in [tree]
    )


def build_class_test_counts() -> Dict[str, int]:
    """Scan all test files and return {ClassName: test_method_count}.

    Also creates a special ``<filename>::module`` key for files that use
    module-level test functions (e.g. test_human_api_bridge.py).
    """
    counts: Dict[str, int] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        # Class-level test methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                n = sum(
                    1 for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child.name.startswith("test_")
                )
                if n:
                    counts[node.name] = counts.get(node.name, 0) + n
        # Module-level test functions — keyed as "<filename>::module"
        module_key = f"{path.name}::module"
        module_n = sum(
            1 for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
        if module_n:
            counts[module_key] = module_n
    return counts


def build_mutation_class_set() -> set:
    """Return the set of test class names defined in test_regression_mutations.py."""
    path = _TESTS_DIR / _MUTATION_FILE
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    return {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


# ---------------------------------------------------------------------------
# Step 2: map invariants → test counts
# ---------------------------------------------------------------------------


@dataclass
class InvariantCoverage:
    """Coverage record for a single TAS invariant."""

    id: str
    layer: int
    layer_name: str
    source_module: str
    test_classes: List[str]
    total_tests: int
    mutation_tests: int
    covered: bool

    @property
    def regular_tests(self) -> int:
        return self.total_tests - self.mutation_tests

    def status_icon(self) -> str:
        if self.total_tests == 0:
            return "⚠️ "
        if self.mutation_tests > 0:
            return "✅+"
        return "✅ "


def compute_coverage() -> List[InvariantCoverage]:
    """Return a coverage record for every invariant in the index."""
    from invariant_query import InvariantIndex

    idx = InvariantIndex()
    class_counts = build_class_test_counts()
    mutation_classes = build_mutation_class_set()

    records: List[InvariantCoverage] = []
    for inv in idx.list_all():
        total = 0
        mut = 0
        for cls in inv.test_classes:
            n = class_counts.get(cls, 0)
            total += n
            if cls in mutation_classes:
                mut += n
        records.append(InvariantCoverage(
            id=inv.id,
            layer=inv.layer,
            layer_name=inv.layer_name,
            source_module=inv.source_module,
            test_classes=inv.test_classes,
            total_tests=total,
            mutation_tests=mut,
            covered=total > 0,
        ))
    return records


# ---------------------------------------------------------------------------
# Step 3: rendering
# ---------------------------------------------------------------------------


def _render_table(records: List[InvariantCoverage], by_layer: bool = False) -> str:
    lines: List[str] = []

    def _fmt_row(r: InvariantCoverage) -> str:
        mut_str = f" (+{r.mutation_tests} mutation)" if r.mutation_tests else ""
        cls_str = ", ".join(r.test_classes[:3])
        if len(r.test_classes) > 3:
            cls_str += f" … +{len(r.test_classes) - 3} more"
        return (
            f"  {r.status_icon()}  {r.id:<6}  "
            f"{r.total_tests:>3} tests{mut_str:<20}  "
            f"[{r.source_module}]  {cls_str}"
        )

    if by_layer:
        from itertools import groupby
        for layer_num, group in groupby(records, key=lambda r: r.layer):
            grp = list(group)
            layer_name = grp[0].layer_name
            lines.append(f"\nLayer {layer_num} — {layer_name}")
            lines.append("─" * 72)
            for r in grp:
                lines.append(_fmt_row(r))
    else:
        lines.append("─" * 72)
        for r in records:
            lines.append(_fmt_row(r))
        lines.append("─" * 72)

    covered = sum(1 for r in records if r.covered)
    total_tests = sum(r.total_tests for r in records)
    mut_tests = sum(r.mutation_tests for r in records)
    lines.append(
        f"\n{covered}/{len(records)} invariants covered  |  "
        f"{total_tests} enforcing tests total  |  "
        f"{mut_tests} mutation sentinels"
    )
    uncovered = [r.id for r in records if not r.covered]
    if uncovered:
        lines.append(f"⚠️  Uncovered: {', '.join(uncovered)}")
    return "\n".join(lines)


def _render_summary(records: List[InvariantCoverage]) -> str:
    covered = sum(1 for r in records if r.covered)
    total_tests = sum(r.total_tests for r in records)
    mut_tests = sum(r.mutation_tests for r in records)
    return (
        f"{covered}/{len(records)} invariants covered — "
        f"{total_tests} enforcing tests ({mut_tests} mutation sentinels)"
    )


def _render_json(records: List[InvariantCoverage]) -> str:
    out = []
    for r in records:
        d = asdict(r)
        d["regular_tests"] = r.regular_tests
        d["status"] = r.status_icon().strip()
        out.append(d)
    return json.dumps(out, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="coverage_report",
        description="Report TAS invariant enforcement coverage.",
    )
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    p.add_argument("--summary", action="store_true", help="One-line summary only.")
    p.add_argument("--by-layer", action="store_true", help="Group output by architectural layer.")
    args = p.parse_args(argv)

    records = compute_coverage()

    if args.json:
        print(_render_json(records))
    elif args.summary:
        print(_render_summary(records))
    else:
        print(_render_table(records, by_layer=args.by_layer))

    uncovered = [r for r in records if not r.covered]
    return 1 if uncovered else 0


if __name__ == "__main__":
    sys.exit(main())
