"""WakeNonceStore — cross-restart replay-attack prevention for WakeChain (W3).

The WakeChain's in-memory monotone sequence counter prevents replay within a
single process lifetime.  Across restarts an attacker could resubmit a receipt
with seq=0 against a fresh WakeChain and the in-memory check would pass.

This module provides a persistent nonce store that:
1. Records every committed (session_id, seq) pair to a file-backed store.
2. Rejects any (session_id, seq) pair that has already been seen, even across
   process boundaries.
3. Records the wake-head hash alongside each entry so that a restarted process
   can verify it is continuing from the correct chain tip.

Invariant W3 (anti-replay across restarts):
    For any session_id S and sequence number N, a ProvenanceMark with seq=N
    may be accepted at most once.  A second presentation of (S, N) raises
    ``ReplayAttackDetected``, regardless of process boundaries.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import threading
from typing import Dict, Optional, Tuple


class ReplayAttackDetected(Exception):
    """Raised when a (session_id, seq) pair has already been committed."""


class NonceStoreCorrupted(Exception):
    """Raised when the nonce store file fails HMAC integrity verification."""


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _file_hmac(path: pathlib.Path, key: bytes) -> str:
    """Return HMAC-SHA-256 hex digest of the file's raw bytes."""
    raw = path.read_bytes() if path.exists() else b""
    return hmac.new(key, raw, hashlib.sha256).hexdigest()


class WakeNonceStore:
    """Persistent nonce store for cross-restart WakeChain replay prevention.

    Parameters
    ----------
    store_path:
        Path to the JSON file that backs the nonce store.
        Created automatically if it does not exist.
    integrity_key:
        32-byte key used to HMAC-protect the store file.
        If not provided, a deterministic key derived from the path is used
        (suitable for single-machine deployments where file-system access
        controls are the primary protection boundary).
    """

    def __init__(
        self,
        store_path: str | pathlib.Path = "ledger/wake_nonces.json",
        integrity_key: Optional[bytes] = None,
    ) -> None:
        self._path = pathlib.Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._key: bytes = integrity_key or _sha256(str(self._path.resolve()).encode())
        self._lock = threading.Lock()
        # In-memory index: (session_id, seq) -> wake_head_hex
        self._seen: Dict[Tuple[str, int], str] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_and_record(
        self,
        session_id: str,
        seq: int,
        wake_head_hex: str,
    ) -> None:
        """Assert that (session_id, seq) is novel, then record it.

        Parameters
        ----------
        session_id:
            The WakeChain session UUID.
        seq:
            The ProvenanceMark sequence number being committed.
        wake_head_hex:
            The wake-head hash *after* this receipt is committed (for
            continuity verification on the next restart).

        Raises
        ------
        ReplayAttackDetected
            If (session_id, seq) has already been seen.
        """
        key = (session_id, seq)
        with self._lock:
            if key in self._seen:
                raise ReplayAttackDetected(
                    f"Replay attack detected: session={session_id!r} seq={seq} "
                    f"was already committed with wake_head={self._seen[key]!r}"
                )
            self._seen[key] = wake_head_hex
            self._persist()

    def last_wake_head(self, session_id: str) -> Optional[str]:
        """Return the most recent wake-head hex for *session_id*, or None."""
        with self._lock:
            max_seq = -1
            head = None
            for (sid, seq), wake_head in self._seen.items():
                if sid == session_id and seq > max_seq:
                    max_seq = seq
                    head = wake_head
            return head

    def seen_count(self, session_id: Optional[str] = None) -> int:
        """Return the number of recorded nonces, optionally filtered by session."""
        with self._lock:
            if session_id is None:
                return len(self._seen)
            return sum(1 for (sid, _) in self._seen if sid == session_id)

    def verify_integrity(self) -> bool:
        """Return True iff the store file passes HMAC integrity verification."""
        if not self._path.exists():
            return True
        try:
            raw = self._path.read_bytes()
            data = json.loads(raw)
            stored_mac = data.get("__hmac__", "")
            payload_bytes = json.dumps(
                data.get("nonces", {}), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            expected = hmac.new(self._key, payload_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, stored_mac)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load nonces from disk.  Raises NonceStoreCorrupted on HMAC failure."""
        if not self._path.exists():
            return
        try:
            raw = self._path.read_bytes()
            data = json.loads(raw)
        except Exception as exc:
            raise NonceStoreCorrupted(f"Cannot parse nonce store: {exc}") from exc

        stored_mac = data.get("__hmac__", "")
        nonces = data.get("nonces", {})
        payload_bytes = json.dumps(nonces, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = hmac.new(self._key, payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, stored_mac):
            raise NonceStoreCorrupted(
                "WakeNonceStore HMAC verification failed — file may have been tampered with."
            )

        for composite_key, wake_head in nonces.items():
            session_id, seq_str = composite_key.rsplit(":", 1)
            self._seen[(session_id, int(seq_str))] = wake_head

    def _persist(self) -> None:
        """Write the current nonce map to disk with an HMAC integrity tag."""
        nonces = {
            f"{session_id}:{seq}": wake_head
            for (session_id, seq), wake_head in self._seen.items()
        }
        payload_bytes = json.dumps(nonces, sort_keys=True, separators=(",", ":")).encode("utf-8")
        mac = hmac.new(self._key, payload_bytes, hashlib.sha256).hexdigest()
        data = {"nonces": nonces, "__hmac__": mac}
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self._path)
