"""
Intelligence API for Shadow Intelligence Layer.

Simple, clean API for intent classification and property prediction.
Designed for easy integration with mobile applications.
"""

from __future__ import annotations

import os
import sys
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.edge_inference import EdgeInferenceEngine, InferenceMode
from models.intent_classifier import IntentPrediction
from models.property_predictor import PropertyPrediction


class ObjectType(Enum):
    """Object type classification."""
    HAND = "hand"
    TOOL = "tool"
    OTHER = "other"


class GraspState(Enum):
    """Hand grasp state."""
    OPEN = "open"
    CLOSED = "closed"
    PINCHING = "pinching"


class InteractionIntent(Enum):
    """Interaction intent."""
    POINTING = "pointing"
    MANIPULATING = "manipulating"
    RESTING = "resting"


class MaterialType(Enum):
    """Material type."""
    RIGID = "rigid"
    SOFT = "soft"
    LIQUID = "liquid"


class SizeCategory(Enum):
    """Size category."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class ShadowIntelligence:
    """
    Complete intelligence result for a shadow observation.
    
    This is the main output format of the intelligence API.
    """
    # Object classification
    object_type: str
    object_confidence: float
    
    # Intent (if object is a hand)
    grasp_state: Optional[str]
    grasp_confidence: Optional[float]
    interaction_intent: Optional[str]
    interaction_confidence: Optional[float]
    
    # Properties
    material: str
    material_confidence: float
    size_category: str
    size_confidence: float
    
    # Overall
    overall_confidence: float
    
    # Performance metrics
    inference_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def is_hand(self) -> bool:
        """Check if detected object is a hand."""
        return self.object_type == "hand"
    
    def is_tool(self) -> bool:
        """Check if detected object is a tool."""
        return self.object_type == "tool"
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        """Check if prediction meets confidence threshold."""
        return self.overall_confidence >= threshold


class IntelligenceAPI:
    """
    Main API for Shadow Intelligence Layer.
    
    Provides a simple interface for:
    - Intent classification
    - Property prediction
    - Batch processing
    - Performance monitoring
    
    Example:
        >>> api = IntelligenceAPI()
        >>> result = api.classify(shadow_data)
        >>> print(f"Detected: {result.object_type}")
    """
    
    def __init__(
        self,
        intent_model_path: Optional[str] = None,
        property_model_path: Optional[str] = None,
        mode: str = "auto",
        num_threads: int = 4
    ) -> None:
        """
        Initialize Intelligence API.
        
        Args:
            intent_model_path: Path to intent classifier TFLite model
            property_model_path: Path to property predictor TFLite model
            mode: Execution mode ('cpu', 'gpu', 'npu', 'auto')
            num_threads: Number of CPU threads for inference
        """
        # Set default model paths
        if intent_model_path is None:
            intent_model_path = self._find_default_model("intent_model.tflite")
        
        if property_model_path is None:
            property_model_path = self._find_default_model("property_model.tflite")
        
        self.intent_model_path = intent_model_path
        self.property_model_path = property_model_path
        
        # Initialize inference engine
        self.engine = EdgeInferenceEngine(
            intent_model_path=intent_model_path,
            property_model_path=property_model_path,
            mode=InferenceMode(mode),
            num_threads=num_threads
        )
        
        # Performance tracking
        self._inference_count = 0
        self._total_inference_time = 0.0
    
    def _find_default_model(self, model_name: str) -> Optional[str]:
        """Find default model in common locations."""
        search_paths = [
            os.path.join("models", "pretrained", model_name),
            os.path.join("..", "models", "pretrained", model_name),
            os.path.join(os.path.dirname(__file__), "..", "models", "pretrained", model_name),
            model_name
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def classify(
        self,
        shadow_data: np.ndarray,
        return_properties: bool = True
    ) -> ShadowIntelligence:
        """
        Classify shadow data and return intelligence result.
        
        Args:
            shadow_data: Shadow observation data (H, W) or (H, W, 1)
            return_properties: Also predict properties
        
        Returns:
            ShadowIntelligence result object
        """
        # Run inference
        result = self.engine.infer(
            shadow_data,
            run_intent=True,
            run_property=return_properties
        )
        
        # Update performance tracking
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        # Build result
        intent = result.intent
        props = result.properties
        
        # Calculate overall confidence
        if intent and props:
            overall_conf = (intent.overall_confidence + props.overall_confidence) / 2
        elif intent:
            overall_conf = intent.overall_confidence
        elif props:
            overall_conf = props.overall_confidence
        else:
            overall_conf = 0.0
        
        return ShadowIntelligence(
            object_type=intent.object_type if intent else "unknown",
            object_confidence=intent.object_confidence if intent else 0.0,
            grasp_state=intent.grasp_state if intent and intent.object_type == "hand" else None,
            grasp_confidence=intent.grasp_confidence if intent and intent.object_type == "hand" else None,
            interaction_intent=intent.interaction_intent if intent and intent.object_type == "hand" else None,
            interaction_confidence=intent.interaction_confidence if intent and intent.object_type == "hand" else None,
            material=props.material if props else "unknown",
            material_confidence=props.material_confidence if props else 0.0,
            size_category=props.size_category if props else "unknown",
            size_confidence=props.size_confidence if props else 0.0,
            overall_confidence=overall_conf,
            inference_time_ms=result.total_time_ms
        )
    
    def classify_batch(
        self,
        shadow_data_batch: np.ndarray,
        return_properties: bool = True
    ) -> List[ShadowIntelligence]:
        """
        Classify a batch of shadow observations.
        
        Args:
            shadow_data_batch: Batch of shadow data (N, H, W) or (N, H, W, 1)
            return_properties: Also predict properties
        
        Returns:
            List of ShadowIntelligence results
        """
        results = []
        
        # Process each sample
        for i in range(len(shadow_data_batch)):
            result = self.classify(shadow_data_batch[i], return_properties)
            results.append(result)
        
        return results
    
    def get_intent(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get only intent classification (faster, lighter).
        
        Args:
            shadow_data: Shadow observation data
        
        Returns:
            Dictionary with intent information
        """
        result = self.engine.infer(
            shadow_data,
            run_intent=True,
            run_property=False
        )
        
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        intent = result.intent
        
        if intent is None:
            return {"error": "Intent classification failed"}
        
        return {
            "object_type": intent.object_type,
            "object_confidence": intent.object_confidence,
            "grasp_state": intent.grasp_state,
            "grasp_confidence": intent.grasp_confidence,
            "interaction_intent": intent.interaction_intent,
            "interaction_confidence": intent.interaction_confidence,
            "inference_time_ms": result.total_time_ms
        }
    
    def get_properties(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get only property prediction (faster, lighter).
        
        Args:
            shadow_data: Shadow observation data
        
        Returns:
            Dictionary with property information
        """
        result = self.engine.infer(
            shadow_data,
            run_intent=False,
            run_property=True
        )
        
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        props = result.properties
        
        if props is None:
            return {"error": "Property prediction failed"}
        
        return {
            "material": props.material,
            "material_confidence": props.material_confidence,
            "material_probabilities": props.material_probabilities,
            "size_category": props.size_category,
            "size_confidence": props.size_confidence,
            "size_probabilities": props.size_probabilities,
            "inference_time_ms": result.total_time_ms
        }
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if self._inference_count == 0:
            return {
                "inference_count": 0,
                "average_inference_time_ms": 0.0,
                "total_inference_time_ms": 0.0
            }
        
        return {
            "inference_count": self._inference_count,
            "average_inference_time_ms": self._total_inference_time / self._inference_count,
            "total_inference_time_ms": self._total_inference_time
        }
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics."""
        self._inference_count = 0
        self._total_inference_time = 0.0
    
    def benchmark(self, num_runs: int = 100) -> Dict[str, float]:
        """
        Run performance benchmark.
        
        Args:
            num_runs: Number of benchmark iterations
        
        Returns:
            Benchmark results
        """
        return self.engine.benchmark(num_runs=num_runs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return self.engine.get_model_info()


# Simple function interface for quick usage
def classify(
    shadow_data: np.ndarray,
    intent_model: Optional[str] = None,
    property_model: Optional[str] = None
) -> ShadowIntelligence:
    """
    Simple classification function.
    
    Args:
        shadow_data: Shadow observation data
        intent_model: Path to intent model (optional)
        property_model: Path to property model (optional)
    
    Returns:
        ShadowIntelligence result
    """
    api = IntelligenceAPI(
        intent_model_path=intent_model,
        property_model_path=property_model
    )
    return api.classify(shadow_data)


def quick_classify(shadow_data: np.ndarray) -> Dict[str, str]:
    """
    Ultra-simple classification returning basic info.
    
    Args:
        shadow_data: Shadow observation data
    
    Returns:
        Simple dictionary with key results
    """
    result = classify(shadow_data)
    
    return {
        "object": result.object_type,
        "confidence": f"{result.overall_confidence:.2%}",
        "material": result.material,
        "size": result.size_category
    }


# Flask/FastAPI integration helpers
def create_api_response(result: ShadowIntelligence) -> Dict[str, Any]:
    """Create API response from intelligence result."""
    return {
        "success": True,
        "data": result.to_dict()
    }


def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create error API response."""
    return {
        "success": False,
        "error": error_message
    }


# Example usage
if __name__ == "__main__":
    # Create dummy shadow data for testing
    dummy_shadow = np.random.rand(64, 64).astype(np.float32)
    
    # Initialize API
    api = IntelligenceAPI()
    
    # Run classification
    result = api.classify(dummy_shadow)
    
    # Print results
    print("Classification Result:")
    print(f"  Object Type: {result.object_type} ({result.object_confidence:.2%})")
    
    if result.is_hand():
        print(f"  Grasp State: {result.grasp_state} ({result.grasp_confidence:.2%})")
        print(f"  Interaction: {result.interaction_intent} ({result.interaction_confidence:.2%})")
    
    print(f"  Material: {result.material} ({result.material_confidence:.2%})")
    print(f"  Size: {result.size_category} ({result.size_confidence:.2%})")
    print(f"  Overall Confidence: {result.overall_confidence:.2%}")
    print(f"  Inference Time: {result.inference_time_ms:.2f} ms")
