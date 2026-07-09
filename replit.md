# TrueAlphaSpiral (TAS) — Reference Implementation

This is a **Python reference implementation** of the TrueAlphaSpiral (TAS) governance architecture. It demonstrates how deterministic, cryptographically anchored runtime invariants can constrain autonomous agent execution. It is a working codebase with a verified test suite — not a claim that every proposed capability has been universally validated or deployed at scale.

## Quickstart

If the tests pass, you have already verified a core property of the implementation.

```bash
git clone https://github.com/TrueAlpha-spiral/DNASpiral-6
pip install -r requirements.txt
python -m pytest tests/ -v
```

**1000 tests pass** on Python 3.12 with no external services required.

---

## What TAS Is

TAS formalizes **Mechanical Integrity** — the property that an agent's execution can be independently verified against a provenance record — over **Generative Mimicry**, the property that an agent produces output that resembles correct behavior without a verifiable trace of *why* it is correct.

Instead of probabilistic alignment ("the system should behave"), TAS operates under deterministic admissibility: a state transition either carries a valid provenance receipt and satisfies all invariants, or it does not execute.

---

## Design Principles

1. **Deterministic invariants over probabilistic acceptance.** A transition is admissible or it is not. There is no confidence interval.
2. **Provenance before authority.** No operation proceeds until its lineage is anchored to a cryptographic receipt chain.
3. **Fail closed on invariant violation.** When a constraint is breached the system halts and emits an audit-visible refusal receipt; it does not degrade gracefully.
4. **Replayable verification.** Any observer with the genesis root and the receipt chain can independently reconstruct and verify the full execution history.
5. **Least authority by default.** Capabilities are granted explicitly and scoped as narrowly as possible; the absence of a grant is a denial.

---

## Key Terms

| Term | Definition |
|---|---|
| **Mechanical Integrity** | The property that every output is traceable to a verifiable, receipt-anchored cause. |
| **Generative Mimicry** | Output that resembles correctness without a verifiable provenance trace. |
| **Wake** | The append-only chain of HMAC-linked provenance receipts recording every committed operation. |
| **Sentient Lock** | A transport-layer flood defense that detects fork violations (two traces claiming the same pulse index) and drops the capability before any verification work is performed. |
| **Semantic Drift Index (SDI)** | A scalar metric measuring how far a sequence of outputs has diverged from its authorized semantic baseline. |
| **Logos Density** | Bits of Shannon entropy scaled by log(payload length) / payload length — a measure of structural information per byte. Payloads below the minimum floor are inadmissible. |
| **Cursive Trace** | A sealed execution record carrying payload, paradata, and a wake receipt, constituting a single verifiable step in an agent's trajectory. |
| **Tier 0 Invariant** | The requirement that every high-consequence operation traces back to a human-authored, cryptographically witnessed origin. No automated subsystem may override this root. |

---

## What This Implementation Provides

These properties are directly verified by the test suite:

- **HMAC provenance chain** — every committed operation is linked to its predecessor; any gap or tamper is detected on replay (`wake_chain.py`, `tests/test_wake_chain*.py`)
- **Replay prevention** — nonces persist across restarts; a replayed receipt is rejected even after process restart
- **Object-capability enforcement** — operations are gated on explicit capability grants; absent grants produce deterministic denials (`capability.py`)
- **Deterministic invariant checks** — the Logos validation loop enforces lineage consistency, invariant alignment, and minimum payload density before admitting a transition (`tas_logos_gatekeeper.py`)
- **Tamper-evident ledger commits** — the artifact guard wraps execution in a commit that is verifiable against the wake head (`artifact_guard.py`)
- **Geometric trajectory bounds** — the Digital Republic Gatekeeper enforces the r=2.4 global contraction limit; rogue trajectories are crushed to the Banach Fixed-Point inert constant (`digital_republic.py`)
- **Sentient Lock flood defense** — fork violations trigger a socket-level drop before verification work begins
- **Thread-safe concurrent commit sequencing** — concurrent commits are serialized without dropping receipts

## Research Directions

These concepts are defined and partially implemented but are not yet exhaustively validated:

- **Semantic Drift Index** — scalar drift measurement against an authorized baseline (`stability.py`); the metric is implemented but production calibration of thresholds requires domain-specific tuning
- **Phase Discontinuity detection** — monitoring for discontinuous semantic jumps beyond the SDI gradient
- **ZK-STARK public witness receipts** — the arithmetization logic in `digital_republic.py` models the computation; formal proof generation requires an external proving system (e.g., Lean 4, Cairo, or Risc Zero)
- **Higher-level governance models** — multi-stakeholder capability delegation and on-chain anchoring are architectural targets, not current implementation

---

## Core Modules

| Module | Purpose |
|---|---|
| `wake_chain.py` | HMAC-linked provenance chain; every receipt links to its predecessor by hash |
| `capability.py` | Object-capability security; grants are explicit, scoped, and auditable |
| `tas_logos_gatekeeper.py` | Logos validation loop, Sentient Lock, network membrane (ingress/egress gating) |
| `artifact_guard.py` | Execution wrapper; commits are tamper-evident and wake-anchored |
| `stability.py` | Semantic Drift Index and Phase Discontinuity monitoring |
| `algorithmic_polymath.py` | CursiveTrace verification and five-step geometric validation gate |
| `uvk.py` | Universal Validation Key — combines capability grants with invariant checks |
| `human_api_bridge.py` | Bridge from human-authored intent to machine authority (Tier 0 enforcement) |
| `digital_republic.py` | Digital Republic Doctrine execution gate; enforces Tier 0 attestation and r=2.4 bound |
| `codex_tas_runner.py` | End-to-end runner (requires `OPENAI_API_KEY`) |

---

## Running

```bash
# Full test suite (no API key required)
python -m pytest tests/ -v

# Codex end-to-end runner
export OPENAI_API_KEY="your_api_key_here"
python codex_tas_runner.py

# Digital Republic Gatekeeper — canonical verification cases
python digital_republic.py

# PDR export — produces a SHA-256 chained receipt bundle
python pdr_export.py
python pdr_export.py --verify EXECUTE_01JAB7.json
```

---

## Tech Stack

- **Language:** Python 3.12
- **Dependencies:** `openai>=1.0.0`, `pytest>=7.0.0`
- **Testing:** 781 passing tests via `pytest`

---

## License

Add project license information here.

## User Preferences

- Keep the test suite as the primary workflow entry point.
