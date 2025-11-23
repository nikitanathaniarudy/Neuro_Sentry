# """Prompt builder for Gemini triage."""

# from __future__ import annotations

# import json
# from typing import Dict, List


# def build_triage_prompt(stats: Dict[str, object], sample_packets: List[Dict[str, object]], max_mesh_packets: int = 2) -> str:
#     """
#     Build a concise prompt for Gemini triage using stats + raw packet samples.
#     Includes a small number of face mesh examples so Gemini can reason about asymmetry.
#     """
#     face_mesh_samples = []
#     for pkt in sample_packets:
#         pts = pkt.get("face_points") or []
#         if pts:
#             face_mesh_samples.append(pts)
#         if len(face_mesh_samples) >= max_mesh_packets:
#             break

#     payload = {
#         "computed_stats": stats,
#         "face_mesh_samples": face_mesh_samples,
#         "raw_packets_sample": sample_packets[:8],
#     }

#     instructions = (
#         "You are Neuro-Sentry. Analyze Presage vitals and face mesh landmarks to estimate stroke vs Bell's palsy risk. "
#         "Return ONLY JSON with keys: risk_level (LOW/MED/HIGH), stroke_probability (0-1), "
#         "bell_palsy_probability (0-1), summary (string), recommendation (string), confidence (0-1). "
#         "Do not include markdown or any extra keys."
#     )

#     return instructions + "\n\nDATA:\n" + json.dumps(payload)


# __all__ = ["build_triage_prompt"]

# """Prompt builder for Gemini triage with Clinical RAG Context."""

# from __future__ import annotations

# import json
# from typing import Dict, List

# # --- RAG: STATIC KNOWLEDGE BASE ---
# # We inject this "Textbook Definition" so Gemini doesn't hallucinate medical rules.
# CLINICAL_KNOWLEDGE_BASE = """
# CLINICAL REFERENCE GUIDE: FACIAL NERVE PATHOLOGY

# 1. NORMAL PHYSIOLOGY (HEALTHY):
#    - Human faces are naturally slightly asymmetrical.
#    - Minor asymmetry scores (< 100.0 variance) should be considered NORMAL/NOISE.
#    - Vitals: HR 60-100 BPM is Normal.
#    - RESULT: If metrics are low, Probability must be < 0.05 (5%).

# 2. CENTRAL FACIAL PALSY (ISCHEMIC STROKE):
#    - KEY SIGN: Contralateral paralysis of the lower face ONLY.
#    - MECHANISM: The forehead is bilaterally innervated, so the upper face is SPARED.
#    - PATTERN: HIGH Mouth Asymmetry + LOW Brow Asymmetry.
#    - VITALS: Often accompanied by hypertension or tachycardia (Distress).

# 3. PERIPHERAL FACIAL PALSY (BELL'S PALSY):
#    - KEY SIGN: Ipsilateral paralysis of the ENTIRE half of the face.
#    - MECHANISM: Damage to the facial nerve (CN VII) nucleus or nerve itself.
#    - PATTERN: HIGH Mouth Asymmetry + HIGH Brow Asymmetry.
#    - NOTE: This is much more common than stroke in young, healthy-appearing individuals with asymmetry.
# """

# def build_triage_prompt(stats: Dict[str, object], sample_packets: List[Dict[str, object]]) -> str:
#     """
#     Builds a prompt that forces Gemini to act as a grounded medical classifier.
#     """
    
#     # 1. Pre-process Stats for Context (Help Gemini understand the scale)
#     mouth_score = float(stats.get("mouth_asymmetry_mean") or 0.0)
#     brow_score = float(stats.get("brow_asymmetry_mean") or 0.0)
    
#     # Human-readable context to prevent "Number Hallucination"
#     # We explicitly tell Gemini if the number is considered "High" or "Low" relative to our math.
#     context_notes = []
#     if mouth_score < 200.0 and brow_score < 200.0:
#         context_notes.append("METRICS ASSESSMENT: Values suggest normal physiological asymmetry (Healthy).")
#     elif mouth_score > 500.0:
#         context_notes.append("METRICS ASSESSMENT: Significant lower facial droop detected.")
    
