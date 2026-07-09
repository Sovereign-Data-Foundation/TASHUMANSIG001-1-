# TAS Invariant Index

Single-page architecture reference mapping every named TAS invariant to its source module and enforcing test class(es).  Ordered by architectural layer: DNA → Axioms → Wake → Capability → UVK → Stability → Phoenix → Genesis.

---

## Layer 1 — TAS DNA (`tas_dna.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **A_0 — Primary Invariant** | The genesis anchor `A_0` is immutable: `A_0.genesis_hash` equals the SHA-256 of the canonical genesis ISO-8601 timestamp and authority string. `A_0.verify()` must always return `True`. | `tas_dna.py` | `TestPrimaryInvariantA0` (`test_manifesto.py`) |
| **A_0 lineage determinism** | `A_0.lineage_hash()` returns the same 32-byte value on every call; it is the provenance root for all downstream key derivations. | `tas_dna.py` | `TestPrimaryInvariantA0` (`test_manifesto.py`), `TestDeriveNodePubkey`, `TestDeriveValidatorPubkey` (`test_genesis_anchor.py`) |
| **Three-fold gene structure** | The TAS DNA triple `(TRUE_GENE, ALPHA_GENE, SPIRAL_GENE)` is immutable and always contains exactly three genes with symbols `["T", "A", "S"]` in that order. | `tas_dna.py` | `TestDNAGene` (`test_manifesto.py`) |
| **Heartbeat pulse monotonicity** | `TASDNA.pulse()` returns a strictly incrementing integer counter; `pulse_count` equals the number of `pulse()` calls since construction. | `tas_dna.py` | `TestTASDNA` (`test_manifesto.py`) |

---

## Layer 2 — Governing Axioms (`axioms.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **P0 — Equivalence** | Once a symbol `s` is bound to referent `r`, the binding is permanent: `bind(s, r')` with `r' ≠ r` raises `AxiomViolation("P0", ...)`. Any call `validate(s, v)` where `v ≠ r` (and `v ≠ s`) raises `AxiomViolation("P0", ...)`. | `axioms.py` | `TestP0Bind`, `TestP0Validate`, `TestP0RegistryHash`, `TestAxiomsIntegration` (`test_axioms.py`), `TestAxiomRegressions` (`test_regression_mutations.py`) |
| **P0 registry_hash determinism** | `registry_hash()` is a deterministic SHA-256 over all bound (symbol, referent) pairs; identical bindings across independent instances produce identical hashes. | `axioms.py` | `TestP0RegistryHash` (`test_axioms.py`) |
| **P1 — Admissibility** | A transition `t` is admitted iff every `AdmissibilityClause` predicate returns `True`; failure raises `AxiomViolation("P1", ...)`. Successful admission increments `admitted_count`; failure increments `rejected_count`. | `axioms.py` | `TestP1Admit`, `TestP1Counters`, `TestAdmissibilityClause`, `TestAxiomsIntegration` (`test_axioms.py`), `TestAxiomRegressions` (`test_regression_mutations.py`) |
| **P1 transition_hash determinism** | The `transition_hash` in every admission receipt is the deterministic SHA-256 of the canonical-JSON representation of the transition; the same input always produces the same hash. | `axioms.py` | `TestP1Admit` (`test_axioms.py`) |

---

