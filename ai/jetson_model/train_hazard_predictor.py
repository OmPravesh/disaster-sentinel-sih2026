"""
Disaster Sentinel — Jetson Hazard Predictor AI Trainer

Trains an ML hazard risk model (RandomForest/GradientBoosting) on synthetic/historical disaster datasets.
Exports serialized model file for runtime inference on Jetson Orin Nano.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def generate_hazard_dataset(num_samples: int = 10000):
    """
    Generate synthetic dataset matching 3-layer sensor features:
      Features: [l1_anom, l2_anom, l3_anom, combined_score, rate_flag, battery]
      Labels: 0 = NORMAL, 1 = FLOOD, 2 = FIRE, 3 = LANDSLIDE
    """
    np.random.seed(42)
    X = []
    y = []

    for _ in range(num_samples):
        hazard = np.random.choice([0, 1, 2, 3], p=[0.70, 0.10, 0.10, 0.10])
        
        if hazard == 0:  # NORMAL
            l1 = np.random.uniform(0.0, 0.20)
            l2 = np.random.uniform(0.0, 0.20)
            l3 = np.random.uniform(0.0, 0.20)
            rate = np.random.choice([0, 1], p=[0.9, 0.1])
        else:  # DISASTER (All 3 layers elevated for high confidence)
            severity = np.random.uniform(0.5, 1.0)
            l1 = np.clip(severity + np.random.normal(0, 0.05), 0.4, 1.0)
            l2 = np.clip(severity + np.random.normal(0, 0.08), 0.3, 1.0)
            l3 = np.clip(severity + np.random.normal(0, 0.10), 0.2, 1.0)
            rate = np.random.choice([1, 3], p=[0.3, 0.7])
            
        combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3
        battery = np.random.randint(20, 100)
        
        X.append([l1, l2, l3, combined, rate, battery])
        y.append(hazard)

    return np.array(X), np.array(y)


def main():
    print("=== Training Jetson Hazard Prediction Model ===")
    X, y = generate_hazard_dataset(10000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    print("\nModel Evaluation:")
    print(classification_report(y_test, y_pred, target_names=["NORMAL", "FLOOD", "FIRE", "LANDSLIDE"]))
    
    out_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "hazard_predictor.pkl")
    
    joblib.dump(clf, out_file)
    print(f"\n[AI] Model saved to {out_file}")


if __name__ == "__main__":
    main()
