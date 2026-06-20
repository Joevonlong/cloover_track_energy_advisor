"""Recommendation orchestration service.

Owner: Zhou (backend)
Feature ID: F17 (api endpoints)

Wires the pipeline: resolver -> engine -> llm -> persist.
"""

from __future__ import annotations

from typing import Any


class RecommendationService:
    """Top-level use case behind POST /api/v1/advisor/recommend."""

    def run(self, household: Any, options: Any) -> Any:
        """Resolve context, run the engine, explain, persist. TODO F17."""
        raise NotImplementedError("TODO F17: RecommendationService.run")