#     payload = {
#         "computed_stats": stats,
#         "assessment_hint": " ".join(context_notes),
#         # We limit raw packets to prevent token overflow, just showing 2 for structure check
#         "raw_telemetry_sample": sample_packets[:2] 
#     }

#     instructions = (
#         "You are Neuro-Sentry, a clinical decision support system. "
#         "Your job is to analyze biometric telemetry and output a strict JSON triage report.\n\n"
#         f"{CLINICAL_KNOWLEDGE_BASE}\n\n" # <--- INJECTING THE RAG CONTEXT HERE
#         "INSTRUCTIONS:\n"
#         "1. Compare the 'computed_stats' against the Reference Guide above.\n"
#         "2. If values are within the NORMAL/NOISE range, risk_level MUST be 'LOW' and probabilities near 0.\n"
#         "3. Do not alarm healthy users. Minor variation is not a stroke.\n"
#         "4. Return ONLY valid JSON matching the schema."
#     )

#     return instructions + "\n\nPATIENT DATA:\n" + json.dumps(payload)


# __all__ = ["build_triage_prompt"]

# """Prompt builder that pre-calculates asymmetry physics to prevent LLM hallucinations."""

# from __future__ import annotations

# import json
# import math
# from typing import Dict, List, Tuple

# # --- MEDIAPIPE FACE MESH INDICES (The "Cranial Nerve Map") ---
# IDX_NOSE = 1         # Reference Point
# IDX_CHIN = 152       # For Height Normalization
# IDX_MOUTH_L = 61     # Left Mouth Corner
# IDX_MOUTH_R = 291    # Right Mouth Corner
# IDX_BROW_L = 105     # Left Eyebrow Arch
# IDX_BROW_R = 334     # Right Eyebrow Arch

# def _calculate_asymmetry(
#     points: List[List[float]]
# ) -> Tuple[float, float, bool]:
#     """
#     Returns (mouth_asymmetry_percent, brow_asymmetry_percent, is_valid).
#     Calculates vertical deviation normalized by face height.
#     """
#     try:
#         # 1. Extract Key Coordinates (Y-axis is vertical height)
#         nose_y = points[IDX_NOSE][1]
#         chin_y = points[IDX_CHIN][1]
        
#         mouth_l_y = points[IDX_MOUTH_L][1]
#         mouth_r_y = points[IDX_MOUTH_R][1]
        
#         brow_l_y = points[IDX_BROW_L][1]
#         brow_r_y = points[IDX_BROW_R][1]

#         # 2. Calculate Face Height (Normalization Factor)
#         # This ensures the math works whether the user is 1ft or 5ft from camera.
#         face_height = abs(chin_y - nose_y)
#         if face_height < 10: return 0.0, 0.0, False # Garbage frame

#         # 3. Calculate Mouth Asymmetry (Vertical difference relative to nose)
#         # Logic: |(Left_Drop) - (Right_Drop)| / Face_Height
#         dist_mouth_l = abs(mouth_l_y - nose_y)
#         dist_mouth_r = abs(mouth_r_y - nose_y)
#         mouth_asym = abs(dist_mouth_l - dist_mouth_r) / face_height

#         # 4. Calculate Brow Asymmetry
#         dist_brow_l = abs(brow_l_y - nose_y)
#         dist_brow_r = abs(brow_r_y - nose_y)
#         brow_asym = abs(dist_brow_l - dist_brow_r) / face_height

#         return mouth_asym, brow_asym, True

#     except (IndexError, TypeError):
#         return 0.0, 0.0, False

# def compute_session_features(packets: List[Dict[str, object]]) -> Dict[str, object]:
#     """
#     Aggregates raw packets into a single clinical summary.
#     """
#     mouth_scores = []
#     brow_scores = []
#     heart_rates = []
    
#     for p in packets:
#         # Vitals
#         if p.get("heart_rate"):
#             hr = float(p["heart_rate"])
#             if 40 < hr < 200: heart_rates.append(hr)

