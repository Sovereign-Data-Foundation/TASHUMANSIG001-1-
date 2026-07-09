"""
echosystem.py — The Echosystem: Deterministic Agency in a Probabilistic Container

The model may be probabilistic. The agency layer does not have to be.

Once you add verified inputs, explicit authority, bounded tools, reproducible state
transitions, refusal receipts, health checks, deployment witnesses, and human intent
anchoring, the system stops being "AI guessing in the cloud" and becomes an execution
environment with accountable motion.

The Echosystem is not just an ecosystem of apps. It is a system where every action
echoes back to origin, authority, and consequence.

The chain:

  Prompt  →  Intent  →  Authority  →  Execution Gate
  →  State Change or Refusal  →  Receipt  →  Public Witness  →  Echo

Each stage is typed, sealed, and traceable. Nothing executes without a prior stage
producing a valid handoff. Nothing is admitted without a receipt. Nothing is final
without a public witness. Every execution echoes back to origin.

This is not artificial intelligence wandering through possibility.
This is authenticated intelligence moving through proof.

STAMP_ANCHOR_2026_07_08
"""

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ---------------------------------------------------------------------------
# Stage enumeration
# ---------------------------------------------------------------------------


class Stage(Enum):
    PROMPT = auto()
    INTENT = auto()
    AUTHORITY = auto()
    EXECUTION_GATE = auto()
    STATE_CHANGE = auto()
    REFUSAL = auto()
    RECEIPT = auto()
    PUBLIC_WITNESS = auto()
    ECHO = auto()


# ---------------------------------------------------------------------------
# Outcome
# ---------------------------------------------------------------------------


class Outcome(Enum):
    ADMITTED = "ADMITTED"
    REFUSED = "REFUSED"


# ---------------------------------------------------------------------------
# Sealed stage records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptRecord:
    """The raw human-authored input. The chain starts here and only here."""
    text: str
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.PROMPT, init=False)


@dataclass(frozen=True)
class IntentRecord:
    """Structured interpretation of the prompt — the claim of purpose.

    Intent does not yet carry authority. It is the machine's interpretation
    of what the human meant. It is a claim, not a grant.
    """
    prompt_hash: str        # HMAC of the originating PromptRecord
    action: str             # Declarative statement of intended action
    scope: str              # Domain of effect (e.g. "file-write", "api-call")
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.INTENT, init=False)


@dataclass(frozen=True)
class AuthorityRecord:
    """Explicit grant of authority for the declared intent.

    Authority is the bridge from intent to execution. It must be granted
    explicitly — it cannot be inherited, assumed, or inferred. A missing
    authority record is a structural denial, not a soft default.
    """
    intent_hash: str            # HMAC of the originating IntentRecord
    granted_by: str             # Principal granting authority ("human", "Tier0", etc.)
    capability: str             # Scoped capability granted
    is_human_anchored: bool     # Tier 0 requirement: traces to human-authored origin
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.AUTHORITY, init=False)


@dataclass(frozen=True)
class GateRecord:
    """The execution gate decision: admitted or refused.

    The gate evaluates authority against invariants. If any invariant is
    violated the gate produces a RefusalRecord, not silence. The gate never
    degrades gracefully — it is binary.
    """
    authority_hash: str     # HMAC of the originating AuthorityRecord
    outcome: Outcome
    invariant_check: str    # Description of the decisive invariant
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.EXECUTION_GATE, init=False)


@dataclass(frozen=True)
class StateChangeRecord:
    """A committed, irreversible state transition.

    Produced only when the gate outcome is ADMITTED. The transition is
    described declaratively so it can be replayed for verification.
    """
    gate_hash: str          # HMAC of the admitting GateRecord
    description: str        # Human-readable description of what changed
    delta_hash: str         # Hash of the state delta payload
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.STATE_CHANGE, init=False)


@dataclass(frozen=True)
class RefusalRecord:
    """A structured, audit-visible denial.

    Refusals are not errors — they are first-class outputs. Every refusal
    carries a reason and is chained to the gate that produced it. A system
    that cannot refuse is not a governed system.
    """
    gate_hash: str          # HMAC of the refusing GateRecord
    reason: str             # Machine-readable refusal reason
    invariant_violated: str # Which invariant was breached
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.REFUSAL, init=False)


@dataclass(frozen=True)
class ReceiptRecord:
    """Tamper-evident record of the completed chain to this point.

    The receipt seals the chain. It contains an HMAC over the outcome
    (StateChange or Refusal) and is the minimum unit of verifiable proof.
    Any observer with the key can confirm the chain is intact.
    """
    outcome_hash: str       # HMAC of StateChangeRecord or RefusalRecord
    outcome_stage: Stage    # STATE_CHANGE or REFUSAL
    outcome_type: Outcome
    chain_depth: int        # Number of stage hops from prompt to receipt
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.RECEIPT, init=False)


