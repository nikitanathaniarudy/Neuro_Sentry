import json
import torch
import sys
import os
from extract_features import load_json, extract_features

# Rebuild model architecture to load weights
class TriageMLP(torch.nn.Module):
    def __init__(self, input_size=5):
        super().__init__()
        self.fc1 = torch.nn.Linear(input_size, 16)
        self.fc2 = torch.nn.Linear(16, 8)
        self.fc3 = torch.nn.Linear(8, 1)
        self.relu = torch.nn.ReLU()
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.sigmoid(self.fc3(x))

# Load trained model
model = TriageMLP()
model.load_state_dict(torch.load('model.pth'))
model.eval()

def run_inference(input_file: str, output_file: str = None):
    seq, fps = load_json(input_file)
    features = extract_features(seq, fps)
    
    # Extract feat vec
    feat_tensor = torch.tensor([[
        features['branch_scores'].get('temporal', 0),
        features['branch_scores'].get('zygomatic', 0),
        features['branch_scores'].get('buccal', 0),
        features['branch_scores'].get('mandibular', 0),
        features['asymmetry_global']
    ]], dtype=torch.float32)
    
    with torch.no_grad():
        ml_prob = model(feat_tensor).item()
    
    # Enrich output
    output = {
        **features,
        "triage_prob_ml": float(ml_prob),
        "recommendation": "Code Stroke - Alert Triage" if ml_prob > 0.5 else "Monitor - Low Risk"
    }
    
    # Auto-save if no output_file
    if output_file is None:
        base_name = os.path.basename(input_file)
        output_file = base_name.replace('.json', '_output.json')
    
    with open(f"data/{output_file}", 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Processed {input_file} → {output_file}")
    print(f"ML Triage Prob: {ml_prob:.3f} | Rec: {output['recommendation']}")
    print(f"Key Scores: { {k: f'{v:.2f}' for k, v in features['branch_scores'].items()} }")
    return output

# CLI for easy testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/training_fixed/stroke_000.json"  # Default test
    
    run_inference(input_file)