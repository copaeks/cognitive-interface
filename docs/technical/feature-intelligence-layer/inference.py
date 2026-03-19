"""
Shadow Intelligence Layer - Edge Inference
===========================================

Lightweight inference engine for intent classification on edge devices.
Supports both Keras and TFLite models.

Author: Cognitive AR Empire 2035 Technical Team
Version: 1.0
"""

import numpy as np
import time
from typing import Tuple, Optional, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
import os

# Try to import TensorFlow, but allow fallback to TFLite only
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Try to import TFLite runtime
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    try:
        from tensorflow import lite as tflite
        TFLITE_AVAILABLE = True
    except ImportError:
        TFLITE_AVAILABLE = False


# =============================================================================
# DATA TYPES
# =============================================================================

class IntentType(Enum):
    """Intent classification categories"""
    HAND = 0
    TOOL = 1
    OTHER = 2
    
    @classmethod
    def from_index(cls, idx: int) -> 'IntentType':
        """Get IntentType from index"""
        for intent in cls:
            if intent.value == idx:
                return intent
        return cls.OTHER


@dataclass
class IntentPrediction:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    probabilities: np.ndarray
    inference_time_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'intent': self.intent.name.lower(),
            'confidence': float(self.confidence),
            'probabilities': self.probabilities.tolist(),
            'inference_time_ms': float(self.inference_time_ms)
        }


# =============================================================================
# PREPROCESSING
# =============================================================================

CONTOUR_POINTS = 64
INPUT_DIM = 2


def preprocess_contour(
    contour: np.ndarray,
    target_points: int = CONTOUR_POINTS,
    normalize: bool = True
) -> np.ndarray:
    """
    Preprocess a contour for model input.
    
    Steps:
    1. Resample to fixed number of points
    2. Normalize coordinates to [-1, 1] range
    3. Ensure correct shape (points, 2)
    
    Parameters:
    -----------
    contour : np.ndarray
        Input contour, shape (N, 2) or (N*2,)
    target_points : int
        Number of points to resample to
    normalize : bool
        Whether to normalize coordinates
        
    Returns:
    --------
    processed : np.ndarray
        Processed contour, shape (target_points, 2)
    """
    # Ensure 2D array
    if contour.ndim == 1:
        contour = contour.reshape(-1, 2)
    
    # Resample to fixed number of points
    n_points = len(contour)
    if n_points != target_points:
        # Linear interpolation
        indices = np.linspace(0, n_points - 1, target_points)
        processed = np.zeros((target_points, 2))
        for i in range(2):
            processed[:, i] = np.interp(indices, np.arange(n_points), contour[:, i])
    else:
        processed = contour.copy()
    
    # Normalize to [-1, 1] range
    if normalize:
        # Center
        centroid = np.mean(processed, axis=0)
        processed = processed - centroid
        
        # Scale to unit bounding box
        max_range = np.max(np.abs(processed))
        if max_range > 0:
            processed = processed / max_range
    
    return processed.astype(np.float32)


def batch_preprocess(contours: List[np.ndarray]) -> np.ndarray:
    """Preprocess a batch of contours"""
    processed = [preprocess_contour(c) for c in contours]
    return np.array(processed)


# =============================================================================
# INFERENCE ENGINE
# =============================================================================