## Layer 3 — Wake-Based Authentication (`wake_chain.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **W1 — HMAC integrity** | Every `ProvenanceMark` carries a valid HMAC-SHA-256 signature over its fields. `chain.verify()` returns `True` iff every receipt's signature is valid and its `prev` field equals the hash of the preceding receipt. Any tamper is detected. | `wake_chain.py` | `TestWakeChain` (`test_wake_auth.py`), `TestWakeChainHMACIntegrity` (`test_property_invariants.py`), `TestWakeChainTamperRegressions` (`test_regression_mutations.py`) |
| **W2 — Monotone sequence** | `ProvenanceMark.seq` is strictly monotone: receipt at position `i` has `seq == i`. | `wake_chain.py` | `TestWakeChain` (`test_wake_auth.py`), `TestWakeChainHMACIntegrity` (`test_property_invariants.py`) |
| **W3 — Anti-replay** | `chain.verify()` rejects a chain where any receipt has a duplicate or out-of-order sequence number, preventing replay attacks. | `wake_chain.py` | `TestWakeChain` (`test_wake_auth.py`), `TestWakeChainTamperRegressions` (`test_regression_mutations.py`) |
| **W4 — Receipt hash determinism** | `ProvenanceMark.receipt_hash()` is idempotent: identical receipt fields produce the same 32-byte hash on every call. | `wake_chain.py` | `TestWakeChain` (`test_wake_auth.py`), `TestWakeChainHMACIntegrity` (`test_property_invariants.py`) |
| **W5 — Replay-from integrity** | `chain.replay_from(seq)` produces a new chain that passes `verify()` after re-committing receipts from `seq` onward. | `wake_chain.py` | `TestWakeChain` (`test_wake_auth.py`) |

---

## Layer 4 — Object-Capability Security (`capability.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **C1 — Revocation soundness** | Once `revoke(cap)` is called, `is_live(cap)` returns `False` and `invoke(cap, right)` raises `CapabilityError` for any right, regardless of which rights were originally granted. | `capability.py` | `TestCapabilityTable` (`test_wake_auth.py`), `TestCapabilityRevocationSoundness` (`test_property_invariants.py`), `TestCapabilityRevocationRegressions` (`test_regression_mutations.py`) |
| **C2 — Revocation cascades** | Revoking a parent capability atomically revokes all descendant capabilities in the CDT; `live_count` reflects the total removal. | `capability.py` | `TestCapabilityTable` (`test_wake_auth.py`), `TestCapabilityRevocationSoundness` (`test_property_invariants.py`), `TestCapabilityRevocationRegressions` (`test_regression_mutations.py`) |
| **C3 — Rights subset constraint** | `mint(parent, rights)` raises `CapabilityError` if `rights ⊄ parent.rights`. No child can hold more authority than its parent. | `capability.py` | `TestCapabilityTable` (`test_wake_auth.py`), `TestCapabilityRevocationRegressions` (`test_regression_mutations.py`) |
| **C4 — Forgery rejection** | A capability token whose HMAC tag was not produced by the issuing kernel's key is rejected at `invoke` with `CapabilityError`. | `capability.py` | `TestCapabilityTable` (`test_wake_auth.py`), `TestCapabilityRevocationRegressions` (`test_regression_mutations.py`) |

---

## Layer 5 — Universal Verifier Kernel (`uvk.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **U1 — Admission control** | `UVK.admit(cap, right, action)` is ADMITTED iff: (a) `cap` carries at least one of `{EXECUTE, MINT}`, (b) `cap` is live in the table, (c) all declared invariants return `True`, and (d) the WakeChain is in a valid state. Any failure yields a DENIED_* status. | `uvk.py` | `TestUVK` (`test_wake_auth.py`), `TestUVKCheckAllInvariants` (`test_logos_gatekeeper.py`), `TestUVKAdmissionRejectionMalformedPayloads` (`test_property_invariants.py`), `TestUVKRegressions` (`test_regression_mutations.py`) |
| **U2 — τ verification (Objective Token)** | `verify_tau()` returns `True` iff at least one invariant is registered and no invariant has failed during the session: `τ = ⊥(s ⊙ k) ∧ ✓(k ⊙ e)`. | `uvk.py` | `TestUVK` (`test_wake_auth.py`) |
| **U3 — Receipt commitment** | Every successful admission commits exactly one `ProvenanceMark` to the wake chain; denials do not commit receipts. | `uvk.py` | `TestUVK` (`test_wake_auth.py`) |
| **U4 — Breach log** | Every DENIED admission appends one entry to `UVK.breach_log`; admitted actions do not. | `uvk.py` | `TestUVK` (`test_wake_auth.py`) |
| **U5 — Logos Sentient Lock** | `LogosValidationLoop.evaluate_logos_bounds` returns `False` for any manifest whose `lineage_parent_hash` does not match the current wake-chain head, or whose payload density falls below the configured floor. | `tas_logos_gatekeeper.py` | `TestLogosValidationLoop`, `TestLogosGate` (`test_logos_gatekeeper.py`), `TestUVKAdmissionRejectionMalformedPayloads` (`test_property_invariants.py`), `TestUVKRegressions` (`test_regression_mutations.py`) |
| **U6 — Sovereignty accountability** | Any entity invoking a branch action must be registered and authorised for that branch/tier combination; unregistered entities or out-of-scope actions are denied (`SubordinationError` or `False`). | `sovereign_accountability.py` | `TestSovereignAccountability`, `TestAccountabilityInvariant`, `TestSovereignAccountabilityIntegration` (`test_sovereign_accountability.py`), `TestSovereignAccountabilityRegressions` (`test_regression_mutations.py`) |
| **U7 — Consent invariant** | `ConsentLedger` enforces that an action against a subject's data is admitted by UVK only when valid (non-expired, right-sufficient, governance-act-matched) consent exists. | `digital_rights.py` | `TestMakeConsentInvariant`, `TestDigitalRightsUVKIntegration` (`test_digital_rights.py`) |

