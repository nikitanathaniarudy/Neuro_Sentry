# import json
# import numpy as np
# import os

# # Config
# T, N = 30, 68  # Frames, landmarks (use 468 for full MediaPipe)
# os.makedirs("data/training", exist_ok=True)

# np.random.seed(42)

# # Base landmarks (random normalized)
# base_landmarks = np.random.uniform(0, 1, (N, 2))

# # Healthy template: Symmetric smile lift in mouth (indices 48-68)
# healthy_seq = np.tile(base_landmarks, (T, 1, 1))
# smile_start = 15
# mouth_indices = np.arange(48, min(68, N))
# for t in range(smile_start, T):
#     progress = (t - smile_start) / (T - smile_start)
#     if progress > 0:
#         healthy_seq[t, mouth_indices, 1] += 0.15 * progress * np.sin(progress * np.pi)

# # Stroke template: Asymmetric/slower left (0-34 indices)
# stroke_seq = healthy_seq.copy()
# left_indices = np.arange(0, N//2)
# stroke_seq[smile_start:, left_indices, 1] *= 0.6  # 40% slower
# stroke_seq += np.random.normal(0, 0.005, stroke_seq.shape)

# # Generate samples
# for i in range(80):  # Healthy
#     var = np.random.normal(0, 0.01, healthy_seq.shape)
#     var_seq = healthy_seq + var
#     landmarks = [lm.flatten().tolist() for lm in var_seq]
#     data = {
#         "session_id": f"healthy_{i:03d}",
#         "fps": 30.0,
#         "landmarks_sequence": landmarks
#     }
#     with open(f"data/training/{data['session_id']}.json", "w") as f:
#         json.dump(data, f, indent=2)

# for i in range(20):  # Stroke
#     var = np.random.normal(0, 0.01, stroke_seq.shape)
#     var_seq = stroke_seq + var
#     sev = np.random.uniform(0.4, 0.8)
#     var_seq[smile_start:, left_indices, 1] *= sev
#     landmarks = [lm.flatten().tolist() for lm in var_seq]
#     data = {
#         "session_id": f"stroke_{i:03d}",
#         "fps": 30.0,
#         "landmarks_sequence": landmarks
#     }
#     with open(f"data/training/{data['session_id']}.json", "w") as f:
#         json.dump(data, f, indent=2)

# print(f"Generated 100 dummy JSONs in data/training/. Check one: head data/training/healthy_000.json")

import json
import numpy as np
import os

# Config
T, N = 30, 68  # Frames, landmarks
os.makedirs("data/training_fixed", exist_ok=True)  # New folder

np.random.seed(42)

# Base landmarks (random normalized)
base_landmarks = np.random.uniform(0, 1, (N, 2))

# Healthy template: Subtle symmetric smile lift in mouth (indices 48-68)
healthy_seq = np.tile(base_landmarks, (T, 1, 1))
smile_start = 15
mouth_indices = np.arange(48, 68)  # Full mouth area
for t in range(smile_start, T):
    progress = (t - smile_start) / (T - smile_start)
    if progress > 0:
        healthy_seq[t, mouth_indices, 1] += 0.05 * progress * np.sin(progress * np.pi)  # Smaller lift

# Left groups for stroke: jaw/brow + left mouth
left_indices = list(range(0, 35)) + list(range(48, 59))  # 0-34 left face + 48-58 left mouth

# Stroke template: Asymmetric/slower left
stroke_seq = healthy_seq.copy()
stroke_seq[smile_start:, left_indices, 1] *= 0.6  # Base slow
stroke_seq += np.random.normal(0, 0.005, stroke_seq.shape)

# Generate samples
for i in range(80):  # Healthy
    var = np.random.normal(0, 0.01, healthy_seq.shape)
    var_seq = healthy_seq + var
    landmarks = [lm.flatten().tolist() for lm in var_seq]
    data = {
        "session_id": f"healthy_{i:03d}",
        "fps": 30.0,
        "landmarks_sequence": landmarks
    }
    with open(f"data/training_fixed/{data['session_id']}.json", "w") as f:
        json.dump(data, f, indent=2)

for i in range(20):  # Stroke
    var = np.random.normal(0, 0.01, stroke_seq.shape)
    var_seq = stroke_seq + var
    sev = np.random.uniform(0.4, 0.8)
    var_seq[smile_start:, left_indices, 1] *= sev  # Extra slow
    landmarks = [lm.flatten().tolist() for lm in var_seq]
    data = {
        "session_id": f"stroke_{i:03d}",
        "fps": 30.0,
        "landmarks_sequence": landmarks
    }
    with open(f"data/training_fixed/{data['session_id']}.json", "w") as f:
        json.dump(data, f, indent=2)

print(f"Generated 100 fixed dummy JSONs in data/training_fixed/. Check: type data\\training_fixed\\healthy_000.json")