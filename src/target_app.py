"""
M2 — Thin client for the system under test (SUT).

Contract used by later metrics (M3+):
  target.complete(prompt: str) -> TargetResponse

Backends:
  - mock  : offline, no API key (default)
  - openai: OpenAI-compatible Chat Completions (OpenAI, xAI/Grok, Azure-compatible, etc.)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import requests
from dotenv import load_dotenv

load_dotenv()

# Software-testing assistant system prompt (shared by live backends)
SYSTEM_PROMPT = (
    "You are a concise software testing assistant for QA engineers and SDETs. "
    "Answer clearly and accurately. Prefer practical guidance over fluff. "
    "If unsure, say so. Do not invent product-specific facts."
)


@dataclass
class TargetResponse:
    """Normalized answer from the system under test."""

    answer: str
    latency_ms: float
    model: str
    backend: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int | None:
        if self.prompt_tokens is None and self.completion_tokens is None:
            return None
        return (self.prompt_tokens or 0) + (self.completion_tokens or 0)


class TargetApp(Protocol):
    """Interface for any SUT wrapper (LLM, RAG HTTP API, mock)."""

    name: str

    def complete(self, prompt: str) -> TargetResponse: ...


class MockTarget:
    """
    Offline target for local smoke tests without API keys.

    Returns a short, deterministic template answer so M2/M3 plumbing can run
    without spending tokens. Not used for real quality scores.
    """

    name = "mock"

    def complete(self, prompt: str) -> TargetResponse:
        t0 = time.perf_counter()
        # Tiny delay so latency_ms is non-zero and realistic for smoke runs
        time.sleep(0.01)
        text = (
            "[mock] This is a placeholder answer from MockTarget. "
            f"You asked ({len(prompt)} chars): {prompt[:160]}"
            f"{'…' if len(prompt) > 160 else ''}. "
            "Configure TARGET_BACKEND=openai and API keys for a real model."
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        return TargetResponse(
            answer=text,
            latency_ms=round(latency_ms, 2),
            model="mock-v1",
            backend=self.name,
            prompt_tokens=None,
            completion_tokens=None,
            raw={"mock": True},
        )


class OpenAICompatibleTarget:
    """
    Chat Completions client for OpenAI-compatible APIs.

    Env:
      OPENAI_API_KEY   (required) — or XAI_API_KEY as fallback for xAI
      OPENAI_BASE_URL  (optional) — default https://api.openai.com/v1
                                   xAI: https://api.x.ai/v1
      OPENAI_MODEL     (optional) — default gpt-4o-mini
    """

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("XAI_API_KEY")
            or ""
        )
        self.base_url = (
            base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout_s = timeout_s
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY (or XAI_API_KEY) is required for openai backend. "
                "Use TARGET_BACKEND=mock for offline smoke tests."
            )

    def complete(self, prompt: str) -> TargetResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        t0 = time.perf_counter()
        resp = requests.post(url, headers=headers, json=body, timeout=self.timeout_s)
        latency_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage") or {}
        return TargetResponse(
            answer=answer,
            latency_ms=round(latency_ms, 2),
            model=data.get("model") or self.model,
            backend=self.name,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            raw={"id": data.get("id"), "usage": usage},
        )


def get_target(backend: str | None = None) -> TargetApp:
    """
    Factory: TARGET_BACKEND=mock|openai (default mock).
    """
    choice = (backend or os.getenv("TARGET_BACKEND") or "mock").strip().lower()
    if choice in ("mock", "local"):
        return MockTarget()
    if choice in ("openai", "xai", "grok", "llm"):
        return OpenAICompatibleTarget()
    raise ValueError(
        f"Unknown TARGET_BACKEND={choice!r}. Use 'mock' or 'openai'."
    )


def ask(prompt: str, backend: str | None = None) -> TargetResponse:
    """Convenience: one-shot prompt → TargetResponse."""
    return get_target(backend).complete(prompt)


if __name__ == "__main__":
    import json
    import sys

    prompt = " ".join(sys.argv[1:]) or "What is a flaky test?"
    result = ask(prompt)
    print(
        json.dumps(
            {
                "backend": result.backend,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "answer": result.answer,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
