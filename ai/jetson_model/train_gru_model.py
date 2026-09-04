"""
═══════════════════════════════════════════════════════════
DISASTER SENTINEL — GRU Model Training Script
═══════════════════════════════════════════════════════════

Trains PyTorch GRU time-series models for disaster prediction:
  - FLOOD (3 layers, 5 features)
  - FIRE (3 layers, 5 features)
  - LANDSLIDE (3 layers, 5 features)
  - POLLUTION (2 layers, 3 features)

Generates synthetic scenario data and exports trained .pt model weights
to jetson/data/models/.

SIH 2026 · Problem Statement SIH26178 · Qualcomm
═══════════════════════════════════════════════════════════
"""

import os
import sys
import argparse
import logging
import torch
import torch.nn as nn
import numpy as np

# Add jetson directory to path to import engine
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
JETSON_DIR = os.path.join(PROJECT_ROOT, "jetson")
sys.path.insert(0, JETSON_DIR)

from engine.ai_predictor import HazardGRU, generate_synthetic_sequences

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HAZARDS = {
    "FLOOD": {"layer_count": 3, "input_size": 5},
    "FIRE": {"layer_count": 3, "input_size": 5},
    "LANDSLIDE": {"layer_count": 3, "input_size": 5},
    "POLLUTION": {"layer_count": 2, "input_size": 3},
}

def train_hazard_model(
    hazard_type: str,
    output_dir: str,
    epochs: int = 100,
    batch_size: int = 64,
    lr: float = 0.001,
    num_sequences: int = 2500,
    seq_length: int = 30,
) -> str:
    info = HAZARDS[hazard_type]
    layer_count = info["layer_count"]
    input_size = info["input_size"]

    logger.info(f"Generating synthetic training data for {hazard_type} (layers={layer_count}, features={input_size})...")
    X, Y = generate_synthetic_sequences(hazard_type, num_sequences=num_sequences, seq_length=seq_length, layer_count=layer_count)

    # Train/Val split
    split = int(0.85 * len(X))
    X_train, X_val = X[:split], X[split:]
    Y_train, Y_val = Y[:split], Y[split:]

    X_train_t = torch.FloatTensor(X_train)
    Y_train_t = torch.FloatTensor(Y_train)
    X_val_t = torch.FloatTensor(X_val)
    Y_val_t = torch.FloatTensor(Y_val)

    model = HazardGRU(input_size=input_size, hidden_size=32)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    logger.info(f"Training GRU model for {hazard_type} over {epochs} epochs...")

    for epoch in range(epochs):
        model.train()
        indices = torch.randperm(len(X_train_t))
        total_loss = 0.0
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

        if (epoch + 1) % 20 == 0 or epoch == epochs - 1:
            model.eval()
            with torch.no_grad():
                val_pred = model(X_val_t)
                val_loss = criterion(val_pred, Y_val_t).item()
                val_mae = torch.mean(torch.abs(val_pred - Y_val_t)).item()

            if val_loss < best_val_loss:
                best_val_loss = val_loss

            if (epoch + 1) % 50 == 0 or epoch == epochs - 1:
                logger.info(
                    f"[{hazard_type}] Epoch {epoch+1:3d}/{epochs} | "
                    f"Train Loss: {total_loss/batches:.4f} | Val Loss: {val_loss:.4f} | Val MAE: {val_mae:.4f}"
                )

    os.makedirs(output_dir, exist_ok=True)
    model_filename = f"gru_{hazard_type.lower()}.pt"
    save_path = os.path.join(output_dir, model_filename)

    model.eval()
    torch.save(model.state_dict(), save_path)
    logger.info(f"✅ Saved trained model to {save_path} (Final Val MAE: {val_mae:.4f})\n")

    return save_path

def main():
    parser = argparse.ArgumentParser(description="Train GRU models for Disaster Sentinel hazards")
    parser.add_argument("--hazard", choices=["FLOOD", "FIRE", "LANDSLIDE", "POLLUTION", "ALL"], default="ALL", help="Hazard type to train")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--output-dir", type=str, default=os.path.join(JETSON_DIR, "data", "models"), help="Output directory for .pt model files")
    args = parser.parse_args()

    hazards_to_train = list(HAZARDS.keys()) if args.hazard == "ALL" else [args.hazard]

    logger.info(f"Starting training run for: {', '.join(hazards_to_train)}")
    for ht in hazards_to_train:
        train_hazard_model(ht, output_dir=args.output_dir, epochs=args.epochs)

    logger.info("🎉 All model training complete!")

if __name__ == "__main__":
    main()
