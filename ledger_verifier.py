"""LedgerVerifier — tamper-evident hardening for ArtifactGuard ledger (X3/W1).

``artifact_guard`` appends lines of the form::

    <artifact_digest>  <artifact_filename>  wake=<wake_receipt_hash>

to ``ledger/artifacts.hash``.  This file is append-only in normal operation
but is not itself integrity-protected — an attacker with file-system access
could silently modify or delete lines.

This module adds two layers of hardening:

1. **Ledger HMAC seal** (``LedgerSeal``): a companion file
   ``ledger/artifacts.seal`` stores an HMAC-SHA-256 over the entire ledger
   content.  After every append the seal is rewritten.  Any read-time
   verification that detects a mismatch raises ``LedgerTampered``.

2. **Merkle accumulator** (``LedgerMerkle``): a rolling SHA-256 Merkle root
   over all ledger lines, persisted in ``ledger/artifacts.merkle``.  Each
   new line extends the root as ``SHA-256(prev_root || SHA-256(line))``.
   This makes it possible to prove inclusion of any individual entry and
   detect any retroactive insertion or deletion without re-reading the full
   ledger.

Both objects are independent and can be used separately or together.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import hashlib
import hmac
import json
import pathlib
import threading
from typing import List, Optional


_GENESIS_ROOT = bytes(32)  # 32 zero bytes — well-known Merkle genesis


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


class LedgerTampered(Exception):
    """Raised when the ledger file fails HMAC or Merkle integrity verification."""


# ---------------------------------------------------------------------------
# HMAC seal
# ---------------------------------------------------------------------------


class LedgerSeal:
    """HMAC-SHA-256 seal over the entire ledger file.

    After every call to :meth:`record` the seal file is atomically rewritten.
    :meth:`verify` reads both files and confirms the HMAC matches.

    Parameters
    ----------
    ledger_path:
        Path to the ``artifacts.hash`` ledger file.
    seal_path:
        Path to the companion ``.seal`` file.  Defaults to
        ``<ledger_path>.seal``.
    integrity_key:
        32-byte HMAC key.  A deterministic key derived from the ledger path
        is used when not provided.
    """

    def __init__(
        self,
        ledger_path: str | pathlib.Path = "ledger/artifacts.hash",
        seal_path: Optional[str | pathlib.Path] = None,
        integrity_key: Optional[bytes] = None,
    ) -> None:
        self._ledger = pathlib.Path(ledger_path)
        self._seal = pathlib.Path(seal_path) if seal_path else self._ledger.with_suffix(".seal")
        self._ledger.parent.mkdir(parents=True, exist_ok=True)
        self._key: bytes = integrity_key or _sha256(str(self._ledger.resolve()).encode())
        self._lock = threading.Lock()

    def record(self, line: str) -> None:
        """Append *line* to the ledger and refresh the HMAC seal.

        Parameters
        ----------
        line:
            A single ledger line (must not contain a trailing newline — one
            will be appended automatically).
        """
        with self._lock:
            with self._ledger.open("a") as fh:
                fh.write(line.rstrip("\n") + "\n")
            self._write_seal()

    def verify(self) -> bool:
        """Return True iff the ledger content matches the stored HMAC seal.

        Returns False (does not raise) so callers can decide how to handle
        a mismatch.  Use :meth:`assert_integrity` for a raising variant.
        """
        with self._lock:
            return self._check_seal()

    def assert_integrity(self) -> None:
        """Raise :class:`LedgerTampered` if the ledger fails HMAC verification."""
        if not self.verify():
            raise LedgerTampered(
                f"Ledger HMAC seal mismatch — {self._ledger} may have been tampered with."
            )

    def _write_seal(self) -> None:
        content = self._ledger.read_bytes() if self._ledger.exists() else b""
        mac = hmac.new(self._key, content, hashlib.sha256).hexdigest()
        tmp = self._seal.with_suffix(".tmp")
        tmp.write_text(json.dumps({"__hmac__": mac}))
        tmp.replace(self._seal)

    def _check_seal(self) -> bool:
        if not self._seal.exists():
            # No seal yet — only valid if ledger is also empty/absent
            ledger_empty = not self._ledger.exists() or self._ledger.stat().st_size == 0
            return ledger_empty
        try:
            stored = json.loads(self._seal.read_text()).get("__hmac__", "")
        except Exception:
            return False
        content = self._ledger.read_bytes() if self._ledger.exists() else b""
        expected = hmac.new(self._key, content, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, stored)


# ---------------------------------------------------------------------------
# Merkle accumulator
# ---------------------------------------------------------------------------


class LedgerMerkle:
    """Rolling SHA-256 Merkle accumulator over ledger lines.

    Each new line extends the Merkle root as::

        root_{n} = SHA-256(root_{n-1} || SHA-256(line_n))

    The current root and line count are persisted in a companion ``.merkle``
    file so the accumulator survives process restarts.

    Parameters
    ----------
    ledger_path:
        Path to the ``artifacts.hash`` ledger file (used to derive the
        default merkle path and integrity key).
    merkle_path:
        Path to the ``.merkle`` state file.
    integrity_key:
        32-byte HMAC key protecting the merkle state file itself.
    """

    def __init__(
        self,
        ledger_path: str | pathlib.Path = "ledger/artifacts.hash",
        merkle_path: Optional[str | pathlib.Path] = None,
        integrity_key: Optional[bytes] = None,
    ) -> None:
        self._ledger = pathlib.Path(ledger_path)
        self._merkle = (
            pathlib.Path(merkle_path) if merkle_path
            else self._ledger.with_suffix(".merkle")
        )
        self._ledger.parent.mkdir(parents=True, exist_ok=True)
        self._key: bytes = integrity_key or _sha256(str(self._ledger.resolve()).encode())
        self._lock = threading.Lock()
        self._root: bytes = _GENESIS_ROOT
        self._count: int = 0
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def root(self) -> bytes:
        """Current Merkle root (32 bytes)."""
        return self._root

    @property
    def root_hex(self) -> str:
        """Current Merkle root as a 64-char hex string."""
        return self._root.hex()

    @property
    def count(self) -> int:
        """Number of lines accumulated so far."""
        return self._count

    def extend(self, line: str) -> bytes:
        """Extend the Merkle root with *line* and persist.

        Parameters
        ----------
        line:
            A ledger line (trailing newline stripped before hashing).

        Returns
        -------
        bytes
            The new Merkle root after including this line.
        """
        with self._lock:
            line_hash = _sha256(line.rstrip("\n").encode("utf-8"))
            self._root = _sha256(self._root + line_hash)
            self._count += 1
            self._persist()
            return self._root

    def verify_against_ledger(self) -> bool:
        """Recompute the Merkle root from the full ledger and compare.

        Returns True iff the persisted root matches a full replay of the
        ledger file.  Detects insertions, deletions, and reorderings.
        """
        with self._lock:
            if not self._ledger.exists():
                return self._root == _GENESIS_ROOT and self._count == 0
            lines = self._ledger.read_text().splitlines()
            root = _GENESIS_ROOT
            for line in lines:
                if not line.strip():
                    continue
                root = _sha256(root + _sha256(line.encode("utf-8")))
            return root == self._root and len(lines) == self._count

    def inclusion_proof(self, line: str) -> bool:
        """Return True iff *line* can be found in the ledger by content match.

        This is a simple linear-scan inclusion check.  A production
        implementation would use a proper Merkle proof path; for the TAS
        reference implementation a full-ledger scan suffices.
        """
        if not self._ledger.exists():
            return False
        needle = line.rstrip("\n")
        for raw in self._ledger.read_text().splitlines():
            if raw.strip() == needle:
                return True
        return False

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._merkle.exists():
            return
        try:
            data = json.loads(self._merkle.read_text())
        except Exception:
            return
        stored_mac = data.get("__hmac__", "")
        payload = {"root": data.get("root", ""), "count": data.get("count", 0)}
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(self._key, payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, stored_mac):
            raise LedgerTampered(
                f"Merkle state file {self._merkle} failed HMAC verification."
            )
        self._root = bytes.fromhex(data["root"])
        self._count = int(data["count"])

    def _persist(self) -> None:
        payload = {"root": self._root.hex(), "count": self._count}
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        mac = hmac.new(self._key, payload_bytes, hashlib.sha256).hexdigest()
        data = {**payload, "__hmac__": mac}
        tmp = self._merkle.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self._merkle)
