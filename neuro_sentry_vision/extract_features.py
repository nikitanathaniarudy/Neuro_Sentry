import json
import numpy as np
from typing import Dict

# Simplified branch indices (MediaPipe approx; left/right symmetric)
# Simplified branch indices (for 68-point Dlib-style landmarks)
BRANCHES = {
    'temporal': ([17, 18, 19], [22, 23, 24]),  # Left/right eyebrows (lift proxy)
    'zygomatic': ([2, 3, 4], [13, 14, 15]),   # Jaw/cheek edges (smile raise approx)
    'buccal': ([48], [54]),                    # Mouth corners (cheilion proxy)
    'mandibular': ([56, 57], [58, 59])         # Lower lip (droop proxy)
}

def load_json(input_file: str) -> tuple:
    with open(input_file, 'r') as f:
        data = json.load(f)
    seq = np.array(data['landmarks_sequence']).reshape(-1, 68, 2)  # Adjust 68 to your N
    fps = data['fps']
    return seq, fps

def extract_features(seq: np.ndarray, fps: float = 30.0) -> Dict[str, float]:
    T, N, _ = seq.shape
    dt = 1.0 / fps
    action_start = T // 2

    # Smooth (moving avg)
    window = 5;#min(3, T)
    seq_smooth = np.apply_along_axis(lambda col: np.convolve(col, np.ones(window)/window, mode='same'), axis=0, arr=seq)

    branch_scores = {}
    global_asyms = []

    for branch, (left_idx, right_idx) in BRANCHES.items():
        left_pos = np.mean(seq_smooth[:, left_idx, 1], axis=1)  # Avg y for lift
        right_pos = np.mean(seq_smooth[:, right_idx, 1], axis=1)

        left_vel = np.gradient(left_pos, dt)
        right_vel = np.gradient(right_pos, dt)
        left_accel = np.gradient(left_vel, dt)
        right_accel = np.gradient(right_vel, dt)

        left_a = left_accel[action_start:]
        right_a = right_accel[action_start:]

        left_visc = 1.0 / (np.mean(np.abs(left_a)) + 1e-6)
        right_visc = 1.0 / (np.mean(np.abs(right_a)) + 1e-6)
        visc_thresh, max_visc = 0.05, 0.5
        left_score = np.clip((left_visc - visc_thresh) / (max_visc - visc_thresh), 0, 1)
        right_score = np.clip((right_visc - visc_thresh) / (max_visc - visc_thresh), 0, 1)

        branch_score = np.mean([left_score, right_score])
        asym = abs(left_visc - right_visc) / (np.mean([left_visc, right_visc]) + 1e-6)
        branch_scores[branch] = branch_score
        global_asyms.append(asym)
        # DEBUG PRINTS (remove later)
        # print(f"\n--- Branch: {branch} ---")
        # print(f"Mean |left_accel| (action): {np.mean(np.abs(left_a)):.4f}")
        # print(f"Mean |right_accel| (action): {np.mean(np.abs(right_a)):.4f}")
        # print(f"left_visc: {left_visc:.4f}, right_visc: {right_visc:.4f}")
        # print(f"left_score: {left_score:.4f}, right_score: {right_score:.4f}")

    global_asym = np.mean(global_asyms)

    # Simple triage logic (pre-ML)
    lower_mean = np.mean([branch_scores.get(b, 0) for b in ['zygomatic', 'buccal', 'mandibular']])
    temporal_spared = branch_scores.get('temporal', 0) < 0.3
    triage_prob = 1.0 if (lower_mean > 0.5 and temporal_spared) else lower_mean * global_asym

    return {
        'branch_scores': branch_scores,
        'asymmetry_global': float(global_asym),
        'triage_prob': float(triage_prob)
    }

# Test standalone
if __name__ == "__main__":
    # features = extract_features(load_json("data/training/stroke_019.json")[0])
    features = extract_features(load_json("data/training_fixed/stroke_002.json")[0])
    print(features)