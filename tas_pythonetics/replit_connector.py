"""
tas_pythonetics.replit_connector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deterministic admission boundary for Replit-originated workspace actions.

The ReplitConnector never mutates a workspace directly. On admission it returns
an immutable ``ConnectorReceipt``. On refusal it raises a structured
``SovereignStructuralViolation`` whose message is a JSON receipt containing
the connector name, payload hash, manifest hash, structural density, refusal
reason, and UTC timestamp.

Refusals engage an **irreversible in-memory Sentient Lock**: once a single
structural violation is witnessed the connector instance can never admit another
payload.  Downstream systems may persist the refusal receipt and must not reuse
the locked connector.

Two independent gates must both pass for a payload to be admitted:

1. **Density gate** — ``structural_density(payload) >= min_density``
   Collapses repetitive, token-loop, or padding payloads before they reach
   the governance layer.

2. **Manifest integrity gate** — ``canonical_manifest_hash(manifest) == expected``
   Guarantees that the manifest has not been reordered or tampered with since
   the expected hash was produced.
"""

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from tas_logos_gatekeeper import SovereignStructuralViolation


_CONNECTOR_NAME = "ReplitConnector"
_DEFAULT_MIN_DENSITY = 0.15


# ---------------------------------------------------------------------------
# ConnectorReceipt — typed, immutable admission receipt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConnectorReceipt:
    """Immutable receipt returned by :meth:`ReplitConnector.verify` on admission.

    Fields
    ------
    connector:
        Name of the connector that produced this receipt.
    status:
        Always ``"ADMITTED"`` for receipts returned from ``verify()``.
    payload_hash:
        SHA-256 hex digest of the admitted payload.
    manifest_hash:
        Canonical SHA-256 hex digest of the admitted manifest.
    structural_density:
        Computed density of the admitted payload.
    timestamp:
        ISO-8601 UTC timestamp with ``Z`` suffix.
    """

    connector: str
    status: str
    payload_hash: str
    manifest_hash: str
    structural_density: float
    timestamp: str


# ---------------------------------------------------------------------------
# Module-level pure functions
# ---------------------------------------------------------------------------


def canonical_manifest_hash(manifest: Mapping[str, Any]) -> str:
    """Return the SHA-256 hex digest of a canonically serialized manifest.

    Serializes *manifest* with ``sort_keys=True`` and compact JSON separators
    ``(",", ":")`` so that key ordering is deterministic regardless of insertion
    order.  This prevents non-deterministic JSON ordering from producing
    divergent provenance roots across Python runtimes or dict implementations.

    Parameters
    ----------
    manifest:
        Arbitrary mapping representing the workspace action manifest.

    Returns
    -------
    str
        64-character lowercase hex SHA-256 digest.
    """
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def character_shannon_entropy(payload: str) -> float:
    """Compute character-level Shannon entropy of *payload* in bits per character.

    Parameters
    ----------
    payload:
        UTF-8 string whose entropy is to be measured.

    Returns
    -------
    float
        Shannon entropy H in bits/character.  Returns ``0.0`` for an empty
        or single-character payload.
    """
    if not payload:
        return 0.0
    counts: dict[str, int] = {}
    for ch in payload:
        counts[ch] = counts.get(ch, 0) + 1
    total = len(payload)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def structural_density(payload: str) -> float:
    """Compute the structural density of *payload*.

    Divides character-level Shannon entropy by the square root of the UTF-8
    byte footprint.  This preserves useful short instructions (high entropy
    relative to their size) while collapsing repetitive padding and token-loop
    payloads whose entropy is diluted by their length.

    .. math::

        D = \\frac{H(payload)}{\\sqrt{|payload|_{\\text{UTF-8 bytes}}}}

    Parameters
    ----------
    payload:
        UTF-8 string to evaluate.

    Returns
    -------
    float
        Structural density scalar.  Returns ``0.0`` for an empty payload.
    """
    if not payload:
        return 0.0
    byte_length = len(payload.encode("utf-8"))
    if byte_length == 0:
        return 0.0
    return character_shannon_entropy(payload) / math.sqrt(byte_length)


# ---------------------------------------------------------------------------
# ReplitConnector
# ---------------------------------------------------------------------------