#         # Face Physics
#         points = p.get("face_points", [])
#         if points and len(points) > 400:
#             m_score, b_score, valid = _calculate_asymmetry(points)
#             if valid:
#                 mouth_scores.append(m_score)
#                 brow_scores.append(b_score)

#     # Averages
#     avg_mouth = sum(mouth_scores) / len(mouth_scores) if mouth_scores else 0.0
#     avg_brow = sum(brow_scores) / len(brow_scores) if brow_scores else 0.0
#     avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 75.0

#     return {
#         "avg_mouth_asymmetry": float(round(avg_mouth, 4)),
#         "avg_brow_asymmetry": float(round(avg_brow, 4)),
#         "avg_heart_rate": float(round(avg_hr, 1)),
#         "data_points_used": len(mouth_scores)
#     }

# def build_triage_prompt(stats: Dict[str, object], sample_packets: List[Dict[str, object]]) -> str:
    
#     # 1. Run the "Digital Sunnybrook" Math
#     features = compute_session_features(sample_packets)
    
#     # 2. Generate Clinical Interpretations (The "Grounding" Layer)
#     # This forces Gemini to accept our math instead of guessing.
    
#     mouth_val = features["avg_mouth_asymmetry"]
#     brow_val = features["avg_brow_asymmetry"]
    
#     # Thresholds derived from medical literature (Sunnybrook scale)
#     # < 3% deviation is usually normal human asymmetry
#     mouth_status = "NORMAL" if mouth_val < 0.03 else "ABNORMAL (DROOP DETECTED)"
#     brow_status = "NORMAL" if brow_val < 0.03 else "ABNORMAL (PARALYSIS DETECTED)"
    
#     clinical_context = f"""
#     PRE-COMPUTED BIOMETRIC PHYSICS:
#     - Mouth Asymmetry Index: {mouth_val:.4f} -> CLINICAL RATING: {mouth_status}
#     - Brow Asymmetry Index:  {brow_val:.4f} -> CLINICAL RATING: {brow_status}
#     - Average Heart Rate:    {features['avg_heart_rate']} BPM
#     """

#     instructions = (
#         "You are Neuro-Sentry, a stroke triage AI. Use the PRE-COMPUTED PHYSICS above to determine risk.\n"
#         "DO NOT analyze the raw coordinates yourself. Trust the 'CLINICAL RATING'.\n\n"
#         "DIAGNOSTIC LOGIC:\n"
#         "1. HEALTHY: If Clinical Ratings are NORMAL, Risk is LOW (Probability < 0.1).\n"
#         "2. STROKE: If Mouth is ABNORMAL but Brow is NORMAL (Forehead Sparing) -> HIGH Stroke Risk.\n"
#         "3. BELL'S PALSY: If Mouth is ABNORMAL AND Brow is ABNORMAL (Hemifacial) -> HIGH Bell's Risk.\n\n"
#         "Return strict JSON matching the schema."
#     )

#     return instructions + "\n\n" + clinical_context

# __all__ = ["build_triage_prompt"]


"""Prompt builder with Cincinnati Prehospital Stroke Scale (CPSS) RAG."""

from __future__ import annotations

import json
import subprocess
import json
import tempfile
from typing import Dict, List, Tuple

# --- MEDIAPIPE INDICES ---
IDX_NOSE = 1
IDX_CHIN = 152
IDX_MOUTH_L = 61
IDX_MOUTH_R = 291
IDX_EYE_L = 33
IDX_EYE_R = 263

# --- RAG: CLINICAL PROTOCOL ---
# This text block effectively "brainwashes" Gemini to follow real medical rules
CPSS_PROTOCOL = """
CLINICAL PROTOCOL: CINCINNATI PREHOSPITAL STROKE SCALE (CPSS)
Target Pathology: Acute Ischemic Stroke (AIS).

1. FACIAL DROOP ANALYSIS:
   - Normal: Both sides of face move equally or have minor natural asymmetry (< 8% deviation).
   - Abnormal: One side of face does not move as well as the other (> 10% deviation).
   
2. TRIAGE RULES:
   - If asymmetry is LOW (< 0.08), the patient is HEALTHY. Do not hallucinate pathology.
   - High heart rate alone is NOT a stroke; it is likely anxiety/demo effect.
   - Stroke probability should barely exceed 5% for asymptomatic individuals.

3. THRESHOLDS:
   - Asymmetry < 0.08 (8%): CLINICALLY INSIGNIFICANT (SAFE)
   - Asymmetry > 0.15 (15%): PROBABLE LESION (DANGER)
"""