class IntentClassifier:
    """
    Edge inference engine for intent classification.
    Supports Keras (.keras) and TFLite (.tflite) models.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_tflite: bool = False
    ):
        """
        Initialize the classifier.
        
        Parameters:
        -----------
        model_path : str, optional
            Path to model file (.keras or .tflite)
        use_tflite : bool
            Force use of TFLite runtime
        """
        self.model_path = model_path
        self.use_tflite = use_tflite or (model_path and model_path.endswith('.tflite'))
        self.model = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.class_names = ['hand', 'tool', 'other']
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> None:
        """
        Load a model from file.
        
        Parameters:
        -----------
        model_path : str
            Path to model file
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model_path = model_path
        self.use_tflite = model_path.endswith('.tflite')
        
        if self.use_tflite:
            self._load_tflite_model(model_path)
        else:
            self._load_keras_model(model_path)
        
        print(f"Model loaded: {model_path}")
    
    def _load_keras_model(self, model_path: str) -> None:
        """Load Keras model"""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow not available. Use TFLite model instead.")
        
        self.model = keras.models.load_model(model_path)
        self.interpreter = None
    
    def _load_tflite_model(self, model_path: str) -> None:
        """Load TFLite model"""
        if TFLITE_AVAILABLE:
            self.interpreter = tflite.Interpreter(model_path=model_path)
        elif TF_AVAILABLE:
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
        else:
            raise RuntimeError("TFLite runtime not available")
        
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.model = None
    
    def predict(
        self,
        contour: np.ndarray,
        return_dict: bool = False
    ) -> Union[IntentPrediction, Dict]:
        """
        Predict intent from a single contour.
        
        Parameters:
        -----------
        contour : np.ndarray
            Input contour, shape (N, 2) or (N*2,)
        return_dict : bool
            Return result as dictionary instead of dataclass
            
        Returns:
        --------
        prediction : IntentPrediction or dict
            Classification result
        """
        # Preprocess
        processed = preprocess_contour(contour)
        processed = np.expand_dims(processed, axis=0)  # Add batch dimension
        
        # Run inference
        start_time = time.perf_counter()
        
        if self.use_tflite and self.interpreter:
            # TFLite inference
            self.interpreter.set_tensor(self.input_details[0]['index'], processed)
            self.interpreter.invoke()
            probabilities = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        elif self.model:
            # Keras inference
            probabilities = self.model.predict(processed, verbose=0)[0]
        else:
            raise RuntimeError("No model loaded")
        
        inference_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Get prediction
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]
        
        result = IntentPrediction(
            intent=IntentType.from_index(predicted_class),
            confidence=float(confidence),
            probabilities=probabilities,
            inference_time_ms=inference_time
        )
        
        return result.to_dict() if return_dict else result
    
    def predict_batch(
        self,
        contours: List[np.ndarray]
    ) -> List[IntentPrediction]:
        """
        Predict intents for a batch of contours.
        
        Parameters:
        -----------
        contours : List[np.ndarray]
            List of input contours
            
        Returns:
        --------
        predictions : List[IntentPrediction]
            List of classification results
        """
        # Preprocess batch
        processed = batch_preprocess(contours)
        
        # Run inference
        start_time = time.perf_counter()
        
        if self.use_tflite and self.interpreter:
            # TFLite batch inference (may need to loop)
            all_probs = []
            for i in range(len(processed)):
                self.interpreter.set_tensor(
                    self.input_details[0]['index'],
                    np.expand_dims(processed[i], axis=0)
                )
                self.interpreter.invoke()
                probs = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                all_probs.append(probs)
            probabilities = np.array(all_probs)
        elif self.model:
            # Keras batch inference
            probabilities = self.model.predict(processed, verbose=0)
        else:
            raise RuntimeError("No model loaded")
        
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        per_item_time = total_time / len(contours)
        
        # Create results
        results = []
        for i, probs in enumerate(probabilities):
            predicted_class = np.argmax(probs)
            confidence = probs[predicted_class]
            results.append(IntentPrediction(
                intent=IntentType.from_index(predicted_class),
                confidence=float(confidence),
                probabilities=probs,
                inference_time_ms=per_item_time
            ))
        
        return results
    
    def benchmark(
        self,
        n_iterations: int = 100,
        warmup: int = 10
    ) -> Dict:
        """
        Benchmark inference latency.
        
        Parameters:
        -----------
        n_iterations : int
            Number of iterations to benchmark
        warmup : int
            Number of warmup iterations
            
        Returns:
        --------
        results : dict
            Benchmark statistics
        """
        # Generate random test input
        test_contour = np.random.randn(CONTOUR_POINTS, INPUT_DIM).astype(np.float32)
        
        # Warmup
        for _ in range(warmup):
            self.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            self.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        times = np.array(times)
        
        return {
            'mean_ms': float(np.mean(times)),
            'std_ms': float(np.std(times)),
            'min_ms': float(np.min(times)),
            'max_ms': float(np.max(times)),
            'p50_ms': float(np.percentile(times, 50)),
            'p95_ms': float(np.percentile(times, 95)),
            'p99_ms': float(np.percentile(times, 99)),
            'n_iterations': n_iterations
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_classifier(model_path: str) -> IntentClassifier:
    """Load a classifier from model file"""
    return IntentClassifier(model_path)


def predict_intent(
    contour: np.ndarray,
    model_path: str = 'models/intent_classifier.keras'
) -> Dict:
    """
    One-shot intent prediction.
    
    Parameters:
    -----------
    contour : np.ndarray
        Input contour
    model_path : str
        Path to model file
        
    Returns:
    --------
    result : dict
        Prediction result with intent, confidence, probabilities, inference_time_ms
    """
    classifier = IntentClassifier(model_path)
    return classifier.predict(contour, return_dict=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Demo inference"""
    print("=" * 60)
    print("Shadow Intent Classifier - Inference Demo")
    print("=" * 60)
    
    # Generate test contours
    from train import SyntheticDataGenerator
    
    generator = SyntheticDataGenerator()
    
    # Test with each class
    test_cases = [
        ('hand', generator.generate_hand_contour()),
        ('tool', generator.generate_tool_contour()),
        ('other', generator.generate_other_contour())
    ]
    
    # Check for available model
    model_path = 'models/intent_classifier.keras'
    tflite_path = 'models/intent_classifier_int8.tflite'
    
    if os.path.exists(tflite_path):
        print(f"\nUsing TFLite model: {tflite_path}")
        classifier = IntentClassifier(tflite_path)
    elif os.path.exists(model_path):
        print(f"\nUsing Keras model: {model_path}")
        classifier = IntentClassifier(model_path)
    else:
        print(f"\nNo trained model found. Run train.py first.")
        return
    
    # Run predictions
    print("\nPredictions:")
    print("-" * 60)
    
    for true_class, contour in test_cases:
        result = classifier.predict(contour)
        print(f"\nTrue class: {true_class}")
        print(f"  Predicted: {result.intent.name.lower()} (confidence: {result.confidence:.3f})")
        print(f"  Probabilities: hand={result.probabilities[0]:.3f}, "
              f"tool={result.probabilities[1]:.3f}, other={result.probabilities[2]:.3f}")
        print(f"  Inference time: {result.inference_time_ms:.3f} ms")
    
    # Benchmark
    print("\n" + "=" * 60)
    print("Benchmarking inference latency...")
    print("=" * 60)
    
    benchmark_results = classifier.benchmark(n_iterations=100)
    
    print(f"\nLatency Statistics (100 iterations):")
    print(f"  Mean: {benchmark_results['mean_ms']:.3f} ms")
    print(f"  Std:  {benchmark_results['std_ms']:.3f} ms")
    print(f"  Min:  {benchmark_results['min_ms']:.3f} ms")
    print(f"  Max:  {benchmark_results['max_ms']:.3f} ms")
    print(f"  P95:  {benchmark_results['p95_ms']:.3f} ms")
    print(f"  P99:  {benchmark_results['p99_ms']:.3f} ms")
    
    target_ms = 5.0
    print(f"\nTarget latency: {target_ms} ms")
    print(f"Target met: {'✓' if benchmark_results['p95_ms'] < target_ms else '✗'}")


if __name__ == "__main__":
    main()
