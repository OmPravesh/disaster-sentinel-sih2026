import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(os.path.join(DATA_DIR, "fire"), exist_ok=True)

np.random.seed(42)
n_samples = 1000

# Normal ambient conditions (70% of data)
n_normal = 700
temp_normal = np.random.uniform(20.0, 35.0, n_normal)
humidity_normal = np.random.uniform(40.0, 75.0, n_normal)
pressure_normal = np.random.uniform(1005.0, 1025.0, n_normal) 
smoke_normal = np.random.uniform(80.0, 200.0, n_normal)
flame_normal = np.zeros(n_normal, dtype=int)
label_normal = np.zeros(n_normal, dtype=int)

# Fire conditions (30% of data)
n_fire = 300
temp_fire = np.random.uniform(45.0, 85.0, n_fire)
humidity_fire = np.random.uniform(10.0, 30.0, n_fire)
pressure_fire = np.random.uniform(995.0, 1010.0, n_fire) 
smoke_fire = np.random.uniform(350.0, 900.0, n_fire)
flame_fire = np.random.choice([0, 1], size=n_fire, p=[0.1, 0.9])
label_fire = np.ones(n_fire, dtype=int)

# Combine all rows
df = pd.DataFrame({
    "temperature": np.concatenate([temp_normal, temp_fire]),
    "humidity": np.concatenate([humidity_normal, humidity_fire]),
    "pressure": np.concatenate([pressure_normal, pressure_fire]),
    "smoke": np.concatenate([smoke_normal, smoke_fire]),
    "flame_detected": np.concatenate([flame_normal, flame_fire]),
    "fire_alert": np.concatenate([label_normal, label_fire]),
})

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df["temperature"] = df["temperature"].round(2)
df["humidity"] = df["humidity"].round(2)
df["pressure"] = df["pressure"].round(2)
df["smoke"] = df["smoke"].round(2)

output_path = os.path.join(DATA_DIR, "fire", "fire_sensor_data.csv")
df.to_csv(output_path, index=False)

print(f"✅ BME280 Dataset successfully created at: {output_path}")
print(df.head())