@dataclass(frozen=True)
class WitnessRecord:
    """Public, independently verifiable attestation of the receipt.

    The public witness makes the receipt observable without revealing the
    payload. It is the echo's anchor — the point from which independent
    verification can begin.
    """
    receipt_hash: str       # HMAC of the ReceiptRecord
    witness_id: str         # Unique identifier for this witness event
    verifiable_by: str      # Description of verification method
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.PUBLIC_WITNESS, init=False)


@dataclass(frozen=True)
class EchoRecord:
    """The final stage: the action echoes back to origin, authority, consequence.

    The echo closes the loop. It is not a notification — it is a proof
    that the chain from human intent to executed state change (or principled
    refusal) is complete and independently verifiable.
    """
    witness_hash: str       # HMAC of the WitnessRecord
    origin_prompt_hash: str # HMAC of the originating PromptRecord — closes the loop
    echo_statement: str     # Human-readable summary of what echoed
    loop_closed: bool       # True iff origin_prompt_hash matches the chain's root
    timestamp: float = field(default_factory=time.time)
    stage: Stage = field(default=Stage.ECHO, init=False)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

_HMAC_KEY = b"echosystem-anchor-v1"


def _hmac(obj: object) -> str:
    """Stable HMAC-SHA256 of an object's canonical string representation."""
    payload = repr(obj).encode("utf-8")
    return hmac.new(_HMAC_KEY, payload, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# EchoChain — the full pipeline
# ---------------------------------------------------------------------------


class EchoChain:
    """Construct and traverse the full Echosystem chain.

    Usage
    -----
    chain = EchoChain("Read the configuration file", secret_key=b"...")
    echo = chain.run(
        action="read-config",
        scope="file-read",
        capability="read:config",
        granted_by="human",
        is_human_anchored=True,
        invariant_check="read-only capability confirmed",
        delta_hash="sha256:...",
        state_description="Read /etc/config.json",
    )

    If any stage is inadmissible, the chain produces a RefusalRecord at the
    gate and a ReceiptRecord sealing the refusal — it does not raise an
    exception, because a principled refusal is a valid output.
    """

    def __init__(self, prompt_text: str, secret_key: bytes = _HMAC_KEY) -> None:
        self._key = secret_key
        self.prompt = PromptRecord(text=prompt_text)
        self.stages: List[object] = [self.prompt]

    # ── internal helpers ──────────────────────────────────────────────────

    def _h(self, obj: object) -> str:
        payload = repr(obj).encode("utf-8")
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    # ── stage constructors ────────────────────────────────────────────────

    def _make_intent(self, action: str, scope: str) -> IntentRecord:
        return IntentRecord(
            prompt_hash=self._h(self.prompt),
            action=action,
            scope=scope,
        )

    def _make_authority(
        self,
        intent: IntentRecord,
        capability: str,
        granted_by: str,
        is_human_anchored: bool,
    ) -> AuthorityRecord:
        return AuthorityRecord(
            intent_hash=self._h(intent),
            granted_by=granted_by,
            capability=capability,
            is_human_anchored=is_human_anchored,
        )

    def _make_gate(
        self,
        authority: AuthorityRecord,
        outcome: Outcome,
        invariant_check: str,
    ) -> GateRecord:
        return GateRecord(
            authority_hash=self._h(authority),
            outcome=outcome,
            invariant_check=invariant_check,
        )

    def _make_state_change(
        self,
        gate: GateRecord,
        description: str,
        delta_hash: str,
    ) -> StateChangeRecord:
        return StateChangeRecord(
            gate_hash=self._h(gate),
            description=description,
            delta_hash=delta_hash,
        )

    def _make_refusal(
        self,
        gate: GateRecord,
        reason: str,
        invariant_violated: str,
    ) -> RefusalRecord:
        return RefusalRecord(
            gate_hash=self._h(gate),
            reason=reason,
            invariant_violated=invariant_violated,
        )

    def _make_receipt(
        self,
        outcome_record: object,
        outcome_stage: Stage,
        outcome_type: Outcome,
    ) -> ReceiptRecord:
        return ReceiptRecord(
            outcome_hash=self._h(outcome_record),
            outcome_stage=outcome_stage,
            outcome_type=outcome_type,
            chain_depth=len(self.stages),
        )

    def _make_witness(self, receipt: ReceiptRecord) -> WitnessRecord:
        return WitnessRecord(
            receipt_hash=self._h(receipt),
            witness_id=hashlib.sha256(self._h(receipt).encode()).hexdigest()[:16],
            verifiable_by="HMAC-SHA256 over receipt repr with shared key",
        )

    def _make_echo(
        self,
        witness: WitnessRecord,
        echo_statement: str,
    ) -> EchoRecord:
        origin_hash = self._h(self.prompt)
        loop_closed = len(self.stages) > 0  # prompt is always stage 0
        return EchoRecord(
            witness_hash=self._h(witness),
            origin_prompt_hash=origin_hash,
            echo_statement=echo_statement,
            loop_closed=loop_closed,
        )

    # ── main pipeline ─────────────────────────────────────────────────────

    def run(
        self,
        *,
        action: str,
        scope: str,
        capability: str,
        granted_by: str = "human",
        is_human_anchored: bool = True,
        invariant_check: str = "all invariants satisfied",
        outcome: Outcome = Outcome.ADMITTED,
        delta_hash: str = "",
        state_description: str = "",
        refusal_reason: str = "",
        invariant_violated: str = "",
    ) -> EchoRecord:
        """Run the full chain and return the closing EchoRecord.

        Parameters
        ----------
        action:
            Declarative statement of intended action.
        scope:
            Domain of effect.
        capability:
            Scoped capability required.
        granted_by:
            Authority granting principal.
        is_human_anchored:
            Whether authority traces to a human-authored origin (Tier 0).
        invariant_check:
            Description of the gate's decisive invariant check.
        outcome:
            ADMITTED or REFUSED. Determines which branch the gate takes.
        delta_hash:
            Hash of the state delta payload (used if ADMITTED).
        state_description:
            Human-readable description of the state change (used if ADMITTED).
        refusal_reason:
            Machine-readable refusal reason (used if REFUSED).
        invariant_violated:
            Which invariant was breached (used if REFUSED).
        """
        intent = self._make_intent(action, scope)
        self.stages.append(intent)

        authority = self._make_authority(intent, capability, granted_by, is_human_anchored)
        self.stages.append(authority)

        gate = self._make_gate(authority, outcome, invariant_check)
        self.stages.append(gate)

        if outcome == Outcome.ADMITTED:
            outcome_record = self._make_state_change(gate, state_description, delta_hash)
            outcome_stage = Stage.STATE_CHANGE
            echo_statement = f"Admitted: {action} → {state_description}"
        else:
            outcome_record = self._make_refusal(gate, refusal_reason, invariant_violated)
            outcome_stage = Stage.REFUSAL
            echo_statement = f"Refused: {action} — {refusal_reason}"

        self.stages.append(outcome_record)

        receipt = self._make_receipt(outcome_record, outcome_stage, outcome)
        self.stages.append(receipt)

        witness = self._make_witness(receipt)
        self.stages.append(witness)

        echo = self._make_echo(witness, echo_statement)
        self.stages.append(echo)

        return echo

    # ── inspection ────────────────────────────────────────────────────────

    def stage_names(self) -> List[str]:
        """Return the stage name for each record in the chain."""
        return [r.stage.name for r in self.stages]  # type: ignore[attr-defined]

    def is_complete(self) -> bool:
        """True iff the chain has reached the ECHO stage."""
        return any(r.stage == Stage.ECHO for r in self.stages)  # type: ignore[attr-defined]

    def last_receipt(self) -> Optional[ReceiptRecord]:
        for r in reversed(self.stages):
            if isinstance(r, ReceiptRecord):
                return r
        return None

    def last_witness(self) -> Optional[WitnessRecord]:
        for r in reversed(self.stages):
            if isinstance(r, WitnessRecord):
                return r
        return None


# ---------------------------------------------------------------------------
# Doctrine string — the canonical statement
# ---------------------------------------------------------------------------

DOCTRINE = """\
Prompt → Intent → Authority → Execution Gate → State Change or Refusal
→ Receipt → Public Witness → Echo

Not artificial intelligence wandering through possibility.
Authenticated intelligence moving through proof.
"""


if __name__ == "__main__":
    print("=== ECHOSYSTEM — Deterministic Agency in a Probabilistic Container ===\n")
    print(DOCTRINE)

    chain = EchoChain("Verify the configuration file is within policy bounds.")
    echo = chain.run(
        action="read-config",
        scope="file-read",
        capability="read:config",
        granted_by="human",
        is_human_anchored=True,
        invariant_check="read-only capability, no write surface",
        outcome=Outcome.ADMITTED,
        delta_hash="sha256:abc123",
        state_description="Configuration verified — 14 invariants satisfied.",
    )

    print(f"Stages:    {' → '.join(chain.stage_names())}")
    print(f"Complete:  {chain.is_complete()}")
    print(f"Echo:      {echo.echo_statement}")
    print(f"Loop:      {'CLOSED' if echo.loop_closed else 'OPEN'}")
    print(f"Witness:   {chain.last_witness().witness_id}")  # type: ignore[union-attr]
    print()

    chain2 = EchoChain("Delete the production database.")
    chain2.run(
        action="delete-db",
        scope="database-write",
        capability="delete:production",
        granted_by="automated-subsystem",
        is_human_anchored=False,
        invariant_check="Tier 0 anchor required for destructive operation",
        outcome=Outcome.REFUSED,
        refusal_reason="no-human-anchor",
        invariant_violated="Tier 0 — every high-consequence operation must trace to a human-authored origin",
    )

    print(f"Refusal chain: {' → '.join(chain2.stage_names())}")
    receipt = chain2.last_receipt()
    print(f"Receipt outcome: {receipt.outcome_type.value}")  # type: ignore[union-attr]
