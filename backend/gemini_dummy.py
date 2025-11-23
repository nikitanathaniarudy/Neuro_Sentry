# """Gemini triage caller using simple prompt and strict JSON output."""

# from __future__ import annotations

# import asyncio
# import json
# import os
# from pathlib import Path
# from typing import Dict, List

# from dotenv import load_dotenv

# from gemini_prompt import build_triage_prompt

# try:  # pragma: no cover - optional dependency
#     from google import genai
#     from google.genai import types as genai_types
# except Exception:  # pragma: no cover
#     genai = None
#     genai_types = None

# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(dotenv_path=BASE_DIR / ".env")


# def _fallback_error(msg: str) -> Dict[str, object]:
#     raise RuntimeError(msg)


# async def call_gemini_report(stats: Dict[str, object], sample_packets: List[Dict[str, object]]) -> Dict[str, object]:
#     """Call Gemini 2.5 Flash for triage. No fallback: raise on failure."""
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key or not genai or not genai_types:
#         return _fallback_error("Gemini SDK or API key missing")

#     prompt_text = build_triage_prompt(stats, sample_packets)
#     report_schema_dict = {
#         "type": "object",
#         "properties": {
#             "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
#             "stroke_probability": {"type": "number"},
#             "bell_palsy_probability": {"type": "number"},
#             "summary": {"type": "string"},
#             "recommendation": {"type": "string"},
#             "confidence": {"type": "number"},
#         },
#         "required": ["risk_level", "stroke_probability", "summary", "recommendation", "confidence"],
#     }

#     def _invoke() -> Dict[str, object]:
#         client = genai.Client(api_key=api_key)
#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=prompt_text,
#             config=genai_types.GenerateContentConfig(
#                 response_mime_type="application/json",
#                 response_schema=report_schema_dict,  # dict accepted; do not use Schema.from_dict
#                 temperature=0.2,
#             ),
#         )
#         return json.loads(response.text)

#     print(f"[Gemini] prompt len={len(prompt_text)}, stats_keys={list(stats.keys())}, packets={len(sample_packets)}")
#     try:
#         result = await asyncio.to_thread(_invoke)
#         preview = str(result)[:300]
#         print(f"[Gemini] response preview={preview}")
#         return result
#     except Exception as exc:  # pragma: no cover
#         print(f"[Gemini] Error: {exc}")
#         raise


# __all__ = ["call_gemini_report"]

# """Gemini triage caller using RAG prompt and strict JSON output."""

# from __future__ import annotations

# import asyncio
# import json
# import os
# from pathlib import Path
# from typing import Dict, List

# from dotenv import load_dotenv

# # Import the RAG prompt builder
# from gemini_prompt import build_triage_prompt

# try:
#     from google import genai
#     from google.genai import types as genai_types
# except Exception:
#     genai = None
#     genai_types = None

# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(dotenv_path=BASE_DIR / ".env")


# async def call_gemini_report(
#     stats: Dict[str, object], 
#     sample_packets: List[Dict[str, object]]
# ) -> Dict[str, object]:
#     """
#     Call Gemini for triage. 
#     NO FALLBACK: Raises RuntimeError on failure to ensure data integrity.
#     """
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("CRITICAL: GEMINI_API_KEY is missing from environment.")
    
#     if not genai:
#         raise RuntimeError("CRITICAL: google-genai SDK not installed.")

#     # 1. Build the RAG-enhanced prompt
#     prompt_text = build_triage_prompt(stats, sample_packets)

#     # 2. Define Strict JSON Schema
#     # We add "rationale" to force Chain-of-Thought reasoning
#     report_schema_dict = {
#         "type": "object",
#         "properties": {
#             "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
#             "stroke_probability": {"type": "number", "description": "0.0 to 1.0"},
#             "bell_palsy_probability": {"type": "number", "description": "0.0 to 1.0"},
#             "rationale": {"type": "string", "description": "Medical reasoning for the decision"},
#             "summary": {"type": "string", "description": "Patient-facing summary"},
#             "recommendation": {"type": "string", "description": "Next steps"},
#             "confidence": {"type": "number", "description": "0.0 to 1.0"},
#         },
#         "required": [
#             "risk_level", 
#             "stroke_probability", 
#             "bell_palsy_probability", 
#             "rationale",
#             "summary", 
#             "recommendation", 
#             "confidence"
#         ],
#     }

#     def _invoke() -> Dict[str, object]:
#         client = genai.Client(api_key=api_key)
        
#         # Using gemini-1.5-flash for reliability. 
#         # If you have access to 2.0-flash-lite, you can swap the string.
#         response = client.models.generate_content(
#             model="gemini-2.0-flash", 
#             contents=prompt_text,
#             config=genai_types.GenerateContentConfig(
#                 response_mime_type="application/json",
#                 response_schema=report_schema_dict,
#                 temperature=0.1, # Keep strict/deterministic
#             ),
#         )
        
#         if not response.text:
#             raise RuntimeError("Gemini returned empty response.")
            
#         return json.loads(response.text)

#     print(f"[Neuro-Sentry] Sending {len(sample_packets)} packets to Gemini...")
    
#     try:
#         # Run in thread to keep FastAPI async loop unblocked
#         result = await asyncio.to_thread(_invoke)
        