def _calculate_physics(points: List[List[float]]) -> Tuple[float, bool]:
    """Calculates pure mouth asymmetry normalized by face height."""
    try:
        nose_y = points[IDX_NOSE][1]
        chin_y = points[IDX_CHIN][1]
        mouth_l_y = points[IDX_MOUTH_L][1]
        mouth_r_y = points[IDX_MOUTH_R][1]

        # Normalization factor (Face Height)
        face_height = abs(chin_y - nose_y)
        if face_height < 10: return 0.0, False

        # Calculate Vertical Mouth Offset
        # How much lower is one corner vs the other?
        dist_l = abs(mouth_l_y - nose_y)
        dist_r = abs(mouth_r_y - nose_y)
        
        # Raw Offset / Face Height = Percentage Deviation
        raw_asym = abs(dist_l - dist_r)
        normalized_asym = raw_asym / face_height

        return normalized_asym, True
    except Exception:
        return 0.0, False

def compute_bio_features(packets: List[Dict[str, object]]) -> Dict[str, float]:
    mouth_scores = []
    valid_packets = 0
    
    for p in packets:
        points = p.get("face_points", [])
        if points and len(points) > 400:
            score, valid = _calculate_physics(points)
            if valid:
                mouth_scores.append(score)
                valid_packets += 1
    
    # Smooth out noise using average
    avg_mouth = sum(mouth_scores) / len(mouth_scores) if mouth_scores else 0.0
    
    return {
        "mouth_asymmetry_index": float(round(avg_mouth, 4)),
        "packets_analyzed": valid_packets
    }


