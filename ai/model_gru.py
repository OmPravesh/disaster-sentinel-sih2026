try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    HAS_TORCH = False

if HAS_TORCH:
    class DisasterGRUForecaster(nn.Module):
        """
        Gated Recurrent Unit (GRU) Temporal Forecaster for NVIDIA Jetson Orin Nano.
        Takes a sequence of past sensor observations [t - seq_len + 1, ..., t]
        and outputs:
        1. Multi-step future sensor values (Regression Head: e.g. future River Water Level in m, or future Slope Angle in °)
        2. Future Disaster Breach Risk Probability (Classification Head: Sigmoid probability of hazardous breach within 30-60 mins)
        """
        def __init__(self, input_dim, hidden_dim=64, num_layers=2, forecast_steps=5, dropout=0.2):
            super().__init__()
            self.input_dim = input_dim
            self.hidden_dim = hidden_dim
            self.num_layers = num_layers
            self.forecast_steps = forecast_steps

            # 2-layer Gated Recurrent Unit
            self.gru = nn.GRU(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0
            )

            # Regression Head: Projects into future timesteps (5 future steps: +10m, +20m, +30m, +40m, +50m)
            self.reg_head = nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(64, forecast_steps)
            )

            # Hazard Probability Head: Predicts probability of breach within lead time
            self.risk_head = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.ReLU(),
                nn.Linear(32, 1),
                nn.Sigmoid()
            )

        def forward(self, x):
            out, _ = self.gru(x)
            last_step = out[:, -1, :]
            future_vals = self.reg_head(last_step)
            risk_prob = self.risk_head(last_step)
            return future_vals, risk_prob
else:
    class DisasterGRUForecaster:
        pass