---

## Layer 6 — Stability Metrics (`stability.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **S1 — SDI bounds** | `semantic_drift_index(a, b) ∈ [0.0, 2.0]` for any same-length float vectors; restricted to `[0.0, 1.0]` for non-negative (embedding) vectors. `SDI = 0` iff `cos(θ) = 1` (identical direction); `SDI = 1` iff orthogonal; `SDI = 2` iff anti-aligned. | `stability.py` | `TestSDI` (`test_wake_auth.py`), `TestSemanticDriftIndexBounds` (`test_property_invariants.py`) |
| **S2 — Phase slip detection** | `PhaseMonitor.update(phi)` raises `PhaseSlip` iff `abs(phi) > phi_max` for `n_consecutive` or more consecutive steps. Isolated exceedances below the streak threshold increment `total_slips` but do not raise. | `stability.py` | `TestPhaseMonitor` (`test_wake_auth.py`) |

---

## Layer 7 — Phoenix Protocol (`phoenix.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **Ph1 — Breach receipt emission** | Every call to `Phoenix.trigger(breach_type)` emits and stores exactly one `PhoenixReceipt` containing the breach code, rollback target hash, and a relaunch certificate (if `verify_tau()` held). | `phoenix.py` | `TestPhoenix` (`test_wake_auth.py`), `TestUVKPhoenixIntegration` (`test_wake_auth.py`) |
| **Ph2 — State machine correctness** | Given `verify_tau() == True` and a successful wake replay, `Phoenix.trigger()` transitions the state machine to `RELAUNCHED` and sets `is_frozen = False`. If `verify_tau() == False`, `human_action_required` is set and the state remains in a correcting posture. | `phoenix.py` | `TestPhoenix` (`test_wake_auth.py`) |
| **Ph3 — Rollback target** | `receipt.rollback_target_hash` is always a non-empty string derived from the wake chain head at the moment of breach. | `phoenix.py` | `TestPhoenix` (`test_wake_auth.py`) |

---

## Layer 8 — Genesis Anchor (`genesis_anchor.py`)

