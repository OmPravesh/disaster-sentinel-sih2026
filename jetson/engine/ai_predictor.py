"""
═══════════════════════════════════════════════════════════
DISASTER SENTINEL — GRU AI Prediction Engine
═══════════════════════════════════════════════════════════

Lightweight GRU (Gated Recurrent Unit) neural network for 
predicting future disaster probability at T+15, T+30, T+60 minutes.

This is the CENTERPIECE of the system — the AI that makes
Disaster Sentinel stand out at SIH 2026.

Architecture:
  Input:  (batch, seq_len=30, features=5)  → for 3-layer nodes
          (batch, seq_len=30, features=3)  → for 2-layer nodes (POL4)
  GRU:    hidden_size=32
  Dense:  32 → 16 → 3 (T+15, T+30, T+60 probabilities)
  Output: sigmoid → [0.0, 1.0] per horizon

Auto-trains with synthetic data if model file not found.
No fallback to rule-based — AI is always the active engine.

SIH 2026 · Problem Statement SIH26178 · Qualcomm
═══════════════════════════════════════════════════════════
"""

import os
import logging
import math
import random
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Try importing PyTorch (may not be available on all dev machines) ──
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available — using NumPy-based GRU fallback")


# ═══════════════════════════════════════════════════════════
# GRU MODEL DEFINITION
# ═══════════════════════════════════════════════════════════

if TORCH_AVAILABLE:
    class HazardGRU(nn.Module):
        """
        Lightweight GRU model for disaster trajectory prediction.
        
        Input:  (batch, seq_len, input_size)
        Output: (batch, 3) → predicted probability at T+15, T+30, T+60 min
        """
        
        def __init__(self, input_size: int = 5, hidden_size: int = 32):
            super().__init__()
            self.gru = nn.GRU(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=1,
                batch_first=True,
            )
            self.fc1 = nn.Linear(hidden_size, 16)
            self.relu = nn.ReLU()
            self.dropout = nn.Dropout(0.2)
            self.fc2 = nn.Linear(16, 3)  # 3 outputs: T+15, T+30, T+60
            self.sigmoid = nn.Sigmoid()
        
        def forward(self, x):
            # x: (batch, seq_len, input_size)
            gru_out, _ = self.gru(x)
            # Take the last hidden state
            last_hidden = gru_out[:, -1, :]  # (batch, hidden_size)
            out = self.fc1(last_hidden)
            out = self.relu(out)
            out = self.dropout(out)
            out = self.fc2(out)
            out = self.sigmoid(out)
            return out  # (batch, 3)


# ═══════════════════════════════════════════════════════════
# NUMPY-BASED SIMPLE GRU (for dev machines without PyTorch)
# ═══════════════════════════════════════════════════════════

class SimpleGRUNumpy:
    """
    Minimal GRU implementation using NumPy for environments
    where PyTorch is not installed (development/testing).
    Uses trained weights if available, otherwise random init.
    """

    def __init__(self, input_size: int = 5, hidden_size: int = 32):
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # GRU weights (random initialization — will be replaced by trained weights)
        scale = 1.0 / math.sqrt(hidden_size)
        self.Wz = np.random.randn(input_size + hidden_size, hidden_size).astype(np.float32) * scale
        self.Wr = np.random.randn(input_size + hidden_size, hidden_size).astype(np.float32) * scale
        self.Wh = np.random.randn(input_size + hidden_size, hidden_size).astype(np.float32) * scale
        self.bz = np.zeros(hidden_size, dtype=np.float32)
        self.br = np.zeros(hidden_size, dtype=np.float32)
        self.bh = np.zeros(hidden_size, dtype=np.float32)
        
        # Dense layers
        self.W1 = np.random.randn(hidden_size, 16).astype(np.float32) * scale
        self.b1 = np.zeros(16, dtype=np.float32)
        self.W2 = np.random.randn(16, 3).astype(np.float32) * scale
        self.b2 = np.zeros(3, dtype=np.float32)
    
    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))
    
    def _relu(self, x):
        return np.maximum(0, x)
    
    def predict(self, sequence: np.ndarray) -> np.ndarray:
        """
        Forward pass through the GRU.
        
        Args:
            sequence: (seq_len, input_size) array
        Returns:
            (3,) array — predicted probabilities for T+15, T+30, T+60
        """
        h = np.zeros(self.hidden_size, dtype=np.float32)
        
        for t in range(sequence.shape[0]):
            x = sequence[t]
            combined = np.concatenate([x, h])
            
            z = self._sigmoid(combined @ self.Wz + self.bz)  # Update gate
            r = self._sigmoid(combined @ self.Wr + self.br)  # Reset gate
            
            combined_r = np.concatenate([x, r * h])
            h_tilde = np.tanh(combined_r @ self.Wh + self.bh)  # Candidate
            
            h = (1 - z) * h + z * h_tilde
        
        # Dense layers
        out = self._relu(h @ self.W1 + self.b1)
        out = self._sigmoid(out @ self.W2 + self.b2)
        
        return out


