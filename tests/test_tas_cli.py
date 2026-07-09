"""
Tests for tas_cli.py — TrueAlphaSpiral Shadow Scan CLI

Verifies:
  1. Manifest loading
  2. STAMP_ANCHOR detection
  3. SHA-256 hashing
  4. shadow-scan: clean result on all-stamped modules
  5. shadow-scan: finds unsequenced artifact (missing stamp)
  6. shadow-scan: finds drifted artifact (hash changed)
  7. shadow-commit: writes and structures baseline correctly
  8. ForensicReceipt fields
  9. ScanResult properties
  10. CLI exit codes via main()

STAMP_ANCHOR_2026_07_08
"""

import json
import tempfile
from pathlib import Path

import pytest

from tas_cli import (
    BASELINE_FILE,
    MANIFEST_FILE,
    STAMP_ANCHOR_MARKER,
    Finding,
    ForensicReceipt,
    ScanResult,
    cmd_shadow_commit,
    cmd_shadow_scan,
    has_stamp_anchor,
    load_baseline,
    load_manifest,
    main,
    make_forensic_receipt,
    save_baseline,
    sha256_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_root(tmp_path):
    """Provide a temp directory with a manifest and two stamped modules."""
    # module A — stamped
    a = tmp_path / "module_a.py"
    a.write_text('"""Module A."""\n# STAMP_ANCHOR_2026_07_08\n\nx = 1\n')
    # module B — stamped
    b = tmp_path / "module_b.py"
    b.write_text('"""Module B."""\n# STAMP_ANCHOR_2026_07_08\n\ny = 2\n')
    # manifest
    manifest = tmp_path / MANIFEST_FILE
    manifest.write_text("module_a.py\nmodule_b.py\n")
    return tmp_path


@pytest.fixture
def unstamped_root(tmp_path):
    """Temp dir with one stamped and one unstamped module."""
    a = tmp_path / "good.py"
    a.write_text("# STAMP_ANCHOR_2026_07_08\nx = 1\n")
    b = tmp_path / "bad.py"
    b.write_text("# no anchor here\ny = 2\n")
    manifest = tmp_path / MANIFEST_FILE
    manifest.write_text("good.py\nbad.py\n")
    return tmp_path


# ---------------------------------------------------------------------------
# sha256_file
# ---------------------------------------------------------------------------

class TestSha256File:
    def test_returns_64_char_hex(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("hello")
        h = sha256_file(f)
        assert len(h) == 64
        int(h, 16)  # valid hex

    def test_different_content_different_hash(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("aaa")
        b.write_text("bbb")
        assert sha256_file(a) != sha256_file(b)

    def test_same_content_same_hash(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("same content")
        b.write_text("same content")
        assert sha256_file(a) == sha256_file(b)


# ---------------------------------------------------------------------------
# has_stamp_anchor
# ---------------------------------------------------------------------------

class TestHasStampAnchor:
    def test_detects_anchor(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("# STAMP_ANCHOR_2026_07_08\n")
        assert has_stamp_anchor(f) is True

    def test_no_anchor(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("# no stamp here\n")
        assert has_stamp_anchor(f) is False

    def test_anchor_anywhere_in_file(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("import os\n\n# STAMP_ANCHOR_2099_01_01\n\npass\n")
        assert has_stamp_anchor(f) is True

    def test_missing_file_returns_false(self, tmp_path):
        f = tmp_path / "nonexistent.py"
        assert has_stamp_anchor(f) is False

    def test_partial_match_not_detected(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("# STAMP_\n")  # prefix only
        assert has_stamp_anchor(f) is False


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------

class TestLoadManifest:
    def test_loads_two_modules(self, tmp_root):
        modules = load_manifest(tmp_root)
        assert len(modules) == 2

    def test_paths_are_absolute(self, tmp_root):
        modules = load_manifest(tmp_root)
        for m in modules:
            assert m.is_absolute()

    def test_missing_manifest_returns_empty(self, tmp_path):
        assert load_manifest(tmp_path) == []

    def test_ignores_comment_lines(self, tmp_path):
        manifest = tmp_path / MANIFEST_FILE
        manifest.write_text("# comment\nmodule_a.py\n")
        modules = load_manifest(tmp_path)
        assert len(modules) == 1

    def test_ignores_blank_lines(self, tmp_path):
        manifest = tmp_path / MANIFEST_FILE
        manifest.write_text("\nmodule_a.py\n\nmodule_b.py\n")
        modules = load_manifest(tmp_path)
        assert len(modules) == 2


# ---------------------------------------------------------------------------
# load_baseline / save_baseline
# ---------------------------------------------------------------------------

class TestBaseline:
    def test_no_baseline_returns_none(self, tmp_path):
        assert load_baseline(tmp_path) is None

    def test_save_then_load(self, tmp_path):
        hashes = {"module_a.py": "abc123", "module_b.py": "def456"}
        save_baseline(tmp_path, hashes)
        loaded = load_baseline(tmp_path)
        assert loaded == hashes

    def test_baseline_file_is_json(self, tmp_path):
        save_baseline(tmp_path, {"x.py": "hash"})
        data = json.loads((tmp_path / BASELINE_FILE).read_text())
        assert "hashes" in data
        assert "committed_at" in data

    def test_baseline_contains_timestamp(self, tmp_path):
        save_baseline(tmp_path, {})
        data = json.loads((tmp_path / BASELINE_FILE).read_text())
        assert isinstance(data["committed_at"], float)
        assert data["committed_at"] > 0


# ---------------------------------------------------------------------------
# ScanResult
# ---------------------------------------------------------------------------

class TestScanResult:
    def test_clean_when_no_findings(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=2)
        assert r.clean is True

    def test_not_clean_with_finding(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=2)
        r.findings.append(Finding(path="x.py", kind="unsequenced", detail="", sha256=""))
        assert r.clean is False

    def test_unsequenced_count(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=2)
        r.findings.append(Finding(path="a.py", kind="unsequenced", detail="", sha256=""))
        r.findings.append(Finding(path="b.py", kind="drifted", detail="", sha256=""))
        assert r.unsequenced_count == 1
        assert r.drifted_count == 1

    def test_to_dict_has_required_keys(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=0)
        d = r.to_dict()
        for key in ("scan_root", "timestamp", "modules_scanned", "clean", "findings"):
            assert key in d


# ---------------------------------------------------------------------------
# ForensicReceipt
# ---------------------------------------------------------------------------

class TestForensicReceipt:
    def test_clean_receipt_summary(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=3)
        receipt = make_forensic_receipt("shadow-scan", r)
        assert receipt.clean is True
        assert "0" in receipt.findings_summary

    def test_dirty_receipt_summary(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=3)
        r.findings.append(Finding(path="x.py", kind="unsequenced", detail="", sha256=""))
        receipt = make_forensic_receipt("shadow-scan", r)
        assert receipt.clean is False
        assert "unsequenced" in receipt.findings_summary

    def test_sha256_is_64_chars(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=1)
        receipt = make_forensic_receipt("shadow-scan", r)
        assert len(receipt.sha256_of_result) == 64

    def test_action_stored(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=1)
        receipt = make_forensic_receipt("shadow-commit", r)
        assert receipt.action == "shadow-commit"

    def test_to_dict(self):
        r = ScanResult(scan_root="/", timestamp=0, modules_scanned=1)
        receipt = make_forensic_receipt("shadow-scan", r)
        d = receipt.to_dict()
        assert "sha256_of_result" in d
        assert "findings_summary" in d


# ---------------------------------------------------------------------------
# cmd_shadow_scan
# ---------------------------------------------------------------------------

class TestCmdShadowScan:
    def test_clean_on_all_stamped_no_baseline(self, tmp_root):
        code = cmd_shadow_scan(tmp_root, emit_json=False, quiet=True)
        assert code == 0

    def test_dirty_on_unstamped_module(self, unstamped_root):
        code = cmd_shadow_scan(unstamped_root, emit_json=False, quiet=True)
        assert code == 1

    def test_json_output_is_valid(self, tmp_root, capsys):
        cmd_shadow_scan(tmp_root, emit_json=True, quiet=False)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "result" in data
        assert "receipt" in data

    def test_json_clean_flag(self, tmp_root, capsys):
        cmd_shadow_scan(tmp_root, emit_json=True, quiet=False)
        data = json.loads(capsys.readouterr().out)
        assert data["result"]["clean"] is True

    def test_no_baseline_drift_not_checked(self, tmp_root):
        # Without a baseline file, only stamp presence is checked — should be clean
        code = cmd_shadow_scan(tmp_root, emit_json=False, quiet=True)
        assert code == 0

    def test_drift_detected_after_change(self, tmp_root):
        # Commit baseline, then modify a file — should detect drift
        cmd_shadow_commit(tmp_root, quiet=True)
        mod = tmp_root / "module_a.py"
        mod.write_text(mod.read_text() + "\n# changed\n")
        code = cmd_shadow_scan(tmp_root, emit_json=False, quiet=True)
        assert code == 1

    def test_clean_after_re_commit(self, tmp_root):
        # Modify, recommit — drift should clear
        cmd_shadow_commit(tmp_root, quiet=True)
        mod = tmp_root / "module_a.py"
        mod.write_text(mod.read_text() + "\n# changed\n")
        cmd_shadow_commit(tmp_root, quiet=True)
        code = cmd_shadow_scan(tmp_root, emit_json=False, quiet=True)
        assert code == 0

    def test_missing_file_reported_as_unsequenced(self, tmp_path):
        ghost = tmp_path / "ghost.py"
        manifest = tmp_path / MANIFEST_FILE
        manifest.write_text("ghost.py\n")
        code = cmd_shadow_scan(tmp_path, emit_json=False, quiet=True)
        assert code == 1


# ---------------------------------------------------------------------------
# cmd_shadow_commit
# ---------------------------------------------------------------------------

class TestCmdShadowCommit:
    def test_creates_baseline_file(self, tmp_root):
        assert not (tmp_root / BASELINE_FILE).exists()
        cmd_shadow_commit(tmp_root, quiet=True)
        assert (tmp_root / BASELINE_FILE).exists()

    def test_baseline_contains_all_modules(self, tmp_root):
        cmd_shadow_commit(tmp_root, quiet=True)
        baseline = load_baseline(tmp_root)
        assert baseline is not None
        assert "module_a.py" in baseline
        assert "module_b.py" in baseline

    def test_commit_returns_zero(self, tmp_root):
        code = cmd_shadow_commit(tmp_root, quiet=True)
        assert code == 0


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------

class TestMain:
    def test_shadow_scan_clean_exit_0(self, tmp_root):
        code = main(["shadow-scan", str(tmp_root), "--quiet"])
        assert code == 0

    def test_shadow_scan_dirty_exit_1(self, unstamped_root):
        code = main(["shadow-scan", str(unstamped_root), "--quiet"])
        assert code == 1

    def test_shadow_commit_exit_0(self, tmp_root):
        code = main(["shadow-commit", str(tmp_root), "--quiet"])
        assert code == 0

    def test_json_flag_produces_json(self, tmp_root, capsys):
        main(["shadow-scan", str(tmp_root), "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "receipt" in data


# ---------------------------------------------------------------------------
# Real codebase scan — verifies the production manifest is clean
# ---------------------------------------------------------------------------

class TestRealCodebaseScan:
    def test_all_governed_modules_are_stamped(self):
        """shadow-scan . on the actual repo returns exit code 0.

        This test is the forensic receipt for issue #37:
        tas_cli.py shadow-scan . → 0 unsequenced/drifted artifacts.
        """
        repo_root = Path(__file__).parent.parent
        # Only stamp-presence check — no baseline required for this assertion
        modules = load_manifest(repo_root)
        assert len(modules) > 0, "manifest is empty"
        unsequenced = [m for m in modules if m.exists() and not has_stamp_anchor(m)]
        assert unsequenced == [], (
            f"Unsequenced governed modules (no STAMP_ANCHOR_): "
            f"{[str(m) for m in unsequenced]}"
        )

    def test_no_missing_governed_modules(self):
        """All modules listed in .tas_manifest actually exist on disk."""
        repo_root = Path(__file__).parent.parent
        modules = load_manifest(repo_root)
        missing = [m for m in modules if not m.exists()]
        assert missing == [], f"Governed modules missing from disk: {missing}"
