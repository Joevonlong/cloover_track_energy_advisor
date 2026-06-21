"""Site check — address / roof feasibility.

Owner: Zhou (backend)
Feature ID: F15 (site check)
"""

from __future__ import annotations

from typing import Any


class SiteCheck:
    """Validate a site for installation feasibility."""

    def run(self, address: str) -> dict[str, Any]:
        """Return a feasibility report for an address. TODO F15."""
        raise NotImplementedError("TODO F15: SiteCheck.run")
