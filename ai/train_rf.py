import os
import sys
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pandas as pd

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BASE_DIR)

MODELS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

# Import the preprocessing functions
try:
    from ai.preprocess import (
        load_and_preprocess_fire_data, 
        load_and_preprocess_pollution_data, 
        load_and_preprocess_flood_data,
        load_and_preprocess_landslide_data
    )
except ImportError:
    from preprocess import (
        load_and_preprocess_fire_data, 
        load_and_preprocess_pollution_data, 
        load_and_preprocess_flood_data,
        load_and_preprocess_landslide_data
    )

def train_fire_model():
    print("\n==============================================")
    print("--- [FIR3 Node] Training ML Model for Fire ---")
    print("==============================================")
    
    # 1. Get the prepared data
    result = load_and_preprocess_fire_data()
    if result is None:
        print("[ERROR] Could not load fire data. Check preprocess.py")
        return
        
    X_train, X_test, y_train, y_test = result

    # 2. Initialize the Algorithm
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    print("\nTraining the Random Forest Fire model...")
    model.fit(X_train, y_train)
    print("[OK] Fire Model Training Complete!")

    # 3. Test the Model
    print("\nEvaluating Fire Model on Test Data...")
    predictions = model.predict(X_test)

    # 4. Calculate Metrics
    acc = accuracy_score(y_test, predictions)
    print(f"\n[METRIC] Fire Model Accuracy: {acc * 100:.2f}%")
    
    print("\n[METRIC] Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))
    
    print("\n[METRIC] Detailed Classification Report:")
    print(classification_report(y_test, predictions))

    # 5. Save Fire Model
    save_path = os.path.join(MODELS_DIR, "fire_model.joblib")
    joblib.dump(model, save_path)
    print(f"[SAVED] Fire Model saved to: {save_path}")

def train_pollution_model():
    print("\n=======================================================")
    print("--- [POL4 Node] Training ML Model for Air Quality ---")
    print("=======================================================")
    
    # 1. Load preprocessed sensor data
    result = load_and_preprocess_pollution_data()
    if result is None:
        return
        
    X_train, X_test, y_train, y_test = result

    # 2. Random Forest: 100 decision trees voting on sensor combinations
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    
    print("\nTraining Random Forest model on MQ-135 + GP2Y1010AU0F data...")
    model.fit(X_train, y_train)
    print("[OK] Pollution Model Training Complete!")

    # 3. Evaluation on 20% test data
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"\n[METRIC] Pollution Model Accuracy: {acc * 100:.2f}%")
    
    print("\n[METRIC] Confusion Matrix (Safe vs Warning vs Hazardous):")
    print(confusion_matrix(y_test, predictions))
    
    print("\n[METRIC] Classification Report:")
    print(classification_report(y_test, predictions))

    # 4. Save model to models/ directory
    save_path = os.path.join(MODELS_DIR, "pollution_model.joblib")
    joblib.dump(model, save_path)
    print(f"[SAVED] Pollution Model saved to: {save_path}")

def train_flood_model():
    print("\n=======================================================")
    print("--- [FLD1 Node] Training ML Model for Flood Early Warning ---")
    print("=======================================================")
    
    # 1. Load preprocessed sensor data
    result = load_and_preprocess_flood_data()
    if result is None:
        return
        
    X_train, X_test, y_train, y_test = result

    # 2. Random Forest: 100 decision trees voting on sensor combinations
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    
    print("\nTraining Random Forest model on Ultrasonic + Rain + BME280 data...")
    model.fit(X_train, y_train)
    print("[OK] Flood Model Training Complete!")

    # 3. Evaluation on 20% test data
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"\n[METRIC] Flood Model Accuracy: {acc * 100:.2f}%")
    
    print("\n[METRIC] Confusion Matrix (Safe vs Warning vs Hazardous):")
    print(confusion_matrix(y_test, predictions))
    
    print("\n[METRIC] Classification Report:")
    print(classification_report(y_test, predictions))

    # 4. Save model to models/ directory
    save_path = os.path.join(MODELS_DIR, "flood_model.joblib")
    joblib.dump(model, save_path)
    print(f"[SAVED] Flood Model saved to: {save_path}")

def train_landslide_model():
    print("\n===========================================================")
    print("--- [SLD2 Node] Training ML Model for Landslide Warning ---")
    print("===========================================================")
    
    # 1. Load preprocessed sensor data
    result = load_and_preprocess_landslide_data()
    if result is None:
        return
        
    X_train, X_test, y_train, y_test = result

    # 2. Random Forest: 100 decision trees voting on sensor combinations
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    
    print("\nTraining Random Forest model on MPU6050 + Soil Moisture + BME280 data...")
    model.fit(X_train, y_train)
    print("[OK] Landslide Model Training Complete!")

    # 3. Evaluation on 20% test data
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"\n[METRIC] Landslide Model Accuracy: {acc * 100:.2f}%")
    
    print("\n[METRIC] Confusion Matrix (Safe vs Hazardous):")
    print(confusion_matrix(y_test, predictions))
    
    print("\n[METRIC] Classification Report:")
    print(classification_report(y_test, predictions))

    # 4. Save model to models/ directory
    save_path = os.path.join(MODELS_DIR, "landslide_model.joblib")
    joblib.dump(model, save_path)
    print(f"[SAVED] Landslide Model saved to: {save_path}")

if __name__ == "__main__":
    train_fire_model()
    train_pollution_model()
    train_flood_model()
    train_landslide_model()