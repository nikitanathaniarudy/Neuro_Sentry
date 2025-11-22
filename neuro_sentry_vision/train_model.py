import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import glob
import numpy as np
from extract_features import load_json, extract_features  # Import your func

class TriageMLP(nn.Module):
    def __init__(self, input_size=5):  # temporal, zygomatic, buccal, mandibular, asym
        super().__init__()
        self.fc1 = nn.Linear(input_size, 16)
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.sigmoid(self.fc3(x))

# Load data & extract features
X, y = [], []
for file in glob.glob("data/training_fixed/*.json"):
    seq, fps = load_json(file)
    feats_dict = extract_features(seq, fps)
    # Flatten to [temporal, zygomatic, buccal, mandibular, asym]
    feat_vec = np.array([
        feats_dict['branch_scores'].get('temporal', 0),
        feats_dict['branch_scores'].get('zygomatic', 0),
        feats_dict['branch_scores'].get('buccal', 0),
        feats_dict['branch_scores'].get('mandibular', 0),
        feats_dict['asymmetry_global']
    ])
    label = 1 if 'stroke' in file else 0  # From filename
    X.append(feat_vec)
    y.append(label)

X = np.array(X)
y = np.array(y).reshape(-1, 1)

# Dataset/Loader
dataset = TensorDataset(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32))
loader = DataLoader(dataset, batch_size=16, shuffle=True)

# Train
model = TriageMLP()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

for epoch in range(10):  # More epochs for better fit
    total_loss = 0
    for feats, labels in loader:
        optimizer.zero_grad()
        out = model(feats)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}, Avg Loss: {total_loss / len(loader):.4f}")

torch.save(model.state_dict(), 'model.pth')
print("Model saved to model.pth. Test acc:", (model(torch.tensor(X, dtype=torch.float32)).round() == torch.tensor(y, dtype=torch.float32)).float().mean().item())