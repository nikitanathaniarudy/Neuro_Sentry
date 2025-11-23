# """Gemini client wrapper returning the triage JSON contract.
# No fallback: always call Gemini and raise on any failure.
# """

# from __future__ import annotations

# import asyncio
# import json
# import os
# from pathlib import Path
# from typing import Dict, List

# from dotenv import load_dotenv

# from google import genai
# from google.genai import types as genai_types

# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(dotenv_path=BASE_DIR / ".env")


# async def call_gemini_report(
#     stats: Dict[str, object],
#     sample_packets: List[Dict[str, object]],
# ) -> Dict[str, object]:
#     """Always calls Gemini. Raises if anything goes wrong."""
#     # CORRECTED: Load from environment variable instead of hardcoding
#     api_key = os.environ.get("GEMINI_API_KEY")

#     if not api_key:
#         raise RuntimeError("GEMINI_API_KEY / GOOGLE_API_KEY not set.")

#     report_schema = {
#         "type": "object",
#         "properties": {
#             "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
#             "stroke_probability": {"type": "number"},
#             "summary": {"type": "string"},
#             "recommendation": {"type": "string"},
#             "confidence": {"type": "number"},
#             "bell_palsy_probability": {"type": "number"},
#         },
#         "required": [
#             "risk_level",
#             "stroke_probability",
#             "summary",
#             "recommendation",
#             "confidence",
#         ],
#     }

#     def _invoke() -> Dict[str, object]:
#         prompt_text = (
#             "You are Neuro-Sentry, an AI Triage system for Ischemic Stroke. "
#             "Given vitals + facial asymmetry stats and a small sample of raw Presage packets, "
#             "return ONLY a valid JSON triage report that matches the schema."
#         )

#         client = genai.Client(api_key=api_key)

#         response = client.models.generate_content(
#             model="gemini-2.0-flash-lite",
#             contents=[
#                 {
#                     "role": "user",
#                     "parts": [{"text": prompt_text}],  # CORRECTED: Wrap string in dict
#                 },
#                 {
#                     "role": "user",
#                     "parts": [{"text": f"Stats: {json.dumps(stats)}"}],  # CORRECTED
#                 },
#                 {
#                     "role": "user",
#                     "parts": [
#                         {"text": f"Raw packets sample: {json.dumps(sample_packets[:8])}"}
#                     ],  # CORRECTED
#                 },
#             ],
#             config=genai_types.GenerateContentConfig(
#                 response_mime_type="application/json",
#                 response_schema=report_schema,  # CORRECTED: Pass dict directly
#             ),
#         )

#         if not getattr(response, "text", None):
#             raise RuntimeError("Gemini returned empty response text.")

#         return json.loads(response.text)

#     # Let exceptions propagate (no fallback)
#     return await asyncio.to_thread(_invoke)

"""Gemini client wrapper returning the triage JSON contract.
No fallback: always call Gemini and raise on any failure.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


async def call_gemini_report(
    stats: Dict[str, object],
    sample_packets: List[Dict[str, object]],
) -> Dict[str, object]:
    """Always calls Gemini. Raises if anything goes wrong."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment.")

    # 1. Define the Strict Schema (The Interface for your Frontend)
    report_schema = {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
            "stroke_probability": {"type": "number"},
            "summary": {"type": "string"},
            "rationale": {"type": "string"}, # Added: Short medical explanation
            "recommendation": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": [
            "risk_level",
            "stroke_probability",
            "summary",
            "rationale",
            "recommendation",
            "confidence",
        ],
    }

    def _invoke() -> Dict[str, object]:
        # 2. The Medical Context (CRITICAL: Don't let the LLM guess)
        prompt_text = (
            "You are Neuro-Sentry, a specialized Triage system for Facial Palsy."
            "\n\nYOUR TASK:"
            "Analyze the provided biometric stats to differentiate between Central (Stroke) "
            "\n\nDIAGNOSTIC RUBRIC:"
            "\n1. ISCHEMIC STROKE (Central Lesion):"
            "\n   - High Mouth Asymmetry (> 1.5)"
            "\n   - LOW Forehead/Brow Asymmetry (Forehead is SPARED due to bilateral innervation)."
            "\n   - High Mouth Asymmetry"
            "\n   - HIGH Forehead/Brow Asymmetry (Entire half of face paralyzed)."
            "\n3. PANIC/DISTRESS:"
            "\n   - High Heart Rate (> 100) but normal facial symmetry."
            "\n\nReturn ONLY a valid JSON object matching the schema."
        )

        client = genai.Client(api_key=api_key)

        # 3. The Context Injection
        # We pass the calculated stats (Physics) and a sample of raw packets (Evidence)
        response = client.models.generate_content(
            model="gemini-2.5-flash", # Use 1.5 Flash for speed/reliability
            contents=[
                {"role": "user", "parts": [{"text": prompt_text}]},
                {"role": "user", "parts": [{"text": f"Computed Biometric Stats: {json.dumps(stats)}? "}]},
                {"role": "user", "parts": [{"text": f"Raw Telemetry Sample (First 8 packets): {json.dumps(sample_packets[:8])}"}]},
            ],
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=report_schema,
            ),
        )

        if not getattr(response, "text", None):
            raise RuntimeError("Gemini returned empty response text.")

        return json.loads(response.text)

    # Let exceptions propagate (No fallback, as requested)
    return await asyncio.to_thread(_invoke)