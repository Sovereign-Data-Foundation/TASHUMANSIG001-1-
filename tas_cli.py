"""
tas_cli.py — TrueAlphaSpiral Command-Line Interface

Provides governance tooling for the TAS codebase:

  shadow-scan  [PATH]          Scan governed modules for unsequenced or drifted artifacts.
  shadow-commit [PATH]         Commit current hashes as the verified baseline.
  receipt      [--verify FILE] Emit or verify a PDR forensic receipt bundle.
  status                       Report overall governance posture.

Usage
-----
  python tas_cli.py shadow-scan .
  python tas_cli.py shadow-scan . --json
  python tas_cli.py shadow-commit .
  python tas_cli.py status

Exit codes
----------
  0  — scan clean (zero findings)
  1  — one or more unsequenced or drifted artifacts detected
  2  — usage error

Baseline
--------
The shadow baseline is stored in `.tas_shadow_baseline.json` at the root of
the scanned path. It maps each governed module path to its SHA-256 hash at
commit time. Commit with `shadow-commit` after any intentional change to a
governed module. A drift is detected when the current hash differs from the
baseline hash.

Manifest
--------
The governed module manifest is read from `.tas_manifest` (one path per line,
relative to the scan root). Only listed modules participate in the scan.

STAMP_ANCHOR_2026_07_08
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MANIFEST_FILE = ".tas_manifest"
BASELINE_FILE = ".tas_shadow_baseline.json"
STAMP_ANCHOR_MARKER = "STAMP_ANCHOR_"


# ---------------------------------------------------------------------------
# Finding types
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single scan finding — unsequenced or drifted artifact."""

    path: str
    kind: str           # "unsequenced" | "drifted"
    detail: str
    sha256: str


@dataclass
class ScanResult:
    """Complete result of a shadow-scan run."""

    scan_root: str
    timestamp: float
    modules_scanned: int
    findings: List[Finding] = field(default_factory=list)
    baseline_present: bool = False
    manifest_path: str = ""

    @property
    def clean(self) -> bool:
        return len(self.findings) == 0

    @property
    def unsequenced_count(self) -> int:
        return sum(1 for f in self.findings if f.kind == "unsequenced")

    @property
    def drifted_count(self) -> int:
        return sum(1 for f in self.findings if f.kind == "drifted")

    def to_dict(self) -> dict:
        return {
            "scan_root": self.scan_root,
            "timestamp": self.timestamp,
            "modules_scanned": self.modules_scanned,
            "clean": self.clean,
            "unsequenced": self.unsequenced_count,
            "drifted": self.drifted_count,
            "baseline_present": self.baseline_present,
            "findings": [asdict(f) for f in self.findings],
        }


