"""Gemini client wrapper that enforces the triage JSON contract."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover - runtime guard for missing SDK
    genai = None
    genai_types = None


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "triage_level": {"type": "integer", "minimum": 1, "maximum": 5},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale_short": {"type": "string"},
        "ui_directives": {
            "type": "object",
            "properties": {
                "alert_color": {"type": "string"},
                "highlight_regions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["alert_color", "highlight_regions"],
        },
    },
    "required": [
        "overall_risk",
        "triage_level",
        "confidence",
        "rationale_short",
        "ui_directives",
    ],
}


def _fallback_triage(presage_summary: Dict[str, object], audio_summary: Dict[str, object]) -> Dict[str, object]:
    hr = float(presage_summary.get("heart_rate") or 0.0)
    br = float(presage_summary.get("breathing_rate") or 0.0)
    quality = float(presage_summary.get("quality") or 0.0)
    energy = float(audio_summary.get("energy") or 0.0)
    jitter = float(audio_summary.get("jitter") or 0.0)

    # Deterministic heuristic: elevated vitals + noisy audio raises risk.
    raw_score = (hr * 0.003) + (br * 0.002) + (energy * 2.5) + (jitter * 5.0)
    scaled_risk = max(0.05, min(1.0, raw_score + (0.3 * (1 - quality))))
    triage_level = min(5, max(1, int(round(scaled_risk * 5))))

    highlight = [r.get("region") for r in presage_summary.get("top_regions", []) if r]
    alert_color = "#e53935" if triage_level >= 4 else "#f9a825" if triage_level == 3 else "#43a047"

    return {
        "overall_risk": float(round(scaled_risk, 3)),
        "triage_level": triage_level,
        "confidence": float(round(0.6 + (quality * 0.3), 3)),
        "rationale_short": "Heuristic fallback based on vitals and audio stability.",
        "ui_directives": {
            "alert_color": alert_color,
            "highlight_regions": highlight,
        },
    }


def _build_prompt(presage_summary: Dict[str, object], audio_summary: Dict[str, object]) -> List[object]:
    presage_json = json.dumps(presage_summary, ensure_ascii=True)
    audio_json = json.dumps(audio_summary, ensure_ascii=True)
    instructions = (
        "You are the triage brain for Neuro-Sentry. Respond ONLY with JSON matching the schema. "
        "Rate overall risk between 0 and 1 and triage_level 1-5. Keep rationale_short concise."
    )
    return [
        {"role": "user", "parts": [instructions]},
        {"role": "user", "parts": [f"Presage summary: {presage_json}"]},
        {"role": "user", "parts": [f"Audio summary: {audio_json}"]},
    ]


def _normalize_output(raw: Dict[str, object]) -> Dict[str, object]:
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        data = {}

    base = {
        "overall_risk": float(data.get("overall_risk", 0.0)),
        "triage_level": int(data.get("triage_level", 1)),
        "confidence": float(data.get("confidence", 0.5)),
        "rationale_short": str(data.get("rationale_short", "Generated fallback")),
        "ui_directives": data.get("ui_directives") or {},
    }

    directives = base["ui_directives"]
    if not isinstance(directives, dict):
        directives = {}
    directives.setdefault("alert_color", "#43a047")
    directives.setdefault("highlight_regions", [])
    base["ui_directives"] = directives
    return base


async def call_gemini_dummy(
    presage_summary: Dict[str, object], audio_summary: Dict[str, object]
) -> Dict[str, object]:
    """Call Gemini with structured schema; fallback to heuristic locally."""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or not genai or not genai_types:
        return _fallback_triage(presage_summary, audio_summary)

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(presage_summary, audio_summary)

    def _invoke() -> Dict[str, object]:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=genai_types.Schema.from_dict(TRIAGE_SCHEMA),
            ),
        )
        if hasattr(response, "text") and response.text:
            try:
                return json.loads(response.text)
            except Exception:
                return _fallback_triage(presage_summary, audio_summary)
        return _fallback_triage(presage_summary, audio_summary)

    try:
        result = await asyncio.to_thread(_invoke)
        return _normalize_output(result)
    except Exception:
        return _fallback_triage(presage_summary, audio_summary)


async def call_gemini_report(
    presage_summary: Dict[str, object], audio_summary: Dict[str, object]
) -> Dict[str, object]:
    """Final session report. Uses Gemini if available, otherwise deterministic."""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    # Reuse heuristics for fallback
    base_triage = _fallback_triage(presage_summary, audio_summary)
    fallback_report = {
        "risk_level": "HIGH" if base_triage["triage_level"] >= 4 else "MED" if base_triage["triage_level"] == 3 else "LOW",
        "summary": "Heuristic summary based on session vitals.",
        "recommendation": "Follow up if symptoms persist; ensure calm breathing and hydration.",
        "confidence": float(base_triage.get("confidence", 0.6)),
        "presage_snapshot": presage_summary,
    }
    if not api_key or not genai or not genai_types:
        return fallback_report

    client = genai.Client(api_key=api_key)

    def _invoke() -> Dict[str, object]:
        prompt = [
            {
                "role": "user",
                "parts": [
                    "You are the triage brain for Neuro-Sentry. Return JSON with keys risk_level (LOW/MED/HIGH), summary, recommendation, confidence (0-1)."
                ],
            },
            {"role": "user", "parts": [f"Session presage summary: {json.dumps(presage_summary, ensure_ascii=True)}"]},
            {"role": "user", "parts": [f"Audio summary: {json.dumps(audio_summary, ensure_ascii=True)}"]},
        ]
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=genai_types.Schema.from_dict(
                    {
                        "type": "object",
                        "properties": {
                            "risk_level": {"type": "string"},
                            "summary": {"type": "string"},
                            "recommendation": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["risk_level", "summary", "recommendation", "confidence"],
                    }
                ),
            ),
        )
        if hasattr(response, "text") and response.text:
            try:
                return json.loads(response.text)
            except Exception:
                return fallback_report
        return fallback_report

    try:
        result = await asyncio.to_thread(_invoke)
        merged = fallback_report.copy()
        merged.update(result or {})
        merged.setdefault("risk_level", fallback_report["risk_level"])
        merged.setdefault("recommendation", fallback_report["recommendation"])
        merged.setdefault("summary", fallback_report["summary"])
        merged.setdefault("confidence", fallback_report["confidence"])
        merged["presage_snapshot"] = presage_summary
        return merged
    except Exception:
        return fallback_report
