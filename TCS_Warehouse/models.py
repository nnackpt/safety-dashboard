from ultralytics import YOLO
import torch
from config import (
    PERSON_MODEL_PATH, PPE_MODEL_PATH, CLASSIFICATION_MODEL_PATH,
    OBSTACLE_MODEL_PATH, ENABLE_OBSTACLE_DETECTION,
    DEVICE, USE_HALF_PRECISION
)

class ModelManager:
    """Manages loading and inference for all YOLO models"""
    
    def __init__(self):
        self.person_model = None
        self.ppe_model = None
        self.classification_model = None
        self.obstacle_model = None
        
        self._load_models()
    
    def _load_model(self, model_path, model_name):
        """Load a single YOLO model"""
        try:
            model = YOLO(str(model_path))
            model.to(DEVICE)
            
            if DEVICE == 'cuda' and USE_HALF_PRECISION:
                model.model.half()
            
            print(f"✅ {model_name} model loaded from {model_path}")
            print(f"📋 Classes: {model.names}")
            return model
        except Exception as e:
            print(f"❌ Error loading {model_name} model: {e}")
            return None
    
    def _load_models(self):
        """Load all required models"""
        print("\n" + "="*60)
        print("🚀 Loading Models")
        print("="*60)
        
        # Load Person Detection Model
        self.person_model = self._load_model(PERSON_MODEL_PATH, "Person Detection")
        
        # Load PPE Detection Model
        self.ppe_model = self._load_model(PPE_MODEL_PATH, "PPE Detection")
        
        # Load Classification Model
        self.classification_model = self._load_model(CLASSIFICATION_MODEL_PATH, "Classification")
        
        if ENABLE_OBSTACLE_DETECTION:
            self.obstacle_model = self._load_model(OBSTACLE_MODEL_PATH, "Obstacle Detection (YOLO11)")
        else:
            print("⚠️ Obstacle detection is disabled")
        
        print("="*60 + "\n")
    
    def detect_persons(self, image, conf_threshold=0.5):
        """
        Detect persons and forklifts in image
        
        Args:
            image: Input image
            conf_threshold: Confidence threshold
            
        Returns:
            YOLO results object
        """
        if self.person_model is None:
            return None
        
        results = self.person_model(
            image,
            device=DEVICE,
            verbose=False,
            half=USE_HALF_PRECISION,
            conf=conf_threshold,
            imgsz=640
        )
        return results
    
    def detect_ppe(self, image, conf_threshold=0.5):
        if self.ppe_model is None:
            return None
        
        results = self.ppe_model(
            image,
            device=DEVICE,
            verbose=False,
            half=USE_HALF_PRECISION,
            conf=conf_threshold
        )
        return results
    
    def classify_ppe(self, crop_image):
        """
        Classify PPE item from cropped image
        
        Args:
            crop_image: Cropped image of PPE item
            
        Returns:
            tuple: (class_name, confidence) or (None, 0.0) if failed
        """
        if self.classification_model is None:
            return None, 0.0
        
        try:
            results = self.classification_model(
                crop_image,
                device=DEVICE,
                verbose=False
            )
            
            if len(results) > 0 and len(results[0].probs) > 0:
                probs = results[0].probs
                top1_idx = probs.top1
                top1_conf = probs.top1conf.item()
                class_name = results[0].names[top1_idx]
                
                return class_name, top1_conf
            
            return None, 0.0
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return None, 0.0
    
    def detect_obstacles(self, image, conf_threshold=0.5):
        """
        Detect obstacles in image using YOLO11
        
        Args:
            image: Input image
            conf_threshold: Confidence threshold
            
        Returns:
            YOLO results object
        """
        if self.obstacle_model is None:
            return None
        
        results = self.obstacle_model(
            image,
            device=DEVICE,
            verbose=False,
            half=USE_HALF_PRECISION,
            conf=conf_threshold
        )
        return results
    
    def is_ready(self):
        """Check if all required models are loaded"""
        required_models = (
            self.person_model is not None and 
            self.ppe_model is not None and 
            self.classification_model is not None
        )
        
        if ENABLE_OBSTACLE_DETECTION and self.obstacle_model is None:
            print("⚠️ Warning: Obstacle detection enabled but model not loaded")
        
        return required_models


# Global model manager instance
model_manager = ModelManager()