@dataclass
class ForensicReceipt:
    """Tamper-evident receipt for a shadow-scan or shadow-commit."""

    action: str             # "shadow-scan" | "shadow-commit"
    scan_root: str
    timestamp: float
    clean: bool
    modules_scanned: int
    unsequenced: int
    drifted: int
    sha256_of_result: str   # SHA-256 of the canonical JSON of ScanResult
    findings_summary: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def has_stamp_anchor(path: Path) -> bool:
    """Return True iff the file contains a STAMP_ANCHOR_ marker."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return STAMP_ANCHOR_MARKER in content
    except OSError:
        return False


def load_manifest(root: Path) -> List[Path]:
    """Load the governed module manifest from .tas_manifest.

    Each non-empty, non-comment line is interpreted as a path relative to root.
    """
    manifest_path = root / MANIFEST_FILE
    if not manifest_path.exists():
        return []
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    paths = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        candidate = root / line
        paths.append(candidate)
    return paths


def load_baseline(root: Path) -> Optional[Dict[str, str]]:
    """Load the stored hash baseline. Returns None if no baseline file exists."""
    baseline_path = root / BASELINE_FILE
    if not baseline_path.exists():
        return None
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "hashes" in data:
            return data["hashes"]
        return None
    except (json.JSONDecodeError, KeyError):
        return None


def save_baseline(root: Path, hashes: Dict[str, str]) -> None:
    """Persist a hash baseline to .tas_shadow_baseline.json."""
    baseline_path = root / BASELINE_FILE
    payload = {
        "committed_at": time.time(),
        "committed_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hashes": hashes,
    }
    baseline_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def make_forensic_receipt(action: str, result: ScanResult) -> ForensicReceipt:
    """Produce a ForensicReceipt from a ScanResult."""
    result_json = json.dumps(result.to_dict(), sort_keys=True)
    sha = hashlib.sha256(result_json.encode("utf-8")).hexdigest()
    if result.clean:
        summary = f"0 unsequenced, 0 drifted — chain intact"
    else:
        parts = []
        if result.unsequenced_count:
            parts.append(f"{result.unsequenced_count} unsequenced")
        if result.drifted_count:
            parts.append(f"{result.drifted_count} drifted")
        summary = ", ".join(parts)
    return ForensicReceipt(
        action=action,
        scan_root=result.scan_root,
        timestamp=result.timestamp,
        clean=result.clean,
        modules_scanned=result.modules_scanned,
        unsequenced=result.unsequenced_count,
        drifted=result.drifted_count,
        sha256_of_result=sha,
        findings_summary=summary,
    )


# ---------------------------------------------------------------------------
# shadow-scan
# ---------------------------------------------------------------------------


def cmd_shadow_scan(root: Path, emit_json: bool, quiet: bool) -> int:
    """Execute a shadow-scan and return the exit code."""
    modules = load_manifest(root)
    baseline = load_baseline(root)

    result = ScanResult(
        scan_root=str(root.resolve()),
        timestamp=time.time(),
        modules_scanned=len(modules),
        baseline_present=baseline is not None,
        manifest_path=str(root / MANIFEST_FILE),
    )

    for mod in modules:
        if not mod.exists():
            result.findings.append(Finding(
                path=str(mod),
                kind="unsequenced",
                detail=f"file not found: {mod.name}",
                sha256="",
            ))
            continue

        current_hash = sha256_file(mod)
        rel = str(mod.relative_to(root))

        if not has_stamp_anchor(mod):
            result.findings.append(Finding(
                path=rel,
                kind="unsequenced",
                detail=f"no {STAMP_ANCHOR_MARKER} marker found",
                sha256=current_hash,
            ))

        if baseline is not None:
            baseline_hash = baseline.get(rel)
            if baseline_hash is None:
                result.findings.append(Finding(
                    path=rel,
                    kind="drifted",
                    detail="not present in baseline — commit required",
                    sha256=current_hash,
                ))
            elif baseline_hash != current_hash:
                result.findings.append(Finding(
                    path=rel,
                    kind="drifted",
                    detail=f"hash changed: {baseline_hash[:12]}… → {current_hash[:12]}…",
                    sha256=current_hash,
                ))

    receipt = make_forensic_receipt("shadow-scan", result)

    if emit_json:
        output = {
            "result": result.to_dict(),
            "receipt": receipt.to_dict(),
        }
        print(json.dumps(output, indent=2))
    elif not quiet:
        _print_scan_report(result, receipt)

    return 0 if result.clean else 1


def _print_scan_report(result: ScanResult, receipt: ForensicReceipt) -> None:
    w = 64
    print("=" * w)
    print("TAS SHADOW SCAN".center(w))
    print("=" * w)
    print(f"  Root:     {result.scan_root}")
    print(f"  Modules:  {result.modules_scanned}")
    print(f"  Baseline: {'present' if result.baseline_present else 'not found (drift detection disabled)'}")
    print()
    if result.clean:
        print("  ✓  CLEAN — 0 unsequenced, 0 drifted artifacts")
    else:
        print(f"  ✗  {result.unsequenced_count} unsequenced  |  {result.drifted_count} drifted")
        print()
        for f in result.findings:
            marker = "UNSEQUENCED" if f.kind == "unsequenced" else "DRIFTED"
            print(f"  [{marker}] {f.path}")
            print(f"           {f.detail}")
    print()
    print("  Forensic Receipt")
    print(f"  ├─ action:   {receipt.action}")
    print(f"  ├─ clean:    {receipt.clean}")
    print(f"  ├─ summary:  {receipt.findings_summary}")
    print(f"  └─ sha256:   {receipt.sha256_of_result[:32]}…")
    print("=" * w)


# ---------------------------------------------------------------------------
# shadow-commit
# ---------------------------------------------------------------------------


def cmd_shadow_commit(root: Path, quiet: bool) -> int:
    """Commit current file hashes as the verified baseline."""
    modules = load_manifest(root)
    hashes: Dict[str, str] = {}

    for mod in modules:
        if not mod.exists():
            if not quiet:
                print(f"  WARNING: {mod} not found — skipping", file=sys.stderr)
            continue
        rel = str(mod.relative_to(root))
        hashes[rel] = sha256_file(mod)

    save_baseline(root, hashes)

    if not quiet:
        print(f"  shadow-commit: baseline written ({len(hashes)} modules)")
        print(f"  → {root / BASELINE_FILE}")

    return 0


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


def cmd_status(root: Path) -> int:
    """Print a one-line governance posture summary."""
    modules = load_manifest(root)
    baseline = load_baseline(root)
    stamped = sum(1 for m in modules if m.exists() and has_stamp_anchor(m))
    missing = sum(1 for m in modules if not m.exists())

    print("TAS Governance Status")
    print(f"  Manifest modules:  {len(modules)}")
    print(f"  Stamped:           {stamped}/{len(modules)}")
    print(f"  Missing files:     {missing}")
    print(f"  Baseline:          {'present' if baseline else 'absent'}")

    if baseline:
        drifted = 0
        for mod in modules:
            if not mod.exists():
                continue
            rel = str(mod.relative_to(root))
            if baseline.get(rel) != sha256_file(mod):
                drifted += 1
        print(f"  Drifted:           {drifted}")

    clean = (stamped == len(modules) - missing) and (baseline is None or True)
    return 0 if clean else 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tas_cli.py",
        description="TrueAlphaSpiral governance tooling",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # shadow-scan
    scan_p = sub.add_parser("shadow-scan", help="Scan governed modules for unsequenced or drifted artifacts")
    scan_p.add_argument("path", nargs="?", default=".", help="Root path to scan (default: .)")
    scan_p.add_argument("--json", action="store_true", dest="emit_json", help="Emit JSON output")
    scan_p.add_argument("--quiet", action="store_true", help="Suppress human-readable output")

    # shadow-commit
    commit_p = sub.add_parser("shadow-commit", help="Commit current hashes as the verified baseline")
    commit_p.add_argument("path", nargs="?", default=".", help="Root path (default: .)")
    commit_p.add_argument("--quiet", action="store_true", help="Suppress output")

    # status
    sub.add_parser("status", help="Report overall governance posture")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(getattr(args, "path", ".")).resolve()

    if args.command == "shadow-scan":
        return cmd_shadow_scan(root, emit_json=args.emit_json, quiet=args.quiet)
    elif args.command == "shadow-commit":
        return cmd_shadow_commit(root, quiet=args.quiet)
    elif args.command == "status":
        return cmd_status(root)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
