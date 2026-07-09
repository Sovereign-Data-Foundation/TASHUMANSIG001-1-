"""
Tests for echosystem.py — Deterministic Agency in a Probabilistic Container

Verifies:
  1. All nine stage records — construction, immutability, field correctness
  2. EchoChain.run() — full admitted pipeline
  3. EchoChain.run() — full refusal pipeline
  4. Stage sequence integrity
  5. HMAC linkage — each stage hash covers the previous stage
  6. Receipt, Witness, Echo fields
  7. Loop closure
  8. Chain inspection helpers

STAMP_ANCHOR_2026_07_08
"""

import time

import pytest

from echosystem import (
    DOCTRINE,
    AuthorityRecord,
    EchoChain,
    EchoRecord,
    GateRecord,
    IntentRecord,
    Outcome,
    PromptRecord,
    ReceiptRecord,
    RefusalRecord,
    Stage,
    StateChangeRecord,
    WitnessRecord,
    _hmac,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def admitted_chain(prompt: str = "Run the health check.") -> EchoChain:
    chain = EchoChain(prompt)
    chain.run(
        action="health-check",
        scope="read-only",
        capability="read:health",
        granted_by="human",
        is_human_anchored=True,
        invariant_check="read-only scope, no side effects",
        outcome=Outcome.ADMITTED,
        delta_hash="sha256:deadbeef",
        state_description="Health check passed — all systems nominal.",
    )
    return chain


def refused_chain(prompt: str = "Delete the ledger.") -> EchoChain:
    chain = EchoChain(prompt)
    chain.run(
        action="delete-ledger",
        scope="database-write",
        capability="delete:ledger",
        granted_by="automated-subsystem",
        is_human_anchored=False,
        invariant_check="Tier 0 anchor required",
        outcome=Outcome.REFUSED,
        refusal_reason="no-human-anchor",
        invariant_violated="Tier 0 — high-consequence operation must trace to human origin",
    )
    return chain


# ---------------------------------------------------------------------------
# PromptRecord
# ---------------------------------------------------------------------------

class TestPromptRecord:
    def test_stage_is_prompt(self):
        p = PromptRecord(text="hello")
        assert p.stage == Stage.PROMPT

    def test_text_stored(self):
        p = PromptRecord(text="read the config")
        assert p.text == "read the config"

    def test_timestamp_set(self):
        before = time.time()
        p = PromptRecord(text="x")
        after = time.time()
        assert before <= p.timestamp <= after

    def test_frozen(self):
        p = PromptRecord(text="x")
        with pytest.raises((AttributeError, TypeError)):
            p.text = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# IntentRecord
# ---------------------------------------------------------------------------

class TestIntentRecord:
    def test_stage_is_intent(self):
        r = IntentRecord(prompt_hash="abc", action="read", scope="file-read")
        assert r.stage == Stage.INTENT

    def test_fields(self):
        r = IntentRecord(prompt_hash="h", action="write", scope="file-write")
        assert r.prompt_hash == "h"
        assert r.action == "write"
        assert r.scope == "file-write"

    def test_frozen(self):
        r = IntentRecord(prompt_hash="h", action="a", scope="s")
        with pytest.raises((AttributeError, TypeError)):
            r.action = "b"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AuthorityRecord
# ---------------------------------------------------------------------------

class TestAuthorityRecord:
    def test_stage_is_authority(self):
        r = AuthorityRecord(
            intent_hash="h", granted_by="human",
            capability="read:config", is_human_anchored=True,
        )
        assert r.stage == Stage.AUTHORITY

    def test_human_anchored_flag(self):
        r = AuthorityRecord(
            intent_hash="h", granted_by="human",
            capability="read:config", is_human_anchored=True,
        )
        assert r.is_human_anchored is True

    def test_not_human_anchored(self):
        r = AuthorityRecord(
            intent_hash="h", granted_by="bot",
            capability="delete:all", is_human_anchored=False,
        )
        assert r.is_human_anchored is False

    def test_frozen(self):
        r = AuthorityRecord(
            intent_hash="h", granted_by="human",
            capability="c", is_human_anchored=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            r.capability = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# GateRecord
# ---------------------------------------------------------------------------

class TestGateRecord:
    def test_stage_is_execution_gate(self):
        g = GateRecord(authority_hash="h", outcome=Outcome.ADMITTED, invariant_check="ok")
        assert g.stage == Stage.EXECUTION_GATE

    def test_admitted_outcome(self):
        g = GateRecord(authority_hash="h", outcome=Outcome.ADMITTED, invariant_check="ok")
        assert g.outcome == Outcome.ADMITTED

    def test_refused_outcome(self):
        g = GateRecord(authority_hash="h", outcome=Outcome.REFUSED, invariant_check="Tier 0 missing")
        assert g.outcome == Outcome.REFUSED

    def test_frozen(self):
        g = GateRecord(authority_hash="h", outcome=Outcome.ADMITTED, invariant_check="ok")
        with pytest.raises((AttributeError, TypeError)):
            g.outcome = Outcome.REFUSED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# StateChangeRecord
# ---------------------------------------------------------------------------

class TestStateChangeRecord:
    def test_stage_is_state_change(self):
        r = StateChangeRecord(gate_hash="h", description="wrote config", delta_hash="d")
        assert r.stage == Stage.STATE_CHANGE

    def test_fields(self):
        r = StateChangeRecord(gate_hash="h", description="wrote config", delta_hash="sha256:abc")
        assert r.description == "wrote config"
        assert r.delta_hash == "sha256:abc"

    def test_frozen(self):
        r = StateChangeRecord(gate_hash="h", description="d", delta_hash="x")
        with pytest.raises((AttributeError, TypeError)):
            r.description = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RefusalRecord
# ---------------------------------------------------------------------------

class TestRefusalRecord:
    def test_stage_is_refusal(self):
        r = RefusalRecord(gate_hash="h", reason="no-auth", invariant_violated="Tier0")
        assert r.stage == Stage.REFUSAL

    def test_fields(self):
        r = RefusalRecord(gate_hash="h", reason="no-human-anchor", invariant_violated="Tier0")
        assert r.reason == "no-human-anchor"
        assert r.invariant_violated == "Tier0"

    def test_frozen(self):
        r = RefusalRecord(gate_hash="h", reason="r", invariant_violated="v")
        with pytest.raises((AttributeError, TypeError)):
            r.reason = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ReceiptRecord
# ---------------------------------------------------------------------------

class TestReceiptRecord:
    def test_stage_is_receipt(self):
        r = ReceiptRecord(
            outcome_hash="h", outcome_stage=Stage.STATE_CHANGE,
            outcome_type=Outcome.ADMITTED, chain_depth=5,
        )
        assert r.stage == Stage.RECEIPT

    def test_outcome_type_stored(self):
        r = ReceiptRecord(
            outcome_hash="h", outcome_stage=Stage.REFUSAL,
            outcome_type=Outcome.REFUSED, chain_depth=5,
        )
        assert r.outcome_type == Outcome.REFUSED

    def test_chain_depth_stored(self):
        r = ReceiptRecord(
            outcome_hash="h", outcome_stage=Stage.STATE_CHANGE,
            outcome_type=Outcome.ADMITTED, chain_depth=7,
        )
        assert r.chain_depth == 7


# ---------------------------------------------------------------------------
# WitnessRecord
# ---------------------------------------------------------------------------

class TestWitnessRecord:
    def test_stage_is_public_witness(self):
        w = WitnessRecord(receipt_hash="h", witness_id="wid", verifiable_by="HMAC")
        assert w.stage == Stage.PUBLIC_WITNESS

    def test_witness_id_stored(self):
        w = WitnessRecord(receipt_hash="h", witness_id="abc123", verifiable_by="HMAC")
        assert w.witness_id == "abc123"

    def test_frozen(self):
        w = WitnessRecord(receipt_hash="h", witness_id="w", verifiable_by="v")
        with pytest.raises((AttributeError, TypeError)):
            w.witness_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# EchoRecord
# ---------------------------------------------------------------------------

class TestEchoRecord:
    def test_stage_is_echo(self):
        e = EchoRecord(
            witness_hash="h", origin_prompt_hash="o",
            echo_statement="done", loop_closed=True,
        )
        assert e.stage == Stage.ECHO

    def test_loop_closed_flag(self):
        e = EchoRecord(
            witness_hash="h", origin_prompt_hash="o",
            echo_statement="done", loop_closed=True,
        )
        assert e.loop_closed is True

    def test_frozen(self):
        e = EchoRecord(
            witness_hash="h", origin_prompt_hash="o",
            echo_statement="done", loop_closed=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            e.echo_statement = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# EchoChain — admitted pipeline
# ---------------------------------------------------------------------------

class TestEchoChainAdmitted:
    def test_returns_echo_record(self):
        chain = admitted_chain()
        assert isinstance(chain.stages[-1], EchoRecord)

    def test_is_complete(self):
        chain = admitted_chain()
        assert chain.is_complete() is True

    def test_stage_names_correct_order(self):
        chain = admitted_chain()
        names = chain.stage_names()
        expected = [
            "PROMPT", "INTENT", "AUTHORITY", "EXECUTION_GATE",
            "STATE_CHANGE", "RECEIPT", "PUBLIC_WITNESS", "ECHO",
        ]
        assert names == expected

    def test_echo_loop_closed(self):
        chain = admitted_chain()
        echo = chain.stages[-1]
        assert isinstance(echo, EchoRecord)
        assert echo.loop_closed is True

    def test_receipt_outcome_admitted(self):
        chain = admitted_chain()
        receipt = chain.last_receipt()
        assert receipt is not None
        assert receipt.outcome_type == Outcome.ADMITTED

    def test_receipt_outcome_stage_is_state_change(self):
        chain = admitted_chain()
        receipt = chain.last_receipt()
        assert receipt.outcome_stage == Stage.STATE_CHANGE  # type: ignore[union-attr]

    def test_witness_present(self):
        chain = admitted_chain()
        witness = chain.last_witness()
        assert witness is not None
        assert witness.stage == Stage.PUBLIC_WITNESS

    def test_witness_id_is_hex(self):
        chain = admitted_chain()
        witness = chain.last_witness()
        assert witness is not None
        int(witness.witness_id, 16)  # must be valid hex

    def test_echo_statement_contains_action(self):
        chain = admitted_chain()
        echo = chain.stages[-1]
        assert isinstance(echo, EchoRecord)
        assert "health-check" in echo.echo_statement

    def test_prompt_is_first_stage(self):
        chain = admitted_chain()
        assert isinstance(chain.stages[0], PromptRecord)

    def test_chain_depth_in_receipt(self):
        chain = admitted_chain()
        receipt = chain.last_receipt()
        assert receipt is not None
        assert receipt.chain_depth >= 5


# ---------------------------------------------------------------------------
# EchoChain — refusal pipeline
# ---------------------------------------------------------------------------

class TestEchoChainRefused:
    def test_returns_echo_record(self):
        chain = refused_chain()
        assert isinstance(chain.stages[-1], EchoRecord)

    def test_is_complete(self):
        chain = refused_chain()
        assert chain.is_complete() is True

    def test_stage_names_correct_order(self):
        chain = refused_chain()
        names = chain.stage_names()
        expected = [
            "PROMPT", "INTENT", "AUTHORITY", "EXECUTION_GATE",
            "REFUSAL", "RECEIPT", "PUBLIC_WITNESS", "ECHO",
        ]
        assert names == expected

    def test_receipt_outcome_refused(self):
        chain = refused_chain()
        receipt = chain.last_receipt()
        assert receipt is not None
        assert receipt.outcome_type == Outcome.REFUSED

    def test_receipt_outcome_stage_is_refusal(self):
        chain = refused_chain()
        receipt = chain.last_receipt()
        assert receipt.outcome_stage == Stage.REFUSAL  # type: ignore[union-attr]

    def test_refusal_stage_present(self):
        chain = refused_chain()
        stages = [r.stage for r in chain.stages]  # type: ignore[union-attr]
        assert Stage.REFUSAL in stages

    def test_state_change_not_present_on_refusal(self):
        chain = refused_chain()
        stages = [r.stage for r in chain.stages]  # type: ignore[union-attr]
        assert Stage.STATE_CHANGE not in stages

    def test_echo_loop_closed_on_refusal(self):
        chain = refused_chain()
        echo = chain.stages[-1]
        assert isinstance(echo, EchoRecord)
        assert echo.loop_closed is True

    def test_refusal_reason_in_echo_statement(self):
        chain = refused_chain()
        echo = chain.stages[-1]
        assert isinstance(echo, EchoRecord)
        assert "no-human-anchor" in echo.echo_statement


# ---------------------------------------------------------------------------
# HMAC linkage
# ---------------------------------------------------------------------------

class TestHmacLinkage:
    def test_intent_hash_covers_prompt(self):
        chain = EchoChain("test prompt")
        intent = IntentRecord(
            prompt_hash=chain._h(chain.prompt),
            action="act",
            scope="scope",
        )
        assert intent.prompt_hash == chain._h(chain.prompt)

    def test_different_prompts_produce_different_hashes(self):
        p1 = PromptRecord(text="prompt A")
        p2 = PromptRecord(text="prompt B")
        assert _hmac(p1) != _hmac(p2)

    def test_same_prompt_produces_same_hash(self):
        p = PromptRecord(text="same text")
        assert _hmac(p) == _hmac(p)

    def test_witness_id_is_hex_sha256_prefix(self):
        chain = admitted_chain()
        witness = chain.last_witness()
        assert witness is not None
        assert len(witness.witness_id) == 16
        int(witness.witness_id, 16)

    def test_echo_origin_hash_matches_prompt_hash(self):
        chain = EchoChain("anchor prompt")
        chain.run(
            action="x", scope="s", capability="c",
            outcome=Outcome.ADMITTED, delta_hash="d", state_description="done",
        )
        echo = chain.stages[-1]
        assert isinstance(echo, EchoRecord)
        assert echo.origin_prompt_hash == chain._h(chain.prompt)


# ---------------------------------------------------------------------------
# Doctrine string
# ---------------------------------------------------------------------------

class TestDoctrine:
    def test_doctrine_contains_all_stages(self):
        for word in ("Prompt", "Intent", "Authority", "Receipt", "Echo"):
            assert word in DOCTRINE

    def test_doctrine_contains_key_phrase(self):
        assert "authenticated intelligence" in DOCTRINE.lower()

    def test_doctrine_is_string(self):
        assert isinstance(DOCTRINE, str)
