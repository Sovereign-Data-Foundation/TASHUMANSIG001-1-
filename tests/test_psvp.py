"""Tests for the Problem Statement Versioning Protocol (PSVP).

Covers:
- shannon_entropy: correctness, edge cases
- Claim: from_text, frozen, to_dict
- ClaimGraph: mean_entropy, graph_hash, to_dict, dependency chain
- SpecArtifact: fields, to_dict, predecessor chaining
- DriftGateError: attributes
- PSVP: decompose, density gate, drift gate, create_spec, history, versioning
- Integration: full pipeline and predecessor chains
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math

import pytest

from psvp import (
    shannon_entropy,
    Claim,
    ClaimGraph,
    SpecArtifact,
    DriftGateError,
    PSVP,
    _tokenise,
)


# ===========================================================================
# shannon_entropy
# ===========================================================================


class TestShannonEntropy:
    """Invariant X5 — PSVP: shannon_entropy correctness and properties.

    Enforces: entropy is non-negative; zero for a single or all-identical token list;
    deterministic for the same input; higher diversity produces higher entropy.
    """

    def test_empty_tokens_returns_zero(self):
        assert shannon_entropy([]) == 0.0

    def test_single_token_returns_zero(self):
        assert shannon_entropy(["hello"]) == 0.0

    def test_two_equal_tokens_returns_one(self):
        h = shannon_entropy(["a", "a"])
        assert h == 0.0

    def test_two_distinct_tokens_returns_one(self):
        h = shannon_entropy(["a", "b"])
        assert abs(h - 1.0) < 1e-9

    def test_uniform_four_tokens(self):
        h = shannon_entropy(["a", "b", "c", "d"])
        assert abs(h - 2.0) < 1e-9

    def test_entropy_is_non_negative(self):
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        assert shannon_entropy(tokens) >= 0.0

    def test_repeated_tokens_lower_entropy(self):
        diverse   = ["a", "b", "c", "d", "e"]
        repetitive = ["a", "a", "a", "a", "b"]
        assert shannon_entropy(diverse) > shannon_entropy(repetitive)

    def test_deterministic_for_same_input(self):
        tokens = ["implement", "wake", "chain", "with", "hmac"]
        assert shannon_entropy(tokens) == shannon_entropy(tokens)


# ===========================================================================
# _tokenise
# ===========================================================================


class TestTokenise:
    """Invariant X5 — PSVP: _tokenise normalisation.

    Enforces: _tokenise lowercases all tokens, strips punctuation, and returns
    an empty list for empty or whitespace-only input — ensuring entropy
    computation is case-insensitive and punctuation-agnostic.
    """

    def test_lowercases_tokens(self):
        assert "HELLO" not in _tokenise("HELLO world")
        assert "hello" in _tokenise("HELLO world")

    def test_strips_punctuation(self):
        tokens = _tokenise("Hello, world.")
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_string_returns_empty(self):
        assert _tokenise("") == []

    def test_whitespace_only_returns_empty(self):
        assert _tokenise("   ") == []


# ===========================================================================
# Claim
# ===========================================================================


class TestClaim:
    """Invariant X5 — PSVP: Claim from_text construction.

    Enforces: Claim.from_text produces a frozen Claim with deterministic SHA-256
    over the text; different texts produce different hashes; entropy is non-negative;
    to_dict round-trip preserves all fields.
    """

    def test_from_text_sets_index(self):
        c = Claim.from_text(3, "some text here")
        assert c.index == 3

    def test_from_text_sets_text(self):
        c = Claim.from_text(0, "hello world")
        assert c.text == "hello world"

    def test_sha256_is_64_hex_chars(self):
        c = Claim.from_text(0, "test")
        assert len(c.sha256) == 64
        assert all(ch in "0123456789abcdef" for ch in c.sha256)

    def test_sha256_deterministic(self):
        c1 = Claim.from_text(0, "deterministic")
        c2 = Claim.from_text(0, "deterministic")
        assert c1.sha256 == c2.sha256

    def test_different_texts_different_hashes(self):
        c1 = Claim.from_text(0, "alpha")
        c2 = Claim.from_text(0, "beta")
        assert c1.sha256 != c2.sha256

    def test_entropy_non_negative(self):
        c = Claim.from_text(0, "implement HMAC-linked provenance chain")
        assert c.entropy >= 0.0

    def test_frozen(self):
        c = Claim.from_text(0, "frozen test")
        with pytest.raises((AttributeError, TypeError)):
            c.index = 99  # type: ignore

    def test_to_dict_keys(self):
        c = Claim.from_text(1, "some claim")
        d = c.to_dict()
        assert set(d.keys()) == {"index", "text", "sha256", "entropy"}

    def test_to_dict_values(self):
        c = Claim.from_text(2, "another claim")
        d = c.to_dict()
        assert d["index"] == 2
        assert d["text"] == "another claim"
        assert d["sha256"] == c.sha256
        assert d["entropy"] == c.entropy


# ===========================================================================
# ClaimGraph
# ===========================================================================


class TestClaimGraph:
    """Invariant X5 — PSVP: ClaimGraph hash determinism and entropy aggregation.

    Enforces: graph_hash is a deterministic SHA-256 over all claim hashes in order
    (order-sensitive); mean_entropy is the arithmetic mean of per-claim entropies;
    to_dict contains all required structural keys.
    """

    def _make_graph(self, texts):
        claims = [Claim.from_text(i, t) for i, t in enumerate(texts)]
        return ClaimGraph(claims=claims)

    def test_mean_entropy_empty_is_zero(self):
        g = ClaimGraph(claims=[])
        assert g.mean_entropy == 0.0

    def test_mean_entropy_single_claim(self):
        c = Claim.from_text(0, "enforce runtime invariants via HMAC receipts")
        g = ClaimGraph(claims=[c])
        assert g.mean_entropy == c.entropy

    def test_mean_entropy_average_of_claims(self):
        g = self._make_graph(["one two three four", "five six seven eight"])
        expected = sum(c.entropy for c in g.claims) / 2
        assert abs(g.mean_entropy - expected) < 1e-12

    def test_graph_hash_is_64_hex(self):
        g = self._make_graph(["claim one", "claim two"])
        assert len(g.graph_hash) == 64

    def test_graph_hash_deterministic(self):
        texts = ["alpha claim", "beta claim"]
        g1 = self._make_graph(texts)
        g2 = self._make_graph(texts)
        assert g1.graph_hash == g2.graph_hash

    def test_graph_hash_changes_with_content(self):
        g1 = self._make_graph(["claim A"])
        g2 = self._make_graph(["claim B"])
        assert g1.graph_hash != g2.graph_hash

    def test_graph_hash_order_sensitive(self):
        g1 = self._make_graph(["first", "second"])
        g2 = self._make_graph(["second", "first"])
        assert g1.graph_hash != g2.graph_hash

    def test_to_dict_structure(self):
        g = self._make_graph(["one two three"])
        d = g.to_dict()
        assert "claims" in d
        assert "dependencies" in d
        assert "timestamp" in d
        assert "mean_entropy" in d
        assert "graph_hash" in d

    def test_to_dict_claim_count(self):
        g = self._make_graph(["a b c", "d e f", "g h i"])
        assert len(g.to_dict()["claims"]) == 3


# ===========================================================================
# SpecArtifact
# ===========================================================================


class TestSpecArtifact:
    """Invariant X5 — PSVP: SpecArtifact version chaining and immutability.

    Enforces: spec_id is a deterministic 64-char hex; predecessor_id is None for
    the genesis artifact; successor artifacts link to predecessor_id (tamper-evident
    chain); SpecArtifact is frozen after construction.
    """

    def _make_artifact(self, version=1, predecessor=None, ts=1000.0):
        from psvp import _compute_spec_id
        g_hash = "a" * 64
        entropy = 2.5
        sid = _compute_spec_id(version, g_hash, entropy, predecessor, ts)
        return SpecArtifact(
            spec_id        = sid,
            version        = version,
            graph_hash     = g_hash,
            mean_entropy   = entropy,
            predecessor_id = predecessor,
            timestamp      = ts,
        )

    def test_spec_id_is_64_hex(self):
        a = self._make_artifact()
        assert len(a.spec_id) == 64

    def test_version_stored(self):
        a = self._make_artifact(version=7)
        assert a.version == 7

    def test_predecessor_none_for_genesis(self):
        a = self._make_artifact(predecessor=None)
        assert a.predecessor_id is None

    def test_predecessor_set_for_successor(self):
        a1 = self._make_artifact(version=1)
        a2 = self._make_artifact(version=2, predecessor=a1.spec_id)
        assert a2.predecessor_id == a1.spec_id

    def test_to_dict_keys(self):
        a = self._make_artifact()
        d = a.to_dict()
        assert set(d.keys()) == {
            "spec_id", "version", "graph_hash", "mean_entropy",
            "predecessor_id", "timestamp",
        }

    def test_frozen(self):
        a = self._make_artifact()
        with pytest.raises((AttributeError, TypeError)):
            a.version = 99  # type: ignore


# ===========================================================================
# DriftGateError
# ===========================================================================


class TestDriftGateError:
    """Invariant X5 — PSVP: DriftGateError exception contract.

    Enforces: DriftGateError stores reason, entropy, and threshold; is a subtype
    of Exception; reason distinguishes "low_density" from "drift_spike".
    """

    def test_reason_stored(self):
        e = DriftGateError("low_density", 0.1, 0.5)
        assert e.reason == "low_density"

    def test_entropy_stored(self):
        e = DriftGateError("drift_spike", 5.0, 2.0)
        assert e.entropy == 5.0

    def test_threshold_stored(self):
        e = DriftGateError("low_density", 0.3, 0.5)
        assert e.threshold == 0.5

    def test_is_exception(self):
        assert isinstance(DriftGateError("low_density", 0.0, 0.5), Exception)


# ===========================================================================
# PSVP.decompose
# ===========================================================================


class TestPSVPDecompose:
    """Invariant X5 — PSVP: PSVP.decompose sentence decomposition.

    Enforces: each sentence becomes one Claim with a linear dependency chain;
    empty segments are skipped; claims are indexed from zero.
    """

    def test_single_sentence_produces_one_claim(self):
        psvp = PSVP()
        g = psvp.decompose("Implement HMAC-linked provenance chain")
        assert len(g.claims) == 1

    def test_multiple_sentences_produce_multiple_claims(self):
        psvp = PSVP()
        g = psvp.decompose("First sentence. Second sentence. Third sentence.")
        assert len(g.claims) == 3

    def test_claims_have_linear_dependencies(self):
        psvp = PSVP()
        g = psvp.decompose("One sentence. Two words. Three items.")
        assert g.dependencies[1] == [0]
        assert g.dependencies[2] == [1]

    def test_first_claim_has_no_dependency(self):
        psvp = PSVP()
        g = psvp.decompose("First. Second.")
        assert 0 not in g.dependencies

    def test_claims_indexed_from_zero(self):
        psvp = PSVP()
        g = psvp.decompose("Alpha. Beta. Gamma.")
        assert [c.index for c in g.claims] == [0, 1, 2]

    def test_empty_segments_skipped(self):
        psvp = PSVP()
        g = psvp.decompose("First.. Second.")
        assert all(c.text.strip() for c in g.claims)

    def test_returns_claim_graph(self):
        psvp = PSVP()
        g = psvp.decompose("Some proposal.")
        assert isinstance(g, ClaimGraph)


# ===========================================================================
# PSVP density gate
# ===========================================================================


class TestPSVPDensityGate:
    """Invariant X5 — PSVP: density gate (low_density DriftGateError).

    Enforces: create_spec raises DriftGateError(reason="low_density") when
    mean_entropy < min_density; passes when entropy is sufficient;
    min_density=0.0 always passes; threshold in the error matches config.
    """

    def test_low_entropy_rejected(self):
        psvp = PSVP(min_density=5.0)
        g = psvp.decompose("a")
        with pytest.raises(DriftGateError) as exc_info:
            psvp.create_spec(g, timestamp=1000.0)
        assert exc_info.value.reason == "low_density"

    def test_sufficient_entropy_passes(self):
        psvp = PSVP(min_density=0.1)
        g = psvp.decompose(
            "Implement wake chain with HMAC receipts for provenance tracking"
        )
        artifact = psvp.create_spec(g, timestamp=1000.0)
        assert artifact.version == 1

    def test_zero_min_density_always_passes(self):
        psvp = PSVP(min_density=0.0)
        g = psvp.decompose("x")
        artifact = psvp.create_spec(g, timestamp=1000.0)
        assert artifact is not None

    def test_density_error_threshold_matches_config(self):
        threshold = 3.0
        psvp = PSVP(min_density=threshold)
        g = psvp.decompose("a a a")
        with pytest.raises(DriftGateError) as exc_info:
            psvp.create_spec(g, timestamp=1000.0)
        assert exc_info.value.threshold == threshold


# ===========================================================================
# PSVP drift gate
# ===========================================================================


class TestPSVPDriftGate:
    """Invariant X5 — PSVP: drift gate (drift_spike DriftGateError).

    Enforces: a large entropy jump relative to the previous spec raises
    DriftGateError(reason="drift_spike"); the first spec never triggers drift;
    drift_ceiling=None disables the gate entirely.
    """

    def _rich_proposal(self):
        return (
            "Enforce deterministic invariants via cryptographic receipts "
            "using Shannon entropy and payload density thresholds"
        )

    def test_first_spec_no_drift_check(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=0.001)
        g = psvp.decompose(self._rich_proposal())
        artifact = psvp.create_spec(g, timestamp=1000.0)
        assert artifact.version == 1

    def test_drift_disabled_always_passes(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        for i in range(5):
            g = psvp.decompose(self._rich_proposal())
            psvp.create_spec(g, timestamp=float(i + 1))

    def test_large_entropy_jump_triggers_drift_gate(self):
        psvp = PSVP(min_density=0.0, drift_ceiling=0.001)
        g1 = psvp.decompose(self._rich_proposal())
        psvp.create_spec(g1, timestamp=1000.0)

        g2 = ClaimGraph(
            claims=[Claim.from_text(0, "a b c d e f g h i j k l m n o p q r s t")],
        )
        with pytest.raises(DriftGateError) as exc_info:
            psvp.create_spec(g2, timestamp=1001.0)
        assert exc_info.value.reason == "drift_spike"

    def test_drift_error_threshold_matches_config(self):
        ceiling = 0.001
        psvp = PSVP(min_density=0.0, drift_ceiling=ceiling)
        g1 = psvp.decompose("a b c d e f")
        psvp.create_spec(g1, timestamp=1000.0)

        g2 = ClaimGraph(
            claims=[Claim.from_text(0, "x y z w v u t s r q p o n m l k j i h g")],
        )
        try:
            psvp.create_spec(g2, timestamp=1001.0)
        except DriftGateError as e:
            assert e.threshold == ceiling


# ===========================================================================
# PSVP versioning and chaining
# ===========================================================================


class TestPSVPVersioning:
    """Invariant X5 — PSVP: spec version chaining and tamper-evident history.

    Enforces: version increments monotonically; genesis spec has no predecessor_id;
    each successor links predecessor_id to the previous spec_id; spec_ids are unique;
    history.length equals the number of specs created.
    """

    def _rich(self):
        return (
            "Enforce cryptographic provenance receipts using HMAC "
            "linked wake chain for deterministic state transitions"
        )

    def test_version_increments(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        for i in range(1, 4):
            g = psvp.decompose(self._rich())
            a = psvp.create_spec(g, timestamp=float(i * 1000))
            assert a.version == i

    def test_genesis_has_no_predecessor(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        g = psvp.decompose(self._rich())
        a = psvp.create_spec(g, timestamp=1000.0)
        assert a.predecessor_id is None

    def test_successor_links_to_predecessor(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        g = psvp.decompose(self._rich())
        a1 = psvp.create_spec(g, timestamp=1000.0)
        a2 = psvp.create_spec(g, timestamp=2000.0)
        assert a2.predecessor_id == a1.spec_id

    def test_spec_ids_are_unique(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        spec_ids = set()
        for i in range(5):
            g = psvp.decompose(self._rich())
            a = psvp.create_spec(g, timestamp=float(i * 1000 + 1))
            spec_ids.add(a.spec_id)
        assert len(spec_ids) == 5

    def test_history_grows_with_each_spec(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        g = psvp.decompose(self._rich())
        for i in range(3):
            psvp.create_spec(g, timestamp=float(i * 1000 + 1))
        assert len(psvp.history) == 3

    def test_version_property_reflects_count(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        assert psvp.version == 0
        g = psvp.decompose(self._rich())
        psvp.create_spec(g, timestamp=1000.0)
        assert psvp.version == 1

    def test_graph_hash_in_artifact(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        g = psvp.decompose(self._rich())
        a = psvp.create_spec(g, timestamp=1000.0)
        assert a.graph_hash == g.graph_hash


# ===========================================================================
# Integration
# ===========================================================================


class TestPSVPIntegration:
    """Integration: PSVP full pipeline — decompose → density gate → create_spec.

    Enforces: a rich proposal passes density and drift gates and produces a valid
    SpecArtifact; three-spec chain is consistently linked (predecessor_id chain).
    """

    def test_full_pipeline_produces_valid_artifact(self):
        psvp = PSVP(min_density=0.5, drift_ceiling=None)
        proposal = (
            "The system must enforce cryptographic provenance receipts. "
            "Each receipt is linked via HMAC to its predecessor. "
            "Payload density must exceed the minimum Shannon entropy threshold."
        )
        graph    = psvp.decompose(proposal)
        artifact = psvp.create_spec(graph, timestamp=1000.0)

        assert artifact.version == 1
        assert len(artifact.spec_id) == 64
        assert artifact.graph_hash == graph.graph_hash
        assert artifact.predecessor_id is None

    def test_three_spec_chain_is_consistent(self):
        psvp = PSVP(min_density=0.1, drift_ceiling=None)
        proposals = [
            "Implement HMAC linked wake chain for authenticated computation",
            "Enforce capability boundaries using object capability security model",
            "Validate payload density with Shannon entropy drift gate mechanism",
        ]
        artifacts = []
        for i, p in enumerate(proposals):
            g = psvp.decompose(p)
            a = psvp.create_spec(g, timestamp=float(1000 * (i + 1)))
            artifacts.append(a)

        assert artifacts[0].predecessor_id is None
        assert artifacts[1].predecessor_id == artifacts[0].spec_id
        assert artifacts[2].predecessor_id == artifacts[1].spec_id

    def test_rejected_proposal_does_not_advance_version(self):
        psvp = PSVP(min_density=5.0)
        g = psvp.decompose("x")
        with pytest.raises(DriftGateError):
            psvp.create_spec(g, timestamp=1000.0)
        assert psvp.version == 0
        assert len(psvp.history) == 0