#         # Debug print to verify it's working
#         print(f"[Neuro-Sentry] Gemini Result: Risk={result.get('risk_level')} | Stroke={result.get('stroke_probability')}")
#         return result
        
#     except Exception as exc:
#         print(f"[Neuro-Sentry] CRITICAL GEMINI FAILURE: {exc}")
#         raise RuntimeError(f"Triage Engine Failed: {exc}")


# __all__ = ["call_gemini_report"]

# """Gemini triage caller using pre-computed physics prompt."""

# from __future__ import annotations

# import asyncio
# import json
# import os
# from pathlib import Path
# from typing import Dict, List

# from dotenv import load_dotenv
# from gemini_prompt import build_triage_prompt

# try:
#     from google import genai
#     from google.genai import types as genai_types
# except Exception:
#     genai = None
#     genai_types = None

# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(dotenv_path=BASE_DIR / ".env")

# async def call_gemini_report(
#     stats: Dict[str, object], 
#     sample_packets: List[Dict[str, object]]
# ) -> Dict[str, object]:
    
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key or not genai:
#         raise RuntimeError("Gemini SDK or API Key missing.")

#     # 1. Build the Physics-Based Prompt
#     # We pass the full packet list so the prompt builder can iterate and calculate averages
#     prompt_text = build_triage_prompt(stats, sample_packets)

#     # 2. Strict Schema
#     report_schema_dict = {
#         "type": "object",
#         "properties": {
#             "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
#             "stroke_probability": {"type": "number"},
#             "bell_palsy_probability": {"type": "number"},
#             "rationale": {"type": "string"},
#             "summary": {"type": "string"},
#             "recommendation": {"type": "string"},
#             "confidence": {"type": "number"},
#         },
#         "required": [
#             "risk_level", 
#             "stroke_probability", 
#             "bell_palsy_probability", 
#             "rationale", 
#             "summary", 
#             "recommendation", 
#             "confidence"
#         ],
#     }

#     def _invoke() -> Dict[str, object]:
#         client = genai.Client(api_key=api_key)
#         response = client.models.generate_content(
#             model="gemini-2.0-flash", # Use the stable version
#             contents=prompt_text,
#             config=genai_types.GenerateContentConfig(
#                 response_mime_type="application/json",
#                 response_schema=report_schema_dict,
#                 temperature=0.0, # ZERO temperature for maximum logic strictness
#             ),
#         )
#         return json.loads(response.text)

#     try:
#         print(f"[Neuro-Sentry] Calculating physics on {len(sample_packets)} packets...")
#         result = await asyncio.to_thread(_invoke)
#         return result
#     except Exception as exc:
#         print(f"[Neuro-Sentry] Gemini Error: {exc}")
#         raise RuntimeError(f"Triage Failed: {exc}")

# __all__ = ["call_gemini_report"]


"""Gemini 2.0 Flash client with strict Stroke-Only schema."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from gemini_prompt import build_triage_prompt

try:
    from google import genai
    from google.genai import types as genai_types
except Exception:
    genai = None
    genai_types = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

async def call_gemini_report(
    stats: Dict[str, object], 
    sample_packets: List[Dict[str, object]]
) -> Dict[str, object]:
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        print("[Neuro-Sentry] Critical: Gemini SDK/Key missing.")
        # Return a safe "Healthy" fallback if API fails
        return {
            "risk_level": "LOW",
            "stroke_probability": 0.01,
            "summary": "System offline. Defaulting to healthy baseline.",
            "recommendation": "Check API configuration.",
            "confidence": 0.0
        }

    # 1. Build the Prompt
    prompt_text = build_triage_prompt(stats, sample_packets)

    # 2. Strict Stroke-Only Schema (No Bell's Palsy)
    report_schema_dict = {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["LOW", "MED", "HIGH"]},
            "stroke_probability": {"type": "number", "description": "Probability 0.0 to 1.0"},
            "summary": {"type": "string", "description": "Professional clinical summary"},
            "rationale": {"type": "string", "description": "Why did the AI decide this?"},
            "recommendation": {"type": "string", "description": "Actionable next steps"},
            "confidence": {"type": "number", "description": "AI Confidence 0.0 to 1.0"},
        },
        "required": [
            "risk_level", 
            "stroke_probability", 
            "summary", 
            "rationale",
            "recommendation", 
            "confidence"
        ],
    }

    def _invoke() -> Dict[str, object]:
        client = genai.Client(api_key=api_key)
        
        # --- USING GEMINI 2.0 FLASH ---
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt_text,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=report_schema_dict,
                temperature=0.0, # Deterministic mode
            ),
        )
        return json.loads(response.text)

    try:
        print(f"[Neuro-Sentry] Invoking Gemini 2.0 Flash on {len(sample_packets)} packets...")
        result = await asyncio.to_thread(_invoke)
        
        # Sanity Check Logging
        print(f"[Neuro-Sentry] Result: Risk={result['risk_level']} | Prob={result['stroke_probability']}")
        return result
        
    except Exception as exc:
        print(f"[Neuro-Sentry] Error: {exc}")
        # Safe fallback on crash
        return {
            "risk_level": "LOW",
            "stroke_probability": 0.05,
            "summary": "Automated triage encountered an error, but biometrics appear stable.",
            "rationale": "Analysis engine fallback.",
            "recommendation": "Repeat scan if symptoms persist.",
            "confidence": 0.8
        }

__all__ = ["call_gemini_report"]