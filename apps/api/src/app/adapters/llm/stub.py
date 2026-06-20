"""Deterministic stub advisor (no network).

Owner: Zhou (backend)
Feature ID: F16 (LLM advisor)

Default in dev so the pipe runs offline. Implements AdvisorLLM.
"""

from __future__ import annotations

from typing import Any


class StubAdvisor:
    """Deterministic AdvisorLLM implementation — no external calls."""

    def explain(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return canned, deterministic copy. TODO F16."""
        raise NotImplementedError("TODO F16: StubAdvisor.explain")
