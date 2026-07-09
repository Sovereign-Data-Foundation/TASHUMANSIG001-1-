"""Tests for invariant_query — machine-readable TAS invariant index (Task 3).

Verifies that the InvariantIndex correctly parses tests/invariants.md and
exposes a correct, queryable API for tools and CI pipelines.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
import json
import pathlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from invariant_query import InvariantIndex, InvariantRecord, main


_INDEX_PATH = pathlib.Path(__file__).parent / "invariants.md"

KNOWN_IDS = [
    "W1",
    "W2",
    "W3",
    "W4",
    "W5",
    "P0",
    "P1",
    "C1",
    "C2",
    "C3",
    "C4",
    "U1",
    "U2",
    "U3",
    "U4",
    "U5",
    "U6",
    "U7",
    "S1",
    "S2",
    "PH1",
    "PH2",
    "PH3",
    "G1",
    "G2",
    "G3",
    "G4",
    "X1",
    "X2",
    "X3",
    "X4",
    "X5",
    "X6",
    "X7",
    "X8",
]


# ===========================================================================
# TestInvariantIndexLoading
# ===========================================================================


class TestInvariantIndexLoading:
    """InvariantIndex parses invariants.md without errors and finds all known IDs."""

    def test_loads_without_error(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert len(idx) > 0

    def test_all_known_ids_present(self):
        idx = InvariantIndex(_INDEX_PATH)
        missing = [inv_id for inv_id in KNOWN_IDS if idx.get(inv_id) is None]
        assert not missing, f"Missing invariant IDs: {missing}"

    def test_total_count_matches_known(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert len(idx) >= len(KNOWN_IDS)

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            InvariantIndex(tmp_path / "nonexistent.md")


# ===========================================================================
# TestInvariantIndexGet
# ===========================================================================


class TestInvariantIndexGet:
    """InvariantIndex.get() returns correct records for known invariant IDs."""

    def test_get_w1(self):
        idx = InvariantIndex(_INDEX_PATH)
        r = idx.get("W1")
        assert r is not None
        assert r.id == "W1"
        assert r.layer == 3
        assert (
            "wake_chain" in r.source_module.lower() or "wake" in r.source_module.lower()
        )

    def test_get_case_insensitive(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert idx.get("w1") == idx.get("W1")
        assert idx.get("c2") == idx.get("C2")

    def test_get_unknown_returns_none(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert idx.get("Z99") is None

    def test_record_has_nonempty_formal_statement(self):
        idx = InvariantIndex(_INDEX_PATH)
        for inv_id in KNOWN_IDS:
            r = idx.get(inv_id)
            assert r is not None
            assert len(r.formal_statement) > 10, (
                f"{inv_id} has too-short formal statement"
            )

    def test_record_has_source_module(self):
        idx = InvariantIndex(_INDEX_PATH)
        for inv_id in KNOWN_IDS:
            r = idx.get(inv_id)
            assert r.source_module.strip(), f"{inv_id} has empty source_module"

    def test_record_has_test_classes(self):
        idx = InvariantIndex(_INDEX_PATH)
        for inv_id in ["W1", "C1", "U1", "G1", "S1"]:
            r = idx.get(inv_id)
            assert r.test_classes, f"{inv_id} has no test_classes"


# ===========================================================================
# TestInvariantIndexListAll
# ===========================================================================


class TestInvariantIndexListAll:
    """InvariantIndex.list_all() returns all invariants in layer order."""

    def test_list_all_returns_all(self):
        idx = InvariantIndex(_INDEX_PATH)
        all_records = idx.list_all()
        assert len(all_records) == len(idx)

    def test_list_all_ordered_by_layer(self):
        idx = InvariantIndex(_INDEX_PATH)
        records = idx.list_all()
        layers = [r.layer for r in records]
        assert layers == sorted(layers)

    def test_list_all_are_invariant_records(self):
        idx = InvariantIndex(_INDEX_PATH)
        for r in idx.list_all():
            assert isinstance(r, InvariantRecord)


# ===========================================================================
# TestInvariantIndexByLayer
# ===========================================================================


class TestInvariantIndexByLayer:
    """InvariantIndex.by_layer() filters correctly."""

    def test_layer_3_contains_wake_invariants(self):
        idx = InvariantIndex(_INDEX_PATH)
        layer3 = idx.by_layer(3)
        ids = {r.id for r in layer3}
        assert {"W1", "W2", "W3", "W4", "W5"}.issubset(ids)

    def test_layer_4_contains_capability_invariants(self):
        idx = InvariantIndex(_INDEX_PATH)
        layer4 = idx.by_layer(4)
        ids = {r.id for r in layer4}
        assert {"C1", "C2", "C3", "C4"}.issubset(ids)

    def test_layer_8_contains_genesis_invariants(self):
        idx = InvariantIndex(_INDEX_PATH)
        layer8 = idx.by_layer(8)
        ids = {r.id for r in layer8}
        assert {"G1", "G2", "G3", "G4"}.issubset(ids)

    def test_unknown_layer_returns_empty(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert idx.by_layer(42) == []


# ===========================================================================
# TestInvariantIndexSearch
# ===========================================================================


class TestInvariantIndexSearch:
    """InvariantIndex.search() finds invariants by keyword."""

    def test_search_hmac_finds_w1(self):
        idx = InvariantIndex(_INDEX_PATH)
        results = idx.search("HMAC")
        ids = {r.id for r in results}
        assert "W1" in ids

    def test_search_capability_finds_c_invariants(self):
        idx = InvariantIndex(_INDEX_PATH)
        results = idx.search("capability")
        ids = {r.id for r in results}
        assert ids.issuperset({"C1", "C2", "C3", "C4"})

    def test_search_case_insensitive(self):
        idx = InvariantIndex(_INDEX_PATH)
        r1 = idx.search("hmac")
        r2 = idx.search("HMAC")
        assert {r.id for r in r1} == {r.id for r in r2}

    def test_search_no_match_returns_empty(self):
        idx = InvariantIndex(_INDEX_PATH)
        assert idx.search("zzz_no_match_zzz") == []


# ===========================================================================
# TestInvariantIndexJSON
# ===========================================================================


class TestInvariantIndexJSON:
    """InvariantIndex.to_json() produces valid, complete JSON output."""

    def test_to_json_is_valid_json(self):
        idx = InvariantIndex(_INDEX_PATH)
        parsed = json.loads(idx.to_json())
        assert isinstance(parsed, list)

    def test_to_json_contains_all_invariants(self):
        idx = InvariantIndex(_INDEX_PATH)
        parsed = json.loads(idx.to_json())
        assert len(parsed) == len(idx)

    def test_to_json_record_has_required_fields(self):
        idx = InvariantIndex(_INDEX_PATH)
        parsed = json.loads(idx.to_json())
        required = {
            "id",
            "layer",
            "layer_name",
            "formal_statement",
            "source_module",
            "test_classes",
        }
        for record in parsed:
            missing = required - set(record.keys())
            assert not missing, f"Record {record.get('id')} missing fields: {missing}"


# ===========================================================================
# TestInvariantQueryCLI
# ===========================================================================


class TestInvariantQueryCLI:
    """invariant_query CLI returns correct exit codes and output."""

    def test_list_exits_zero(self, capsys):
        rc = main(["list"])
        assert rc == 0

    def test_show_known_id_exits_zero(self, capsys):
        rc = main(["show", "W1"])
        assert rc == 0

    def test_show_unknown_id_exits_one(self, capsys):
        rc = main(["show", "Z99"])
        assert rc == 1

    def test_search_exits_zero(self, capsys):
        rc = main(["search", "HMAC"])
        assert rc == 0

    def test_layer_exits_zero(self, capsys):
        rc = main(["layer", "3"])
        assert rc == 0

    def test_json_exits_zero(self, capsys):
        rc = main(["json"])
        assert rc == 0

    def test_json_output_is_parseable(self, capsys):
        main(["json"])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