class ReplitConnector:
    """Deterministic admission boundary for Replit-originated workspace actions.

    Once any structural violation is witnessed the instance engages an
    **irreversible Sentient Lock** — all subsequent calls to :meth:`verify`
    raise ``SovereignStructuralViolation`` with reason
    ``SENTIENT_LOCK_ENGAGED``, regardless of payload quality.

    Parameters
    ----------
    min_density:
        Minimum structural density required for admission.  Payloads below
        this floor are refused with ``DENSITY_BELOW_FLOOR``.
        Default ``0.15``.
    """

    NAME = _CONNECTOR_NAME

    def __init__(self, min_density: float = _DEFAULT_MIN_DENSITY) -> None:
        self.min_density = min_density
        self._locked: bool = False

    # ------------------------------------------------------------------
    # Module-level helpers re-exported as instance methods for convenience
    # ------------------------------------------------------------------

    @staticmethod
    def canonical_manifest_hash(manifest: Mapping[str, Any]) -> str:
        return canonical_manifest_hash(manifest)

    @staticmethod
    def character_shannon_entropy(payload: str) -> float:
        return character_shannon_entropy(payload)

    @staticmethod
    def structural_density(payload: str) -> float:
        return structural_density(payload)

    # ------------------------------------------------------------------
    # Public state
    # ------------------------------------------------------------------

    @property
    def is_locked(self) -> bool:
        """``True`` after any structural violation has been witnessed."""
        return self._locked

    # ------------------------------------------------------------------
    # Admission gate
    # ------------------------------------------------------------------

    def verify(
        self,
        payload: str,
        manifest: Mapping[str, Any],
        expected_manifest_hash: str,
    ) -> ConnectorReceipt:
        """Admit or refuse a Replit-originated workspace action.

        Both the density gate and the canonical manifest hash must pass for
        the action to be admitted.  Either failure engages the irreversible
        Sentient Lock and raises ``SovereignStructuralViolation``; the
        exception message is a JSON receipt.

        Once locked, all subsequent calls raise immediately with
        ``SENTIENT_LOCK_ENGAGED`` before evaluating any gates.

        Parameters
        ----------
        payload:
            The action payload string to density-check.
        manifest:
            The manifest dict whose canonical hash will be verified.
        expected_manifest_hash:
            The SHA-256 hex digest previously committed for this manifest.
            Must match ``canonical_manifest_hash(manifest)`` exactly.

        Returns
        -------
        ConnectorReceipt
            Immutable admission receipt on success.

        Raises
        ------
        SovereignStructuralViolation
            If the Sentient Lock is engaged, the density gate fails, or the
            manifest integrity gate fails.  The exception message is a JSON
            string containing the full refusal receipt.
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Fast-path: Sentient Lock check before any computation
        if self._locked:
            self._raise(
                payload_hash="0" * 64,
                manifest_hash="0" * 64,
                density=0.0,
                reason="SENTIENT_LOCK_ENGAGED",
                timestamp=timestamp,
            )

        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        actual_manifest_hash = canonical_manifest_hash(manifest)
        density = structural_density(payload)

        # Gate 1 — structural density
        if density < self.min_density:
            self._locked = True
            self._raise(
                payload_hash=payload_hash,
                manifest_hash=actual_manifest_hash,
                density=density,
                reason=f"DENSITY_BELOW_FLOOR: {density:.6f} < {self.min_density}",
                timestamp=timestamp,
            )

        # Gate 2 — manifest integrity
        if actual_manifest_hash != expected_manifest_hash:
            self._locked = True
            self._raise(
                payload_hash=payload_hash,
                manifest_hash=actual_manifest_hash,
                density=density,
                reason=(
                    f"MANIFEST_HASH_MISMATCH: got {actual_manifest_hash!r}, "
                    f"expected {expected_manifest_hash!r}"
                ),
                timestamp=timestamp,
            )

        return ConnectorReceipt(
            connector=self.NAME,
            status="ADMITTED",
            payload_hash=payload_hash,
            manifest_hash=actual_manifest_hash,
            structural_density=density,
            timestamp=timestamp,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _raise(
        self,
        payload_hash: str,
        manifest_hash: str,
        density: float,
        reason: str,
        timestamp: str,
    ) -> None:
        receipt = json.dumps(
            {
                "connector": self.NAME,
                "status": "REFUSED",
                "payload_hash": payload_hash,
                "manifest_hash": manifest_hash,
                "structural_density": density,
                "reason": reason,
                "timestamp": timestamp,
            },
            separators=(",", ":"),
        )
        raise SovereignStructuralViolation(receipt)
