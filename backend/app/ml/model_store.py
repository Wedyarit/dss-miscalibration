import os
import json
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime

class ModelStore:
    """Simple model storage and retrieval"""
    
    def __init__(self, base_path: Optional[str] = None):
        # Use temp directory in Docker, or provided path
        if base_path is None:
            # Check if we're in Docker (read-only /app)
            if os.path.exists('/app') and not os.access('/app', os.W_OK):
                self.base_path = tempfile.mkdtemp(prefix='dss_models_')
            else:
                self.base_path = "/app/data"
        else:
            self.base_path = base_path
        
        try:
            os.makedirs(self.base_path, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create model directory {self.base_path}: {e}")
            # Fallback to temp directory
            self.base_path = tempfile.mkdtemp(prefix='dss_models_')
            os.makedirs(self.base_path, exist_ok=True)
    
    def save_model_info(self, model_id: str, info: Dict[str, Any]) -> bool:
        """Save model metadata"""
        try:
            info_path = os.path.join(self.base_path, f"model_{model_id}_info.json")
            with open(info_path, 'w') as f:
                json.dump(info, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving model info: {e}")
            return False
    
    def load_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Load model metadata"""
        try:
            info_path = os.path.join(self.base_path, f"model_{model_id}_info.json")
            if not os.path.exists(info_path):
                return None
            
            with open(info_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading model info: {e}")
            return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        models = []
        try:
            for filename in os.listdir(self.base_path):
                if filename.startswith("model_") and filename.endswith("_info.json"):
                    model_id = filename.replace("model_", "").replace("_info.json", "")
                    info = self.load_model_info(model_id)
                    if info:
                        models.append({
                            "model_id": model_id,
                            **info
                        })
        except Exception as e:
            print(f"Error listing models: {e}")
        
        return sorted(models, key=lambda x: x.get('trained_at', ''), reverse=True)
    
    def get_latest_model_path(self) -> Optional[str]:
        """Get path to the latest model file"""
        models = self.list_models()
        if not models:
            return None
        
        latest_model_id = models[0]['model_id']
        model_path = os.path.join(self.base_path, f"model_{latest_model_id}.pkl")
        
        return model_path if os.path.exists(model_path) else None
    
    def cleanup_old_models(self, keep_last: int = 5) -> int:
        """Remove old model files, keeping only the most recent ones"""
        models = self.list_models()
        removed_count = 0
        
        if len(models) <= keep_last:
            return 0
        
        models_to_remove = models[keep_last:]
        
        for model_info in models_to_remove:
            model_id = model_info['model_id']
            
            # Remove model file
            model_path = os.path.join(self.base_path, f"model_{model_id}.pkl")
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing model file {model_path}: {e}")
            
            # Remove info file
            info_path = os.path.join(self.base_path, f"model_{model_id}_info.json")
            if os.path.exists(info_path):
                try:
                    os.remove(info_path)
                except Exception as e:
                    print(f"Error removing info file {info_path}: {e}")
        
        return removed_count
