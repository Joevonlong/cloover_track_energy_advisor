"""LLM advisor interface.

Owner: Zhou (backend)
Feature ID: F16 (LLM advisor)

Defines the contract every advisor backend implements. Keys live in this
app's env (never the frontend).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AdvisorLLM(Protocol):
    """Turns a computed recommendation payload into plain-language copy."""

    def explain(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a customer-facing explanation. TODO F16."""
        ...
