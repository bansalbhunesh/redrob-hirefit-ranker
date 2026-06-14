#!/usr/bin/env python3
"""ConFit v2: Train Role-Aware Mixture of Experts (MMoE)
Trains a 2-layer MLP (64 hidden units) for each of the 5 role families.
Uses scikit-learn's MLPRegressor to avoid heavy PyTorch dependencies,
and extracts the weights to a simple numpy .npz format for the core pipeline.
"""

import sys
from pathlib import Path
import numpy as np

try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.metrics import ndcg_score
except ImportError:
    print("Please install scikit-learn: pip install scikit-learn")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.moe_scorer import ROLE_FAMILIES, INPUT_DIM, HIDDEN_DIM

def generate_synthetic_data(num_samples=2000):
    """Generates synthetic feature vectors and labels for training."""
    # This simulates a dataset where different features matter for different roles.
    # In a real environment, this would come from a labeled dataset.
    
    X = np.random.rand(num_samples, INPUT_DIM)
    
    # We will construct labels tailored for each role
    y_roles = {}
    
    for role in ROLE_FAMILIES:
        y = np.zeros(num_samples)
        
        # Base features (0: core, 3: depth, 13: prod evidence)
        y += X[:, 0] * 0.2 + X[:, 3] * 0.4 + X[:, 13] * 0.2
        
        # Role-specific tweaks
        if role == "Backend Engineer":
            y += X[:, 30] * 0.5 if INPUT_DIM > 30 else X[:, 1] * 0.5
        elif role == "Data/BI Engineer":
            y += X[:, 31] * 0.5 if INPUT_DIM > 31 else X[:, 2] * 0.5
            
        # Add some noise
        y += np.random.normal(0, 0.05, num_samples)
        y = np.clip(y, 0.0, 1.0)
        y_roles[role] = y
        
    return X, y_roles

def main():
    MODELS_DIR = ROOT / "models"
    MODELS_DIR.mkdir(exist_ok=True)
    
    print("Generating synthetic training data for experts...")
    X_train, y_roles = generate_synthetic_data(3000)
    X_val, y_roles_val = generate_synthetic_data(500)
    
    for role in ROLE_FAMILIES:
        print(f"\nTraining expert for: {role}")
        
        y_train = y_roles[role]
        y_val = y_roles_val[role]
        
        model = MLPRegressor(
            hidden_layer_sizes=(HIDDEN_DIM,),
            activation='relu',
            solver='adam',
            max_iter=500,
            early_stopping=True,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        preds = model.predict(X_val)
        
        # compute NDCG
        # scikit-learn ndcg_score expects shape (1, n_samples)
        val_ndcg = ndcg_score([y_val], [preds], k=10)
        print(f"Validation NDCG@10: {val_ndcg:.4f}")
        
        # Extract weights
        # model.coefs_ is a list of weight matrices: [w1, w2]
        # model.intercepts_ is a list of biases: [b1, b2]
        w1 = model.coefs_[0]
        b1 = model.intercepts_[0]
        w2 = model.coefs_[1]
        b2 = model.intercepts_[1]
        
        # Save to npz
        safe_name = role.replace("/", "_").replace(" ", "_")
        out_path = MODELS_DIR / f"expert_{safe_name}.npz"
        
        np.savez(out_path, w1=w1, b1=b1, w2=w2, b2=b2)
        print(f"Saved weights to {out_path}")

if __name__ == "__main__":
    main()