# ═══════════════════════════════════════════════════════════
# SYNTHETIC DATA GENERATOR (for auto-training)
# ═══════════════════════════════════════════════════════════

SEVERITY_MAP = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


def _severity_from_prob(prob: float) -> str:
    """Convert probability to severity label."""
    if prob >= 0.90:
        return "CRITICAL"
    elif prob >= 0.70:
        return "HIGH"
    elif prob >= 0.45:
        return "MEDIUM"
    else:
        return "LOW"


def generate_synthetic_sequences(
    hazard_type: str,
    num_sequences: int = 2000,
    seq_length: int = 30,
    layer_count: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic time-series training data for a hazard type.
    
    Creates realistic sensor anomaly score trajectories including:
      - Normal baseline sequences (no event)
      - Gradual escalation sequences (building disaster)
      - Rapid onset sequences (sudden disaster)
      - False alarm sequences (spike then return to normal)
      - Decay sequences (disaster subsiding)
    
    Args:
        hazard_type: FLOOD, FIRE, LANDSLIDE, or POLLUTION
        num_sequences: number of training sequences
        seq_length: timesteps per sequence
        layer_count: 2 or 3 (determines feature count)
        
    Returns:
        X: (num_sequences, seq_length, features) input array
        Y: (num_sequences, 3) target array — [prob_t15, prob_t30, prob_t60]
    """
    features = 5 if layer_count >= 3 else 3  # l1, l2, l3, combined, rate OR l1, l2, combined
    X = np.zeros((num_sequences, seq_length, features), dtype=np.float32)
    Y = np.zeros((num_sequences, 3), dtype=np.float32)
    
    for i in range(num_sequences):
        scenario = random.choices(
            ["normal", "gradual_rise", "rapid_onset", "false_alarm", "decay", "plateau"],
            weights=[0.25, 0.25, 0.15, 0.15, 0.10, 0.10],
        )[0]
        
        if scenario == "normal":
            # Baseline: low anomaly scores with noise
            base = random.uniform(0.02, 0.15)
            for t in range(seq_length):
                noise = random.gauss(0, 0.03)
                l1 = max(0, min(1, base + noise))
                l2 = max(0, min(1, base + random.gauss(0, 0.03)))
                if layer_count >= 3:
                    l3 = max(0, min(1, base + random.gauss(0, 0.02)))
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3
                    rate = 0
                    X[i, t] = [l1, l2, l3, combined, rate]
                else:
                    combined = 0.55 * l1 + 0.45 * l2
                    X[i, t] = [l1, l2, combined]
            
            # Future: still normal
            Y[i] = [base + random.gauss(0, 0.05)] * 3
            Y[i] = np.clip(Y[i], 0, 1)
            
        elif scenario == "gradual_rise":
            # Slowly escalating disaster
            start = random.uniform(0.05, 0.20)
            peak = random.uniform(0.70, 0.98)
            rise_rate = (peak - start) / (seq_length + 30)  # continues after window
            
            for t in range(seq_length):
                progress = start + rise_rate * t
                l1 = max(0, min(1, progress + random.gauss(0, 0.04)))
                l2 = max(0, min(1, progress * 0.85 + random.gauss(0, 0.05)))
                if layer_count >= 3:
                    l3 = max(0, min(1, progress * 0.70 + random.gauss(0, 0.04)))
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3
                    rate = 1 if rise_rate > 0.01 else (3 if rise_rate > 0.03 else 0)
                    X[i, t] = [l1, l2, l3, combined, rate]
                else:
                    combined = 0.55 * l1 + 0.45 * l2
                    X[i, t] = [l1, l2, combined]
            
            # Future: continues rising
            last_val = start + rise_rate * seq_length
            Y[i, 0] = min(1.0, last_val + rise_rate * 7.5)    # T+15 (~7.5 readings ahead)
            Y[i, 1] = min(1.0, last_val + rise_rate * 15)     # T+30
            Y[i, 2] = min(1.0, last_val + rise_rate * 30)     # T+60
            Y[i] = np.clip(Y[i], 0, 1)
            
        elif scenario == "rapid_onset":
            # Sudden spike — disaster starts fast
            onset = random.randint(seq_length // 3, seq_length - 5)
            peak = random.uniform(0.80, 0.99)
            
            for t in range(seq_length):
                if t < onset:
                    base = random.uniform(0.03, 0.12)
                    l1 = base + random.gauss(0, 0.02)
                    l2 = base + random.gauss(0, 0.02)
                    l3_val = base + random.gauss(0, 0.02)
                    rate = 0
                else:
                    progress = (t - onset) / max(1, (seq_length - onset))
                    l1 = max(0, min(1, progress * peak + random.gauss(0, 0.03)))
                    l2 = max(0, min(1, progress * peak * 0.9 + random.gauss(0, 0.04)))
                    l3_val = max(0, min(1, progress * peak * 0.75 + random.gauss(0, 0.03)))
                    rate = 3  # rapid
                
                if layer_count >= 3:
                    l3 = max(0, min(1, l3_val))
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3
                    X[i, t] = [max(0, l1), max(0, l2), l3, combined, rate]
                else:
                    combined = 0.55 * max(0, l1) + 0.45 * max(0, l2)
                    X[i, t] = [max(0, l1), max(0, l2), combined]
            
            # Future: high probability
            Y[i] = [peak * 0.95, peak * 0.98, peak]
            Y[i] = np.clip(Y[i], 0, 1)
            
        elif scenario == "false_alarm":
            # Spike then return to normal
            spike_start = random.randint(5, seq_length // 2)
            spike_end = spike_start + random.randint(3, 8)
            spike_height = random.uniform(0.45, 0.75)
            
            for t in range(seq_length):
                if spike_start <= t < spike_end:
                    progress = (t - spike_start) / max(1, (spike_end - spike_start))
                    val = spike_height * math.sin(progress * math.pi)
                    l1 = max(0, val + random.gauss(0, 0.03))
                    l2 = max(0, val * 0.6 + random.gauss(0, 0.04))
                    l3_val = max(0, val * 0.3 + random.gauss(0, 0.03))
                    rate = 1
                else:
                    l1 = random.uniform(0.02, 0.12)
                    l2 = random.uniform(0.02, 0.10)
                    l3_val = random.uniform(0.01, 0.08)
                    rate = 0
                
                if layer_count >= 3:
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * min(1, l3_val)
                    X[i, t] = [l1, l2, min(1, l3_val), combined, rate]
                else:
                    combined = 0.55 * l1 + 0.45 * l2
                    X[i, t] = [l1, l2, combined]
            
            # Future: return to low (false alarm resolved)
            Y[i] = [random.uniform(0.05, 0.15)] * 3
            Y[i] = np.clip(Y[i], 0, 1)
            
        elif scenario == "decay":
            # High values decaying to normal
            start_high = random.uniform(0.70, 0.95)
            end_low = random.uniform(0.05, 0.20)
            
            for t in range(seq_length):
                progress = t / seq_length
                val = start_high + (end_low - start_high) * progress
                l1 = max(0, min(1, val + random.gauss(0, 0.03)))
                l2 = max(0, min(1, val * 0.85 + random.gauss(0, 0.04)))
                l3_val = max(0, min(1, val * 0.70 + random.gauss(0, 0.03)))
                rate = 2  # falling
                
                if layer_count >= 3:
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3_val
                    X[i, t] = [l1, l2, l3_val, combined, rate]
                else:
                    combined = 0.55 * l1 + 0.45 * l2
                    X[i, t] = [l1, l2, combined]
            
            # Future: continues decaying
            decay_rate = (start_high - end_low) / seq_length
            final = end_low
            Y[i, 0] = max(0, final - decay_rate * 7.5)
            Y[i, 1] = max(0, final - decay_rate * 15)
            Y[i, 2] = max(0, final - decay_rate * 30)
            Y[i] = np.clip(Y[i], 0, 1)
            
        elif scenario == "plateau":
            # Sustained medium-high level
            level = random.uniform(0.40, 0.80)
            
            for t in range(seq_length):
                l1 = max(0, min(1, level + random.gauss(0, 0.05)))
                l2 = max(0, min(1, level * 0.9 + random.gauss(0, 0.05)))
                l3_val = max(0, min(1, level * 0.75 + random.gauss(0, 0.04)))
                rate = 0  # stable
                
                if layer_count >= 3:
                    combined = 0.50 * l1 + 0.30 * l2 + 0.20 * l3_val
                    X[i, t] = [l1, l2, l3_val, combined, rate]
                else:
                    combined = 0.55 * l1 + 0.45 * l2
                    X[i, t] = [l1, l2, combined]
            
            # Future: stays at same level
            Y[i] = [level + random.gauss(0, 0.05)] * 3
            Y[i] = np.clip(Y[i], 0, 1)
    
    return X, Y


# ═══════════════════════════════════════════════════════════
# GRU PREDICTOR — Main Interface
# ═══════════════════════════════════════════════════════════

class GRUPredictor:
    """
    GRU-based future disaster prediction engine.
    
    Manages per-hazard GRU models. If a model file is missing
    at startup, automatically generates synthetic training data
    and trains the model — no silent fallback to rule-based.
    """

    HAZARD_TYPES = {
        "FLOOD": {"layer_count": 3, "input_size": 5},
        "FIRE": {"layer_count": 3, "input_size": 5},
        "LANDSLIDE": {"layer_count": 3, "input_size": 5},
        "POLLUTION": {"layer_count": 2, "input_size": 3},
    }

    def __init__(self, config: dict = None, node_configs: dict = None):
        self.config = config or {}
        self.node_configs = node_configs or {}
        self.model_dir = self.config.get("model_dir", "data/models")
        self.seq_length = self.config.get("sequence_length", 30)
        self.horizons = self.config.get("prediction_horizons", [15, 30, 60])
        
        # Ensure model directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_dir_abs = os.path.join(base_dir, "jetson", self.model_dir)
        os.makedirs(self.model_dir_abs, exist_ok=True)
        
        # Model storage
        self.models = {}      # hazard_type → model
        self.np_models = {}   # hazard_type → SimpleGRUNumpy (fallback)
        
        # Update HAZARD_TYPES from node configs
        for nid, ncfg in self.node_configs.items():
            ht = ncfg.get("hazard_type", "")
            lc = ncfg.get("layer_count", 3)
            if ht in self.HAZARD_TYPES:
                self.HAZARD_TYPES[ht]["layer_count"] = lc
                self.HAZARD_TYPES[ht]["input_size"] = 5 if lc >= 3 else 3
        
        # Prediction history for accuracy tracking
        self._prediction_history: Dict[str, List[Dict]] = {}
        
        # Load or auto-train models for all hazard types
        self._initialize_models()

    def _get_model_path(self, hazard_type: str) -> str:
        """Get the model file path for a hazard type."""
        return os.path.join(self.model_dir_abs, f"gru_{hazard_type.lower()}.pt")

    def _initialize_models(self):
        """Load existing models or auto-train missing ones."""
        auto_train_cfg = self.config.get("auto_train", {})
        
        for hazard_type, info in self.HAZARD_TYPES.items():
            model_path = self._get_model_path(hazard_type)
            input_size = info["input_size"]
            
            if TORCH_AVAILABLE:
                model = HazardGRU(input_size=input_size, hidden_size=32)
                
                if os.path.exists(model_path):
                    try:
                        state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
                        model.load_state_dict(state_dict)
                        model.eval()
                        self.models[hazard_type] = model
                        logger.info(f"✅ Loaded GRU model for {hazard_type} from {model_path}")
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to load model for {hazard_type}: {e}")
                
                # Model not found — auto-train
                if auto_train_cfg.get("enabled", True):
                    self._auto_train_pytorch(hazard_type, info, auto_train_cfg)
                else:
                    logger.error(f"❌ No model for {hazard_type} and auto-train disabled!")
            else:
                # NumPy fallback — auto-train with simple gradient descent
                np_model_path = model_path.replace(".pt", ".npz")
                if os.path.exists(np_model_path):
                    self.np_models[hazard_type] = self._load_numpy_model(np_model_path, input_size)
                    logger.info(f"✅ Loaded NumPy GRU model for {hazard_type}")
                else:
                    logger.warning(
                        f"⚠️  No pre-trained model found for {hazard_type} — "
                        f"auto-training with synthetic data..."
                    )
                    self._auto_train_numpy(hazard_type, info, auto_train_cfg)

    def _auto_train_pytorch(self, hazard_type: str, info: dict, train_cfg: dict):
        """Auto-train a PyTorch GRU model with synthetic data."""
        logger.warning(
            f"⚠️  No pre-trained model found for {hazard_type} — "
            f"auto-training with synthetic data (~30s)..."
        )
        
        input_size = info["input_size"]
        layer_count = info["layer_count"]
        epochs = train_cfg.get("epochs", 100)
        lr = train_cfg.get("learning_rate", 0.001)
        num_sequences = train_cfg.get("synthetic_sequences", 2000)
        
        # Generate synthetic training data
        X, Y = generate_synthetic_sequences(
            hazard_type, num_sequences, self.seq_length, layer_count
        )
        
        # Split train/val
        split = int(0.85 * len(X))
        X_train, X_val = X[:split], X[split:]
        Y_train, Y_val = Y[:split], Y[split:]
        
        # Convert to tensors
        X_train_t = torch.FloatTensor(X_train)
        Y_train_t = torch.FloatTensor(Y_train)
        X_val_t = torch.FloatTensor(X_val)
        Y_val_t = torch.FloatTensor(Y_val)
        
        # Create model
        model = HazardGRU(input_size=input_size, hidden_size=32)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        # Training loop
        model.train()
        best_val_loss = float("inf")
        batch_size = 64
        
        for epoch in range(epochs):
            # Mini-batch training
            indices = torch.randperm(len(X_train_t))
            total_loss = 0
            batches = 0
            
            for start in range(0, len(indices), batch_size):
                batch_idx = indices[start:start + batch_size]
                batch_x = X_train_t[batch_idx]
                batch_y = Y_train_t[batch_idx]
                
                optimizer.zero_grad()
                pred = model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                batches += 1
            
            # Validation
            if (epoch + 1) % 20 == 0 or epoch == epochs - 1:
                model.eval()
                with torch.no_grad():
                    val_pred = model(X_val_t)
                    val_loss = criterion(val_pred, Y_val_t).item()
                    val_mae = torch.mean(torch.abs(val_pred - Y_val_t)).item()
                model.train()
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                
                if (epoch + 1) % 50 == 0 or epoch == epochs - 1:
                    logger.info(
                        f"  [{hazard_type}] Epoch {epoch+1}/{epochs} — "
                        f"Train Loss: {total_loss/batches:.4f} | "
                        f"Val Loss: {val_loss:.4f} | Val MAE: {val_mae:.4f}"
                    )
        
        # Save model
        model.eval()
        model_path = self._get_model_path(hazard_type)
        torch.save(model.state_dict(), model_path)
        self.models[hazard_type] = model
        
        logger.info(
            f"✅ GRU model trained for {hazard_type} — "
            f"{epochs} epochs, MAE={val_mae:.4f}, saved to {model_path}"
        )

    def _auto_train_numpy(self, hazard_type: str, info: dict, train_cfg: dict):
        """Auto-train using NumPy-based simple model (no PyTorch)."""
        input_size = info["input_size"]
        layer_count = info["layer_count"]
        num_sequences = train_cfg.get("synthetic_sequences", 2000)
        epochs = min(train_cfg.get("epochs", 100), 50)  # Cap for numpy training
        
        # Generate data
        X, Y = generate_synthetic_sequences(
            hazard_type, num_sequences, self.seq_length, layer_count
        )
        
        # Simple approach: train a numpy model with basic gradient descent
        model = SimpleGRUNumpy(input_size=input_size, hidden_size=32)
        
        lr = 0.01
        for epoch in range(epochs):
            total_loss = 0
            for idx in random.sample(range(len(X)), min(100, len(X))):
                pred = model.predict(X[idx])
                error = pred - Y[idx]
                total_loss += np.mean(error ** 2)
                
                # Simple perturbation-based update (no backprop)
                for attr in ['W2', 'b2', 'W1', 'b1']:
                    w = getattr(model, attr)
                    perturbation = np.random.randn(*w.shape).astype(np.float32) * 0.01
                    setattr(model, attr, w - lr * error.mean() * perturbation)
            
            if (epoch + 1) % 25 == 0:
                logger.info(f"  [{hazard_type}] NumPy Epoch {epoch+1}/{epochs} — Loss: {total_loss/100:.4f}")
        
        # Save numpy model
        model_path = self._get_model_path(hazard_type).replace(".pt", ".npz")
        np.savez(model_path,
                 Wz=model.Wz, Wr=model.Wr, Wh=model.Wh,
                 bz=model.bz, br=model.br, bh=model.bh,
                 W1=model.W1, b1=model.b1, W2=model.W2, b2=model.b2)
        self.np_models[hazard_type] = model
        
        logger.info(f"✅ NumPy GRU model trained for {hazard_type} — saved to {model_path}")

    def _load_numpy_model(self, path: str, input_size: int) -> SimpleGRUNumpy:
        """Load a saved NumPy model."""
        data = np.load(path)
        model = SimpleGRUNumpy(input_size=input_size, hidden_size=32)
        for key in ['Wz', 'Wr', 'Wh', 'bz', 'br', 'bh', 'W1', 'b1', 'W2', 'b2']:
            if key in data:
                setattr(model, key, data[key])
        return model

    def _get_hazard_type(self, node_id: str) -> str:
        """Get hazard type for a node ID."""
        ncfg = self.node_configs.get(node_id, {})
        return ncfg.get("hazard_type", "FLOOD")

    def _prepare_input(self, history: List[Dict], hazard_type: str) -> Optional[np.ndarray]:
        """
        Convert recent readings to model input tensor.
        
        Args:
            history: List of reading dicts from TimeSeriesStore
            hazard_type: FLOOD/FIRE/LANDSLIDE/POLLUTION
            
        Returns:
            (seq_length, features) numpy array, or None if insufficient data
        """
        info = self.HAZARD_TYPES.get(hazard_type, {"input_size": 5, "layer_count": 3})
        features = info["input_size"]
        layer_count = info["layer_count"]
        
        if len(history) < 3:
            return None
        
        # Take last seq_length readings (or pad if fewer)
        recent = history[-self.seq_length:]
        sequence = np.zeros((self.seq_length, features), dtype=np.float32)
        
        for t, reading in enumerate(recent):
            offset = self.seq_length - len(recent)
            idx = offset + t
            if idx < 0 or idx >= self.seq_length:
                continue
            
            l1 = float(reading.get("l1_anomaly", 0))
            l2 = float(reading.get("l2_anomaly", 0))
            combined = float(reading.get("combined_score", 0))
            
            if layer_count >= 3:
                l3 = float(reading.get("l3_anomaly", 0))
                rate = float(reading.get("rate_flag", 0))
                sequence[idx] = [l1, l2, l3, combined, rate]
            else:
                sequence[idx] = [l1, l2, combined]
        
        # If we have fewer readings than seq_length, pad beginning with first value
        if len(recent) < self.seq_length:
            pad_end = self.seq_length - len(recent)
            for t in range(pad_end):
                sequence[t] = sequence[pad_end]
        
        return sequence

    def predict_future(self, node_id: str, history: List[Dict]) -> Dict:
        """
        Predict future disaster probability for a node.
        
        Args:
            node_id: Node identifier (FLD1, SLD2, FIR3, POL4)
            history: Recent readings from time-series store
            
        Returns:
            {
                "t15": {"probability": 0.82, "severity": "HIGH"},
                "t30": {"probability": 0.88, "severity": "HIGH"},
                "t60": {"probability": 0.93, "severity": "CRITICAL"},
                "trajectory": "escalating" | "stable" | "declining",
                "confidence": 0.85,
                "model_type": "GRU" | "NumPy-GRU",
            }
        """
        hazard_type = self._get_hazard_type(node_id)
        sequence = self._prepare_input(history, hazard_type)
        
        if sequence is None:
            # Not enough data yet — return neutral predictions
            return {
                "t15": {"probability": 0.0, "severity": "LOW"},
                "t30": {"probability": 0.0, "severity": "LOW"},
                "t60": {"probability": 0.0, "severity": "LOW"},
                "trajectory": "insufficient_data",
                "confidence": 0.0,
                "model_type": "none",
            }
        
        # Run inference
        if hazard_type in self.models and TORCH_AVAILABLE:
            # PyTorch inference
            model = self.models[hazard_type]
            model.eval()
            with torch.no_grad():
                input_tensor = torch.FloatTensor(sequence).unsqueeze(0)  # (1, seq, features)
                output = model(input_tensor).squeeze(0).numpy()  # (3,)
            model_type = "GRU"
        elif hazard_type in self.np_models:
            # NumPy inference
            output = self.np_models[hazard_type].predict(sequence)
            model_type = "NumPy-GRU"
        else:
            logger.error(f"No model available for {hazard_type}!")
            return self._empty_prediction()
        
        # Post-process
        prob_t15 = float(np.clip(output[0], 0, 1))
        prob_t30 = float(np.clip(output[1], 0, 1))
        prob_t60 = float(np.clip(output[2], 0, 1))
        
        # Determine trajectory
        if prob_t60 > prob_t15 + 0.1:
            trajectory = "escalating"
        elif prob_t15 > prob_t60 + 0.1:
            trajectory = "declining"
        else:
            trajectory = "stable"
        
        # Confidence based on data quantity
        data_ratio = min(1.0, len(history) / self.seq_length)
        confidence = round(data_ratio * 0.9, 2)  # Max 0.9 for synthetic-trained model
        
        result = {
            "t15": {"probability": round(prob_t15, 3), "severity": _severity_from_prob(prob_t15)},
            "t30": {"probability": round(prob_t30, 3), "severity": _severity_from_prob(prob_t30)},
            "t60": {"probability": round(prob_t60, 3), "severity": _severity_from_prob(prob_t60)},
            "trajectory": trajectory,
            "confidence": confidence,
            "model_type": model_type,
        }
        
        # Store prediction for accuracy tracking
        if node_id not in self._prediction_history:
            self._prediction_history[node_id] = []
        self._prediction_history[node_id].append({
            "timestamp": datetime.now().isoformat(),
            **result,
        })
        # Keep last 100 predictions
        if len(self._prediction_history[node_id]) > 100:
            self._prediction_history[node_id] = self._prediction_history[node_id][-100:]
        
        return result

    def _empty_prediction(self) -> Dict:
        """Return empty prediction when no model is available."""
        return {
            "t15": {"probability": 0.0, "severity": "LOW"},
            "t30": {"probability": 0.0, "severity": "LOW"},
            "t60": {"probability": 0.0, "severity": "LOW"},
            "trajectory": "no_model",
            "confidence": 0.0,
            "model_type": "none",
        }

    def get_prediction_history(self, node_id: str, limit: int = 50) -> List[Dict]:
        """Get recent prediction history for a node."""
        return self._prediction_history.get(node_id, [])[-limit:]

    def is_trained(self, hazard_type: str) -> bool:
        """Check if a model is trained for a hazard type."""
        return hazard_type in self.models or hazard_type in self.np_models
