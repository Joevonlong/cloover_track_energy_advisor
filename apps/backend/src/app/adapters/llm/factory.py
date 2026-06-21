"""Advisor LLM factory.

Owner: Zhou (backend)
Feature ID: F16 (LLM advisor)

Selection policy (TODO F16):
  - Claude (Anthropic) is the default live backend; model "claude-opus-4-8".
  - OpenAI is the fallback when only OPENAI_API_KEY is configured.
  - StubAdvisor is used in dev (app_env == "dev") so the pipe runs offline.
All keys come from settings (this app's env) — never the frontend.
"""

from __future__ import annotations

from app.adapters.llm.base import AdvisorLLM
from app.adapters.llm.stub import StubAdvisor
from app.core.config import Settings


def make_advisor(settings: Settings) -> AdvisorLLM:
    """Pick an AdvisorLLM implementation from settings. TODO F16."""
    # TODO F16: branch on settings (Claude default -> OpenAI fallback -> stub).
    return StubAdvisor()
