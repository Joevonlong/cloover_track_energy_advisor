"""Claude (Anthropic) advisor backend (F16).

Owner: Zhou (backend)
Feature ID: F16 (LLM advisor)

Uses the Anthropic Messages API via httpx (no anthropic SDK dependency needed).
Number-assertion guard is applied by the caller (RecommendationService).
Model: claude-opus-4-8 (§16 D8).

IMPORTANT: This provider is only instantiated when ANTHROPIC_API_KEY is set.
The key must never appear in any client-side payload (§11).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.adapters.llm.base import assert_numbers_grounded
from app.adapters.llm.stub import StubAdvisor

logger = logging.getLogger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_MAX_RETRIES = 2


class ClaudeAdvisor:
    """AdvisorLLM backed by Claude (Anthropic Messages API).

    Falls back to the templated StubAdvisor copy on guard failure after
    bounded retries, so the pipeline never ships an unverified figure (AC4).
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-8") -> None:
        self._api_key = api_key
        self._model = model

    def explain(self, payload: dict[str, Any], locale: str = "de") -> dict[str, Any]:
        """Call Claude to generate prose in the requested locale; apply number-assertion guard."""
        prompt = _build_prompt(payload, locale)
        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw = self._call_claude(prompt)
                parsed = _parse_response(raw)
                all_text = " ".join(parsed.values())
                if assert_numbers_grounded(all_text, payload):
                    return parsed
                logger.warning("Guard failed on attempt %d — retrying", attempt + 1)
            except Exception:
                logger.warning("Claude call failed on attempt %d", attempt + 1, exc_info=True)

        # Retries exhausted — fall back to deterministic templated copy (AC4)
        logger.error(
            "Claude guard failed after %d retries; using templated fallback",
            _MAX_RETRIES + 1,
        )
        return StubAdvisor().explain(payload, locale)

    def _call_claude(self, prompt: str) -> str:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                _ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                content=json.dumps(
                    {
                        "model": self._model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            )
            resp.raise_for_status()
            data = resp.json()
            return str(data["content"][0]["text"])


def _build_prompt(payload: dict[str, Any], locale: str = "en") -> str:
    best = payload.get("best", {})
    monthly_saving = best.get("monthly_saving_eur", 0)
    saving_after_payoff = best.get("saving_after_payoff_eur", 0)
    installment = best.get("installment_eur_month", 0)
    current_spend = payload.get("current_monthly_spend_eur", 0)

    context = payload.get("household_context") or {}
    tiers = payload.get("tiers") or []
    tier_lines = "\n".join(
        f"- {t.get('id')}: {t.get('name')} ({t.get('label')})" for t in tiers
    )

    if locale == "en":
        context_block = ""
        if context:
            lines = "\n".join(f"- {v}" for v in context.values())
            context_block = (
                "\nThis specific household's situation — reason about WHY this upgrade "
                "fits them (e.g. an ageing heat pump worth replacing for the subsidy). "
                "Refer to it qualitatively; do NOT introduce any new € amounts:\n"
                f"{lines}\n"
            )
        tier_block = ""
        tier_json = ""
        if tier_lines:
            tier_block = (
                "\nThree packaged offer cards are shown below. Write a one-sentence rationale "
                "for each — what it includes and who it suits. The cards already display every "
                "€ figure, so write NO € amounts in these three:\n"
                f"{tier_lines}\n"
            )
            tier_json = (
                ',\n  "tier_rationale_low": "<one sentence, NO € amounts>",'
                '\n  "tier_rationale_middle": "<one sentence, NO € amounts>",'
                '\n  "tier_rationale_high": "<one sentence, NO € amounts>"'
            )
        return f"""You are an energy advisor for the Heimwende platform. Write prose in English.
IMPORTANT: Do NOT calculate any numbers yourself. Use ONLY the following values from the payload:
- Current monthly spend: €{current_spend:.0f}/month
- Monthly saving (from day one): €{monthly_saving:.0f}/month
- Monthly saving (after financing ends): €{saving_after_payoff:.0f}/month
- Monthly installment: €{installment:.0f}/month
{context_block}{tier_block}
Return JSON with exactly these keys:
{{
  "explanation_md": "<3 sentences linking the saving to this household; only € numbers above>",
  "upsell_reason_md": "<1-2 sentence upgrade recommendation in English>",
  "proposal_copy_md": "<Markdown proposal copy in English for the installer>"{tier_json}
}}

Use EXCLUSIVELY the provided numeric values. Do not invent new numbers."""

    context_block = ""
    if context:
        lines = "\n".join(f"- {v}" for v in context.values())
        context_block = (
            "\nSituation dieses Haushalts — begründe, WARUM dieses Upgrade passt "
            "(z. B. eine alte Wärmepumpe, deren Austausch sich wegen der Förderung lohnt). "
            "Beziehe dich qualitativ darauf; führe KEINE neuen €-Beträge ein:\n"
            f"{lines}\n"
        )
    tier_block = ""
    tier_json = ""
    if tier_lines:
        tier_block = (
            "\nUnten stehen drei Angebotskarten. Schreibe für jede einen Ein-Satz-Grund — was "
            "sie enthält und für wen sie passt. Die Karten zeigen bereits alle €-Beträge, "
            "schreibe daher KEINE €-Beträge in diese drei:\n"
            f"{tier_lines}\n"
        )
        tier_json = (
            ',\n  "tier_rationale_low": "<ein Satz, KEINE €-Beträge>",'
            '\n  "tier_rationale_middle": "<ein Satz, KEINE €-Beträge>",'
            '\n  "tier_rationale_high": "<ein Satz, KEINE €-Beträge>"'
        )
    return f"""Du bist ein Energieberater der Heimwende-Plattform. Schreibe Prosa auf Deutsch.
WICHTIG: Berechne KEINE Zahlen selbst. Verwende NUR die folgenden Werte aus dem Payload:
- Aktuelle Kosten: €{current_spend:.0f}/mo
- Monatliche Einsparung (ab Tag 1): €{monthly_saving:.0f}/mo
- Monatliche Einsparung (nach Kreditende): €{saving_after_payoff:.0f}/mo
- Monatliche Rate: €{installment:.0f}/mo
{context_block}{tier_block}
Gib JSON mit genau diesen Schlüsseln zurück:
{{
  "explanation_md": "<3 Sätze: Einsparung mit Haushaltssituation verknüpfen; nur €-Zahlen oben>",
  "upsell_reason_md": "<1-2 Sätze Upgrade-Empfehlung>",
  "proposal_copy_md": "<Markdown Angebotstext für den Installer>"{tier_json}
}}

Verwende AUSSCHLIESSLICH die angegebenen Zahlenwerte. Erfinde keine neuen Zahlen."""


def _parse_response(raw: str) -> dict[str, Any]:
    """Extract the JSON object from the Claude response."""
    import re

    match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
    if match:
        return dict(json.loads(match.group()))
    raise ValueError(f"Could not parse JSON from Claude response: {raw[:200]}")


# ---------------------------------------------------------------------------
# Narrative report generation
# ---------------------------------------------------------------------------


def generate_report_sections(
    rec_dict: dict[str, Any],
    api_key: str,
    address: str | None = None,
    model: str = "claude-opus-4-8",
) -> list[dict[str, str]]:
    """Call Claude to write a 6-section advisory report from a Recommendation dict.

    Returns a list of {heading, body} dicts. Falls back to deterministic stub
    text on failure so the PDF download never crashes.
    """
    try:
        prompt = _build_report_prompt(rec_dict, address)
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                _ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                content=json.dumps(
                    {
                        "model": model,
                        "max_tokens": 2000,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            )
            resp.raise_for_status()
            raw = str(resp.json()["content"][0]["text"])
        sections = _parse_report_sections(raw, rec_dict)
        if sections:
            return sections
    except Exception:
        logger.warning("generate_report_sections failed — using stub", exc_info=True)

    from app.adapters.llm.stub import generate_report_sections_stub
    return generate_report_sections_stub(rec_dict, address)


def _build_report_prompt(rec_dict: dict[str, Any], address: str | None) -> str:
    best = rec_dict.get("best", {})
    capex = best.get("capex", {})
    conf = best.get("confidence", {})
    current_spend = rec_dict.get("current_monthly_spend_eur", 0)
    saving_now = best.get("monthly_saving_eur", 0)
    saving_after = best.get("saving_after_payoff_eur", 0)
    installment = best.get("installment_eur_month", 0)
    gross = capex.get("gross_eur", 0)
    subsidy = capex.get("subsidy_eur", 0)
    net_inv = capex.get("after_subsidy_eur", 0)
    subsidy_note = capex.get("subsidy_note", "")
    break_even = best.get("break_even_month", 0)
    conf_low = conf.get("low_eur", 0)
    conf_high = conf.get("high_eur", 0)
    driver = conf.get("biggest_driver", "")

    tiers = rec_dict.get("tiers", [])
    tier_lines = []
    for t in tiers:
        tier_lines.append(
            f"- {t.get('name','')}: saves €{t.get('monthly_saving_eur',0):.0f}/mo now,"
            f" €{t.get('saving_after_payoff_eur',0):.0f}/mo after payoff"
            f" (financing €{t.get('installment_eur_month',0):.0f}/mo,"
            f" net investment €{t.get('capex_after_subsidy_eur',0):.0f})"
        )
    tier_block = "\n".join(tier_lines)

    assumptions = rec_dict.get("assumptions", [])
    key_fields = {
        "roof_area_usable_m2", "pv_system_kwp", "panel_count", "roof_orientation",
        "specific_yield_kwh_per_kwp", "heat_pump_cop", "denkmal_listed",
        "mastr_neighbour_count", "kfw_subsidy_rate", "climate_zone",
    }
    assumption_lines = [
        f"- {a.get('field','')}: {a.get('value','')} ({a.get('source','')})"
        for a in assumptions if a.get("field","") in key_fields
    ]
    assumption_block = "\n".join(assumption_lines) if assumption_lines else "(none)"

    address_line = f"Property address: {address}" if address else ""

    return f"""You are Heimwende, a professional home-energy advisor. Write a formal advisory report in English.
{address_line}

AUTHORITATIVE NUMBERS — cite ONLY these € figures in the report (do not invent new ones):
- Current monthly energy spend: €{current_spend:.0f}/month
- Saving from day one (net of installment): €{saving_now:.0f}/month
- Saving after financing ends: €{saving_after:.0f}/month
- Monthly financing installment: €{installment:.0f}/month
- Total investment before subsidies: €{gross:.0f}
- Subsidies applied: €{subsidy:.0f} ({subsidy_note})
- Net investment after subsidies: €{net_inv:.0f}
- Break-even: month {break_even}
- Confidence range: €{conf_low:.0f}–€{conf_high:.0f}/month (biggest uncertainty: {driver})

THREE PACKAGES:
{tier_block}

KEY PROPERTY DATA (reference qualitatively — no new € amounts):
{assumption_block}

Write a JSON object with exactly 6 sections. Each section has a "heading" (string) and "body" (string, 3-4 fluent sentences, plain prose, no markdown symbols, no bullet points).

Sections must be:
1. "Executive Summary" — headline saving, what the upgrade means for this household
2. "Property and Solar Analysis" — roof data, PV sizing, annual yield potential
3. "German Permit and Regulation Status" — what checks passed, regulatory outlook
4. "Three Upgrade Packages" — compare the three tiers, who each suits, no new € amounts beyond the package figures above
5. "Subsidies and Financing" — KfW/VAT details, financing structure, net cost
6. "Our Recommendation and Next Steps" — which package, why, concrete action

Return ONLY valid JSON:
{{"sections": [{{"heading": "...", "body": "..."}}, ...]}}"""


def _parse_report_sections(raw: str, rec_dict: dict[str, Any]) -> list[dict[str, str]]:
    """Extract and validate the sections array from the Claude response."""
    import re
    from app.adapters.llm.base import assert_numbers_grounded

    # Try to find the JSON object (may be wrapped in ```json ... ```)
    match = re.search(r'\{.*"sections"\s*:\s*\[.*?\]\s*\}', raw, re.DOTALL)
    if not match:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return []

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    sections = data.get("sections", [])
    if not isinstance(sections, list) or not sections:
        return []

    # Validate all bodies pass the number guard
    all_text = " ".join(s.get("body", "") for s in sections)
    if not assert_numbers_grounded(all_text, rec_dict):
        logger.warning("Report number guard failed — falling back to stub")
        return []

    return [
        {"heading": str(s.get("heading", "")), "body": str(s.get("body", ""))}
        for s in sections
        if s.get("heading") and s.get("body")
    ]