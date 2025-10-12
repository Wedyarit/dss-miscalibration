import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from typing import Tuple, Optional
import pickle
import os

class CalibrationWrapper:
    """Wrapper for different calibration methods"""
    
    def __init__(self, calibration_type: str = "platt"):
        self.calibration_type = calibration_type
        self.calibrator = None
        self.base_model = LogisticRegression(random_state=42, max_iter=1000)
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit the calibration model"""
        if self.calibration_type == "platt":
            self.calibrator = CalibratedClassifierCV(
                self.base_model, 
                method='sigmoid', 
                cv=3
            )
            self.calibrator.fit(X, y)
            
        elif self.calibration_type == "isotonic":
            self.calibrator = CalibratedClassifierCV(
                self.base_model, 
                method='isotonic', 
                cv=3
            )
            self.calibrator.fit(X, y)
            
        elif self.calibration_type == "none":
            self.calibrator = self.base_model
            self.calibrator.fit(X, y)
            
        else:
            raise ValueError(f"Unknown calibration type: {self.calibration_type}")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities"""
        if self.calibration_type == "none":
            # For uncalibrated model, return probabilities for positive class only
            proba = self.calibrator.predict_proba(X)
            return proba[:, 1] if proba.shape[1] > 1 else proba.flatten()
        else:
            proba = self.calibrator.predict_proba(X)
            return proba[:, 1] if proba.shape[1] > 1 else proba.flatten()
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Predict binary labels"""
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

def save_model(model: CalibrationWrapper, model_path: str):
    """Save trained model to disk"""
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

def load_model(model_path: str) -> Optional[CalibrationWrapper]:
    """Load trained model from disk"""
    if not os.path.exists(model_path):
        return None
    
    try:
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def calibrate_model(X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray,
                   calibration_type: str = "platt") -> Tuple[CalibrationWrapper, dict]:
    """Train and calibrate a model"""
    
    # Create and train calibration wrapper
    model = CalibrationWrapper(calibration_type)
    model.fit(X_train, y_train)
    
    # Evaluate on validation set
    y_val_pred = model.predict_proba(X_val)
    
    # Calculate metrics
    from app.ml.metrics import calculate_all_metrics
    metrics = calculate_all_metrics(y_val, y_val_pred)
    
    return model, metrics
