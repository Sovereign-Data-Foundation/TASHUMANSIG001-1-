"""
tas_pythonetics — TAS connector and adapter layer.

Provides deterministic admission boundaries for external workspace integrations.
"""

from .replit_connector import (
    ConnectorReceipt,
    ReplitConnector,
    canonical_manifest_hash,
    character_shannon_entropy,
    structural_density,
)

__all__ = [
    "ConnectorReceipt",
    "ReplitConnector",
    "canonical_manifest_hash",
    "character_shannon_entropy",
    "structural_density",
]
