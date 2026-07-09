"""Tests for WakeNonceStore — cross-restart replay-attack prevention (W3).

Invariant W3 (anti-replay across restarts):
    For any session_id S and sequence number N, a ProvenanceMark with seq=N
    may be accepted at most once.  A second presentation of (S, N) raises
    ReplayAttackDetected, regardless of process boundaries.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
import json
import pathlib
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from wake_nonce_store import WakeNonceStore, ReplayAttackDetected, NonceStoreCorrupted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _store(tmp_path: pathlib.Path, **kwargs) -> WakeNonceStore:
    return WakeNonceStore(store_path=tmp_path / "nonces.json", **kwargs)


# ===========================================================================
# TestReplayPrevention — W3 basic replay detection
# ===========================================================================


class TestReplayPrevention:
    """Invariant W3 — cross-restart anti-replay (§5).

    Enforces: (session_id, seq) may only be committed once.  A second
    presentation raises ReplayAttackDetected regardless of process boundaries.
    """

    def test_first_commit_accepted(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-1", 0, "aabbcc")

    def test_same_nonce_rejected(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-1", 0, "aabbcc")
        with pytest.raises(ReplayAttackDetected):
            store.check_and_record("sess-1", 0, "deadbeef")

    def test_different_seq_accepted(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-1", 0, "aabb")
        store.check_and_record("sess-1", 1, "ccdd")

    def test_different_session_same_seq_accepted(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-A", 0, "aabb")
        store.check_and_record("sess-B", 0, "ccdd")

    def test_sequence_of_commits(self, tmp_path):
        store = _store(tmp_path)
        for seq in range(20):
            store.check_and_record("sess-1", seq, f"head-{seq}")
        assert store.seen_count("sess-1") == 20

    def test_replay_detected_after_many_commits(self, tmp_path):
        store = _store(tmp_path)
        for seq in range(10):
            store.check_and_record("sess-1", seq, f"h{seq}")
        with pytest.raises(ReplayAttackDetected):
            store.check_and_record("sess-1", 5, "replayed")


# ===========================================================================
# TestCrossRestartPersistence — replay prevention survives process restart
# ===========================================================================


class TestCrossRestartPersistence:
    """Invariant W3 — persistence across process restarts.

    A new WakeNonceStore instance loading the same file must reject a
    previously committed (session_id, seq) pair — simulating process restart.
    """

    def test_nonce_persisted_across_restart(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        store1.check_and_record("sess-1", 0, "head0")
        store1.check_and_record("sess-1", 1, "head1")

        # Simulate restart: new instance, same file
        store2 = WakeNonceStore(store_path=path)
        with pytest.raises(ReplayAttackDetected):
            store2.check_and_record("sess-1", 0, "replayed")

    def test_new_nonce_accepted_after_restart(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        store1.check_and_record("sess-1", 0, "head0")

        store2 = WakeNonceStore(store_path=path)
        store2.check_and_record("sess-1", 1, "head1")

    def test_last_wake_head_survives_restart(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        store1.check_and_record("sess-X", 0, "aabb")
        store1.check_and_record("sess-X", 1, "ccdd")

        store2 = WakeNonceStore(store_path=path)
        assert store2.last_wake_head("sess-X") == "ccdd"

    def test_seen_count_survives_restart(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        for i in range(5):
            store1.check_and_record("sess-1", i, f"h{i}")

        store2 = WakeNonceStore(store_path=path)
        assert store2.seen_count("sess-1") == 5


# ===========================================================================
# TestIntegrityProtection — HMAC tamper detection
# ===========================================================================


class TestIntegrityProtection:
    """Invariant W3 — nonce store HMAC tamper detection.

    The nonce store file is HMAC-protected.  Any modification to the stored
    nonces that bypasses the normal API is detected at load time.
    """

    def test_verify_integrity_passes_on_fresh_store(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-1", 0, "aa")
        assert store.verify_integrity()

    def test_tampered_file_detected_on_load(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        store1.check_and_record("sess-1", 0, "aa")

        # Tamper: inject a new nonce without updating the HMAC
        data = json.loads(path.read_text())
        data["nonces"]["sess-EVIL:99"] = "evilhead"
        path.write_text(json.dumps(data))

        with pytest.raises(NonceStoreCorrupted):
            WakeNonceStore(store_path=path)

    def test_tampered_hmac_field_detected(self, tmp_path):
        path = tmp_path / "nonces.json"
        store1 = WakeNonceStore(store_path=path)
        store1.check_and_record("sess-1", 0, "aa")

        data = json.loads(path.read_text())
        data["__hmac__"] = "0" * 64
        path.write_text(json.dumps(data))

        with pytest.raises(NonceStoreCorrupted):
            WakeNonceStore(store_path=path)

    def test_empty_store_verify_passes(self, tmp_path):
        store = _store(tmp_path)
        assert store.verify_integrity()

    def test_custom_key_round_trips(self, tmp_path):
        path = tmp_path / "nonces.json"
        key = b"A" * 32
        store1 = WakeNonceStore(store_path=path, integrity_key=key)
        store1.check_and_record("sess-1", 0, "aa")

        store2 = WakeNonceStore(store_path=path, integrity_key=key)
        with pytest.raises(ReplayAttackDetected):
            store2.check_and_record("sess-1", 0, "replay")


# ===========================================================================
# TestLastWakeHead — continuity tracking
# ===========================================================================


class TestLastWakeHead:
    """WakeNonceStore.last_wake_head() tracks the latest chain tip per session."""

    def test_none_for_unknown_session(self, tmp_path):
        store = _store(tmp_path)
        assert store.last_wake_head("unknown") is None

    def test_returns_latest_head(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-1", 0, "head0")
        store.check_and_record("sess-1", 1, "head1")
        store.check_and_record("sess-1", 2, "head2")
        assert store.last_wake_head("sess-1") == "head2"

    def test_isolated_per_session(self, tmp_path):
        store = _store(tmp_path)
        store.check_and_record("sess-A", 0, "headA")
        store.check_and_record("sess-B", 0, "headB")
        assert store.last_wake_head("sess-A") == "headA"
        assert store.last_wake_head("sess-B") == "headB"


# ===========================================================================
# TestThreadSafety — concurrent commits
# ===========================================================================


class TestThreadSafety:
    """WakeNonceStore is thread-safe: concurrent commits to different seqs succeed."""

    def test_concurrent_commits_distinct_seqs(self, tmp_path):
        store = _store(tmp_path)
        errors = []

        def commit(seq):
            try:
                store.check_and_record("sess-T", seq, f"h{seq}")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=commit, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Unexpected errors in concurrent commits: {errors}"
        assert store.seen_count("sess-T") == 20

    def test_concurrent_replay_detected(self, tmp_path):
        """Concurrent replay of the same seq raises ReplayAttackDetected at least once."""
        store = _store(tmp_path)
        store.check_and_record("sess-R", 0, "h0")
        replay_errors = []

        def attempt_replay():
            try:
                store.check_and_record("sess-R", 0, "h0")
            except ReplayAttackDetected as exc:
                replay_errors.append(exc)

        threads = [threading.Thread(target=attempt_replay) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(replay_errors) >= 1, "Expected at least one ReplayAttackDetected"
