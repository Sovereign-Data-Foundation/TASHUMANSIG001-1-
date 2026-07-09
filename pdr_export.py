"""Process Data Record (PDR) Stream Exporter — TAS Day-Zero Readiness.

Produces a SHA-256 chained JSON manifest (EXECUTE_01JAB7.json) that encodes
every state transition in a single TAS session: genesis anchor, axiom gates,
wake-chain receipts, and final chain-verification result.

The exported file is independently verifiable by any observer who knows the
session key or can replay the canonical event sequence.

Usage::

    python pdr_export.py                       # writes EXECUTE_01JAB7.json
    python pdr_export.py --out custom.json     # custom output path
    python pdr_export.py --verify existing.json

Exit codes:
    0 — success / verification passed
    1 — chain tampered or verification failed
"""
# © 2025-2026 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from typing import Any, Dict, List

from axioms import AxiomSet, AxiomViolation
from genesis_anchor import build_genesis_payload, derive_app_hash
from wake_chain import WakeChain

_SCHEMA = "TAS-PDR-v1"
_DEFAULT_OUT = "EXECUTE_01JAB7.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# State-transition scenario
# ---------------------------------------------------------------------------
#
# Each entry drives one axiom-gate check and one wake-chain commit.
# The structure is:
#   label     — human-readable event name
#   symbol    — P0 symbol to bind/validate
#   referent  — canonical referent value
#   proof     — P1 proof object (dict passed to the admissibility gate)
#   synthetic — True marks this as an adversarial / OOD input
#
_TRANSITIONS: List[Dict[str, Any]] = [
    {
        "label": "genesis_anchor",
        "symbol": "A0",
        "referent": "Prime Invariant / Genesis Anchor",
        "proof": {"source": "genesis_anchor.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "wake_chain_init",
        "symbol": "WAKE_HEAD_0",
        "referent": "0" * 64,           # genesis hash (32 zero bytes → hex)
        "proof": {"source": "wake_chain.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "p0_equivalence_lock",
        "symbol": "P0:Equivalence",
        "referent": "symbol ≡ referent ∀ registered pairs",
        "proof": {"source": "axioms.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "p1_admissibility_gate",
        "symbol": "P1:Admissibility",
        "referent": "V(spec, proof, π) = True ∀ admitted transitions",
        "proof": {"source": "axioms.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "logos_gate_pass",
        "symbol": "LOGOS_GATE",
        "referent": "lineage_continuity=True,density_floor=True",
        "proof": {"source": "tas_logos_gatekeeper.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "phoenix_circuit_armed",
        "symbol": "PHOENIX_STATE",
        "referent": "ARMED",
        "proof": {"source": "phoenix.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "yknot_branch_tied",
        "symbol": "YKNOT_VERDICT",
        "referent": "TIED",
        "proof": {"source": "yknot.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "sdi_within_threshold",
        "symbol": "SDI_t",
        "referent": "< 0.05",
        "proof": {"source": "stability.py", "entropy_budget": 1e-7, "authorised": True},
        "synthetic": False,
    },
    {
        "label": "adversarial_synthetic_rejected",
        "symbol": "SYNTHETIC_PAYLOAD",
        "referent": None,               # no authorised referent → will be refused
        "proof": {"source": "UNKNOWN", "authorised": False},
        "synthetic": True,
    },
    {
        "label": "uvk_certification",
        "symbol": "UVK_STATUS",
        "referent": "CERTIFIED",
        "proof": {"source": "uvk.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "human_api_bridge_authorised",
        "symbol": "HCS_INTENT",
        "referent": "human_authorised=True",
        "proof": {"source": "human_api_bridge.py", "authorised": True},
        "synthetic": False,
    },
    {
        "label": "ledger_sealed",
        "symbol": "LEDGER_SEAL",
        "referent": "HMAC_VERIFIED",
        "proof": {"source": "ledger_verifier.py", "authorised": True},
        "synthetic": False,
    },
]


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------


def run_session(session_id: str) -> Dict[str, Any]:
    """Run a full TAS session and return a PDR record dict."""

    chain = WakeChain(session_id=session_id)
    axioms = AxiomSet.default()
    genesis = build_genesis_payload()
    app_hash = derive_app_hash(genesis.get("app_state", {}))

    receipts: List[Dict[str, Any]] = []
    refusals: List[Dict[str, Any]] = []

    # ── Commit genesis anchor as receipt 0 ──────────────────────────────
    genesis_pm = chain.commit(
        event={"type": "genesis_anchor", "app_hash": app_hash},
        info={"genesis_chain_id": genesis.get("chain_id"), "app_hash": app_hash},
    )
    receipts.append({
        "seq": genesis_pm.seq,
        "label": "genesis_anchor_block",
        "event_type": "genesis",
        "admitted": True,
        "axiom_p0_registry_hash": axioms.p0.registry_hash(),
        "axiom_p1_verdict": "GENESIS_BLOCK",
        "pm": genesis_pm.to_dict(),
        "timestamp": _now_iso(),
    })

    # ── Process state transitions ────────────────────────────────────────
    for transition in _TRANSITIONS:
        label = transition["label"]
        symbol = transition["symbol"]
        referent = transition["referent"]
        proof = transition["proof"]
        synthetic = transition["synthetic"]

        # P0 — bind or validate symbol equivalence
        p0_result = "SKIPPED"
        p0_violation = None
        try:
            if referent is not None:
                try:
                    axioms.p0.bind(symbol, referent)
                    p0_result = "BOUND"
                except AxiomViolation:
                    axioms.p0.validate(symbol, referent)
                    p0_result = "VALIDATED"
        except AxiomViolation as exc:
            p0_result = "VIOLATED"
            p0_violation = str(exc)

        # P1 — admissibility gate
        p1_record: Dict[str, Any] = {}
        admitted = False
        p1_verdict = "REFUSED"
        try:
            p1_record = axioms.p1.admit(transition=transition, proof=proof)
            admitted = p1_record.get("admitted", False)
            p1_verdict = "ADMITTED" if admitted else "REFUSED"
        except Exception as exc:
            p1_verdict = "ERROR"
            p1_record = {"error": str(exc)}

        if synthetic or not proof.get("authorised", False):
            admitted = False
            p1_verdict = "REFUSED:SYNTHETIC"

        # Wake-chain commit (admitted only — refusals get a refusal receipt)
        if admitted:
            pm = chain.commit(
                event={"label": label, "symbol": symbol, "referent": str(referent)},
                info={
                    "source": proof.get("source"),
                    "p0_result": p0_result,
                    "p1_verdict": p1_verdict,
                },
            )
            receipts.append({
                "seq": pm.seq,
                "label": label,
                "event_type": "state_transition",
                "admitted": True,
                "axiom_p0_result": p0_result,
                "axiom_p1_verdict": p1_verdict,
                "pm": pm.to_dict(),
                "timestamp": _now_iso(),
            })
        else:
            refusal_hash = _sha256_hex(
                json.dumps({"label": label, "reason": p1_verdict, "ts": _now_iso()},
                           sort_keys=True).encode()
            )
            refusals.append({
                "label": label,
                "symbol": symbol,
                "reason": p1_verdict,
                "p0_result": p0_result,
                "p0_violation": p0_violation,
                "refusal_hash": refusal_hash,
                "calculator_doctrine": "SILENT — no output emitted",
                "timestamp": _now_iso(),
            })

    # ── Chain seal ───────────────────────────────────────────────────────
    chain_ok = chain.verify()

    seal_pm = chain.commit(
        event={"type": "chain_seal", "chain_verified": chain_ok},
        info={
            "total_receipts": len(receipts),
            "total_refusals": len(refusals),
            "chain_verified": chain_ok,
        },
    )
    receipts.append({
        "seq": seal_pm.seq,
        "label": "chain_seal",
        "event_type": "seal",
        "admitted": True,
        "chain_verified": chain_ok,
        "pm": seal_pm.to_dict(),
        "timestamp": _now_iso(),
    })

    # ── Build manifest ───────────────────────────────────────────────────
    manifest_body = {
        "schema": _SCHEMA,
        "session_id": session_id,
        "generated_at": _now_iso(),
        "genesis_chain_id": genesis.get("chain_id"),
        "genesis_app_hash": app_hash,
        "wake_head_final": chain.head.hex(),
        "chain_verified": chain_ok,
        "axiom_p0_registry_hash": axioms.p0.registry_hash(),
        "axiom_p1_admitted": axioms.p1.admitted_count,
        "axiom_p1_rejected": axioms.p1.rejected_count,
        "receipts": receipts,
        "refusals": refusals,
        "summary": {
            "total_transitions": len(_TRANSITIONS),
            "admitted": len(receipts),
            "refused": len(refusals),
            "chain_length": len(chain),
            "chain_verified": chain_ok,
        },
    }

    # Compute manifest hash last (covers the body without itself)
    manifest_hash = _sha256_hex(
        json.dumps(manifest_body, sort_keys=True, separators=(",", ":")).encode()
    )
    manifest_body["manifest_hash"] = manifest_hash
    return manifest_body


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_manifest(path: str) -> bool:
    """Re-compute the manifest hash and return True iff it matches."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    stored_hash = data.pop("manifest_hash", None)
    if stored_hash is None:
        print("ERROR: manifest_hash field missing", file=sys.stderr)
        return False

    recomputed = _sha256_hex(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    )
    ok = recomputed == stored_hash
    if ok:
        print(f"✓ Manifest hash verified: {stored_hash[:24]}…")
        print(f"  Chain length : {data['summary']['chain_length']}")
        print(f"  Admitted     : {data['summary']['admitted']}")
        print(f"  Refused      : {data['summary']['refused']}")
        print(f"  Chain OK     : {data['chain_verified']}")
    else:
        print(f"✗ TAMPERED — stored={stored_hash[:24]}… computed={recomputed[:24]}…",
              file=sys.stderr)
    return ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="TAS PDR Stream Exporter")
    parser.add_argument("--out", default=_DEFAULT_OUT, help="Output JSON path")
    parser.add_argument("--verify", metavar="FILE", help="Verify an existing manifest")
    parser.add_argument("--session-id", default=None, help="Fix session UUID (reproducible)")
    args = parser.parse_args()

    if args.verify:
        return 0 if verify_manifest(args.verify) else 1

    session_id = args.session_id or str(uuid.uuid4())
    print(f"Running TAS session  {session_id}")
    manifest = run_session(session_id)

    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Written → {out_path}  ({len(json.dumps(manifest))} bytes)")
    print(f"  Chain length    : {manifest['summary']['chain_length']}")
    print(f"  Admitted        : {manifest['summary']['admitted']}")
    print(f"  Refused         : {manifest['summary']['refused']}")
    print(f"  Chain verified  : {manifest['chain_verified']}")
    print(f"  Manifest hash   : {manifest['manifest_hash'][:24]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