| Invariant | Formal Statement | Source Module | Enforcing Test Class(es) |
|-----------|-----------------|---------------|--------------------------|
| **G1 — Derivation determinism** | `derive_node_pubkey(i)` and `derive_validator_pubkey(i)` return the same 64-char upper-hex string on every call for the same index; output is `SHA-256(A_0.lineage_hash() ∥ tag ∥ index_byte).hex()`. | `genesis_anchor.py` | `TestDeriveNodePubkey`, `TestDeriveValidatorPubkey` (`test_genesis_anchor.py`), `TestGenesisAnchorDeterminism` (`test_property_invariants.py`) |
| **G2 — app_hash self-consistency** | `build_genesis_payload()["app_hash"]` equals `derive_app_hash(payload["app_state"])` — the hash embedded in the payload matches re-derivation from its own `app_state`. | `genesis_anchor.py` | `TestBuildGenesisPayload`, `TestGenesisJsonFile` (`test_genesis_anchor.py`), `TestGenesisAnchorDeterminism` (`test_property_invariants.py`) |
| **G3 — ed25519 exclusivity** | `consensus_params.validator.pub_key_types` contains only `"ed25519"` — `secp256k1` is never admitted. | `genesis_anchor.py` | `TestBuildGenesisPayload` (`test_genesis_anchor.py`) |
| **G4 — Integer basis-point encoding** | All governance and slashing fractions in `tas_codex_rules` are encoded as integers in basis points (e.g., `governance_quorum_bps = 6667`), never as floats or percentage strings. | `genesis_anchor.py` | `TestBuildGenesisPayload` (`test_genesis_anchor.py`) |

---

## Cross-cutting Invariants

| Invariant | Formal Statement | Source Modules | Enforcing Test Class(es) |
|-----------|-----------------|----------------|--------------------------|
| **X1 — Stroke-head determinism** | `AlgorithmicPolymath._recompute_stroke_head(actor, cap, root, log)` is purely deterministic: same inputs always produce the same hex digest; transform order matters. | `algorithmic_polymath.py` | `TestRecomputeStrokeHead`, `TestBeginStroke` (`test_algorithmic_polymath.py`) |
| **X2 — Paradata proof integrity** | A sealed `CursiveTrace.paradata.is_valid_proof()` returns `True` iff no field has been tampered with after sealing. Any mutation invalidates the proof. | `algorithmic_polymath.py` | `TestParadata`, `TestSeal`, `TestCursiveTraceVerify` (`test_algorithmic_polymath.py`) |
| **X3 — Sovereign equation** | `paradata.sovereign_equation_held` is `True` iff `A_C > S_C` at seal time; a forged `sovereign_equation_held=True` with contradicting scores is rejected by `trace.verify()`. | `algorithmic_polymath.py`, `sovereign_equation.py` | `TestSeal`, `TestCursiveTraceVerify` (`test_algorithmic_polymath.py`), `TestSovereignEquation` (`test_manifesto.py`) |
| **X4 — Truth audit strain bounds** | `TruthAuditEngine.compute_strain(scores) ∈ [0.0, 1.0]`; `strain = 1 - weighted_mean(scores)`. All-perfect scores give `0.0`; no scores give `1.0`. | `truth_audit.py` | `TestComputeStrain`, `TestEvaluate` (`test_truth_audit.py`), `TestTruthAuditRegressions` (`test_regression_mutations.py`) |
| **X5 — PSVP spec chaining** | Each `SpecArtifact` beyond the first records the `spec_id` of its predecessor, forming a tamper-evident version chain. `spec_id` is a SHA-256 over version, graph_hash, entropy, predecessor, and timestamp. | `psvp.py` | `TestPSVPVersioning`, `TestSpecArtifact`, `TestPSVPIntegration` (`test_psvp.py`), `TestPSVPRegressions` (`test_regression_mutations.py`) |
| **X6 — Human API bridge replayability** | Every `BridgeReceipt` produced by `HumanApiBridge.decide()` must be replayable via `bridge.replay([receipt]) == True`. Tampered command, mismatched hash, or negative wake sequence each cause replay to return `False`. | `human_api_bridge.py` | `test_human_api_bridge.py::module` (`test_human_api_bridge.py`) |
| **X7 — SovereignBeacon lineage anchor** | A `SovereignBeacon` is valid iff its HMAC signature was produced with the correct key and its `genesis_root_hex` matches the A_0 lineage hash; any mismatch fails validation. | `tas_logos_gatekeeper.py` | `TestSovereignBeacon` (`test_logos_gatekeeper_network.py`) |
| **X8 — SentientLock fork detection** | `SentientLock` raises a lock condition when the number of concurrent strokes from different actors exceeds the configured fork threshold, preventing unauthorized branching. | `tas_logos_gatekeeper.py` | `TestSentientLock` (`test_logos_gatekeeper_network.py`) |