def compute_speech_features(audio_path: str) -> Dict[str, float]:
    """
    Uses Gemini 2.0 Flash to transcribe audio and detect slurring.
    Returns a slur_score between 0 (clear) and 1 (very slurred).
    """
    try:
        from google import genai
        from google.genai import types as genai_types
        import os
        from pathlib import Path
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[Audio] Warning: GEMINI_API_KEY not found. Audio analysis skipped.")
            return {"slur_score": 0.0, "transcription": ""}
        
        # Upload audio file to Gemini Files API
        client = genai.Client(api_key=api_key)
        
        # Upload the audio file with explicit MIME type
        with open(audio_path, "rb") as f:
            audio_file = client.files.upload(file=f, config={"mime_type": "audio/wav"})
        
        print(f"[Audio] Uploaded audio file: {audio_file.name}")
        
        # Use Gemini to transcribe and analyze speech clarity
        prompt = """Transcribe this audio and analyze the speech for signs of slurring or speech difficulty.

Provide a JSON response with:
1. "transcription": The full text of what was said
2. "clarity_score": A score from 0-100 (100 = perfectly clear, 0 = completely slurred/unintelligible)
3. "notes": Brief assessment of speech quality

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_file],
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        
        result = json.loads(response.text)
        transcription = result.get("transcription", "")
        clarity_score = result.get("clarity_score", 100)
        
        # Convert clarity score (0-100) to slur score (0-1, where 1 = heavily slurred)
        slur_score = round((100 - clarity_score) / 100, 2)
        
        print(f"[Audio] Transcription: {transcription}")
        print(f"[Audio] Clarity: {clarity_score}% | Slur Score: {slur_score}")
        
        # Clean up uploaded file
        try:
            client.files.delete(name=audio_file.name)
        except:
            pass
        
        return {
            "slur_score": slur_score,
            "transcription": transcription,
            "clarity_score": clarity_score
        }
        
    except ImportError:
        print("[Audio] Warning: 'google-genai' library not installed. Audio analysis skipped.")
        return {"slur_score": 0.0, "transcription": ""}
    except Exception as e:
        print(f"[Audio] Error during transcription: {e}")
        return {"slur_score": 0.0, "transcription": ""}

def compute_combined_features(packets: List[Dict[str, object]], audio_path: str = None) -> Dict[str, float]:
    bio_features = compute_bio_features(packets)
    
    if audio_path:
        speech_features = compute_speech_features(audio_path)
        bio_features.update(speech_features)
    else:
        bio_features["slur_score"] = 0.0  # default if no audio

    return bio_features

def build_triage_prompt(stats: Dict[str, object], sample_packets: List[Dict[str, object]], audio_path: str = None) -> str:
    # 1. Run Math
    features = compute_combined_features(sample_packets, audio_path)
    mouth_val = features["mouth_asymmetry_index"]
    slur_val = features.get("slur_score", 0.0)
    transcription = features.get("transcription", "")
    clarity_score = features.get("clarity_score", 100)
    
    # 2. Generate "Technician Notes" for Gemini
    # We force the interpretation here so Gemini doesn't guess.
    if mouth_val < 0.02 and slur_val < 0.2:
        tech_note = "Technician Note: Asymmetry is within normal physiological limits and no slurring is detected. PATIENT IS LIKELY HEALTHY."
    elif mouth_val >= 0.15 or slur_val >= 0.5:
        tech_note = "Technician Note: SIGNIFICANT DROOP AND/OR SLURRED SPEECH DETECTED. High Stroke Risk."
    else:
        tech_note = "Technician Note: Mild asymmetry or slight slurring. Monitor closely."

    # 3. Construct the Prompt - Include BOTH vitals AND audio data
    payload = {
        "physics_engine_output": features,
        "vitals_summary": stats,
        "automated_assessment": tech_note,
        "audio_analysis": {
            "transcription": transcription,
            "clarity_score": clarity_score,
            "slur_score": slur_val
        } if audio_path else None
    }

    instructions = (
        "You are Neuro-Sentry, an advanced AI Neurologist using the CPSS Protocol.\\n"
        f"{CPSS_PROTOCOL}\\n\\n"
        "TASK:\\n"
        "1. Analyze the 'physics_engine_output' which contains facial asymmetry data from video analysis.\\n"
        "2. Analyze the 'audio_analysis' which contains speech transcription and clarity metrics.\\n"
        "3. Use BOTH 'mouth_asymmetry_index' (from video) AND 'slur_score' (from audio) to assess stroke risk.\\n"
        "4. If mouth_asymmetry_index < 0.08 AND slur_score < 0.2, declare Risk: LOW.\\n"
        "5. Consider the actual transcribed speech content for additional diagnostic context.\\n"
        "6. Ignore Bell's Palsy. Focus ONLY on Ischemic Stroke risk assessment.\\n"
        "7. Be conservative but thorough. Do not scare healthy users, but be detailed in your analysis.\\n\\n"
        
        "RESPONSE REQUIREMENTS:\\n"
        "- 'summary': Write 3-4 comprehensive sentences describing what you observed and your overall assessment.\\n"
        "- 'rationale': Provide 3-5 detailed sentences explaining your medical reasoning. Reference specific metrics and thresholds.\\n"
        "- 'recommendation': Give 3-4 specific, actionable sentences with clear next steps appropriate to the risk level.\\n"
        "- 'key_findings': List 3-5 specific clinical observations (e.g., 'Facial symmetry within normal limits', 'Speech clarity at 92%').\\n"
        "- 'warning_signs': List any concerning symptoms detected, or empty array if none found.\\n"
        "- 'speech_clarity_score': 0-100 score (100=perfectly clear, 0=completely slurred).\\n\\n"
        
        "Be thorough, professional, and specific. Reference actual measurements from the data.\\n"
    )

    return instructions + "\n\nLIVE TELEMETRY:\n" + json.dumps(payload, indent=2)

__all__ = ["build_triage_prompt"]