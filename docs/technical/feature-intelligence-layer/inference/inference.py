"""
Edge Inference Engine for Intent Classification
===============================================

Lightweight inference for shadow intent prediction.
Optimized for edge deployment with <5ms latency.

Author: Cognitive AR Empire Technical Team
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# Try to import TensorFlow Lite, fall back to regular TF
try:
    import tflite_runtime.interpreter as tflite
    USE_TFLITE = True
except ImportError:
    import tensorflow as tf
    USE_TFLITE = False


@dataclass
class InferenceConfig:
    """Configuration for edge inference."""
    model_path: str = "models/pretrained/intent_model.tflite"
    n_points: int = 64
    input_dims: int = 3
    num_classes: int = 3
    class_names: Tuple[str, ...] = ('hand', 'tool', 'other')


class EdgeInferenceEngine:
    """
    Edge inference engine for intent classification.
    
    Supports both TFLite (preferred for edge) and regular TensorFlow.
    Optimized for sub-5ms inference on mobile NPUs.
    
    Usage:
        engine = EdgeInferenceEngine()
        result = engine.predict(contour)
        print(result['class'], result['confidence'])
    """
    
    def __init__(self, config: InferenceConfig = None):
        self.config = config or InferenceConfig()
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the TFLite or TensorFlow model."""
        model_path = self.config.model_path
        
        if not model_path.endswith('.tflite'):
            # Try to find TFLite version
            tflite_path = model_path.replace('.keras', '.tflite')
            if tf.io.gfile.exists(tflite_path):
                model_path = tflite_path
        
        if USE_TFLITE and model_path.endswith('.tflite'):
            self._load_tflite(model_path)
        else:
            self._load_tensorflow(model_path)
    
    def _load_tflite(self, model_path: str) -> None:
        """Load TFLite model."""
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Check input shape
        expected_shape = (1, self.config.n_points, self.config.input_dims)
        actual_shape = tuple(self.input_details[0]['shape'])
        
        if actual_shape != expected_shape:
            raise ValueError(
                f"Model input shape {actual_shape} doesn't match "
                f"expected {expected_shape}"
            )
    
    def _load_tensorflow(self, model_path: str) -> None:
        """Load regular TensorFlow model."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from model import IntentClassifier
        
        self.interpreter = IntentClassifier.load(model_path)
        self.input_details = None
        self.output_details = None
    
    def preprocess(self, contour: np.ndarray) -> np.ndarray:
        """
        Preprocess contour for inference.
        
        Args:
            contour: (N, 2+) array of points, may have confidence
            
        Returns:
            (1, 64, 3) normalized array
        """
        # Ensure we have at least 2D points
        if contour.ndim == 1:
            raise ValueError("Contour must be 2D array")
        
        # Resample to fixed number of points
        n_input = len(contour)
        if n_input != self.config.n_points:
            # Linear interpolation
            old_indices = np.linspace(0, n_input - 1, n_input)
            new_indices = np.linspace(0, n_input - 1, self.config.n_points)
            
            resampled = np.zeros((self.config.n_points, contour.shape[1]))
            for dim in range(contour.shape[1]):
                resampled[:, dim] = np.interp(
                    new_indices, old_indices, contour[:, dim]
                )
            contour = resampled
        
        # Add confidence if missing
        if contour.shape[1] == 2:
            confidence = np.ones((len(contour), 1)) * 0.9
            contour = np.concatenate([contour, confidence], axis=1)
        
        # Normalize
        centroid = contour[:, :2].mean(axis=0)
        contour[:, :2] -= centroid
        
        scale = contour[:, :2].std()
        if scale > 0:
            contour[:, :2] /= scale
        
        # Add batch dimension
        return np.expand_dims(contour, axis=0).astype(np.float32)
    
    def predict(self, contour: np.ndarray) -> Dict:
        """
        Predict intent from contour.
        
        Args:
            contour: (N, 2+) contour points
            
        Returns:
            Dictionary with prediction results
        """
        # Preprocess
        input_data = self.preprocess(contour)
        
        # Inference
        if USE_TFLITE and self.input_details is not None:
            # TFLite inference
            self.interpreter.set_tensor(
                self.input_details[0]['index'], input_data
            )
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(
                self.output_details[0]['index']
            )
        else:
            # TensorFlow inference
            predictions = self.interpreter.model.predict(input_data, verbose=0)
        
        # Process output
        probs = predictions[0]
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx])
        
        return {
            'class': self.config.class_names[class_idx],
            'class_index': class_idx,
            'confidence': confidence,
            'probabilities': {
                name: float(prob) 
                for name, prob in zip(self.config.class_names, probs)
            },
            'inference_time_ms': None  # Will be set by benchmark
        }
    
    def benchmark(self, n_iterations: int = 100) -> Dict:
        """
        Benchmark inference latency.
        
        Args:
            n_iterations: Number of benchmark iterations
            
        Returns:
            Benchmark results
        """
        # Generate random test contour
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Warm-up
        for _ in range(10):
            self.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            result = self.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        times = np.array(times)
        
        return {
            'mean_ms': float(np.mean(times)),
            'std_ms': float(np.std(times)),
            'min_ms': float(np.min(times)),
            'max_ms': float(np.max(times)),
            'p99_ms': float(np.percentile(times, 99)),
            'iterations': n_iterations
        }


class BatchInferenceEngine:
    """
    Batch inference for processing multiple contours efficiently.
    """
    
    def __init__(self, config: InferenceConfig = None):
        self.config = config or InferenceConfig()
        self.engine = EdgeInferenceEngine(self.config)
    
    def predict_batch(self, contours: List[np.ndarray]) -> List[Dict]:
        """
        Predict intents for multiple contours.
        
        Args:
            contours: List of contour arrays
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        for contour in contours:
            result = self.engine.predict(contour)
            results.append(result)
        return results
    
    def benchmark_batch(
        self, 
        batch_sizes: List[int] = [1, 5, 10, 20],
        n_iterations: int = 50
    ) -> Dict:
        """
        Benchmark batch inference performance.
        
        Args:
            batch_sizes: List of batch sizes to test
            n_iterations: Iterations per batch size
            
        Returns:
            Benchmark results by batch size
        """
        results = {}
        
        for batch_size in batch_sizes:
            # Generate test batch
            test_contours = [
                np.random.randn(64, 3).astype(np.float32)
                for _ in range(batch_size)
            ]
            
            # Warm-up
            self.predict_batch(test_contours)
            
            # Benchmark
            times = []
            for _ in range(n_iterations):
                start = time.perf_counter()
                self.predict_batch(test_contours)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            
            times = np.array(times)
            results[batch_size] = {
                'total_ms': float(np.mean(times)),
                'per_item_ms': float(np.mean(times) / batch_size),
                'std_ms': float(np.std(times)),
                'p99_ms': float(np.percentile(times, 99))
            }
        
        return results


def create_inference_engine(
    model_path: str = None,
    use_tflite: bool = True
) -> EdgeInferenceEngine:
    """
    Factory function to create inference engine.
    
    Args:
        model_path: Path to model file
        use_tflite: Prefer TFLite if available
        
    Returns:
        Configured EdgeInferenceEngine
    """
    if model_path is None:
        model_path = "models/pretrained/intent_model.tflite"
    
    config = InferenceConfig(model_path=model_path)
    return EdgeInferenceEngine(config)


def main():
    """Demo inference engine."""
    print("=" * 60)
    print("EDGE INFERENCE ENGINE DEMO")
    print("=" * 60)
    
    # Create engine
    print("\n[1] Creating inference engine...")
    engine = create_inference_engine()
    print(f"    Using: {'TFLite' if USE_TFLITE else 'TensorFlow'}")
    
    # Generate test contour (hand-like)
    print("\n[2] Generating test contour...")
    t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    x = 0.05 * np.cos(t) + 0.01 * np.sin(5 * t)
    y = 0.06 * np.sin(t) + 0.005 * np.cos(7 * t)
    confidence = 0.8 + 0.2 * np.random.random(64)
    test_contour = np.column_stack([x, y, confidence])
    
    # Predict
    print("\n[3] Running prediction...")
    result = engine.predict(test_contour)
    
    print(f"    Predicted class: {result['class']}")
    print(f"    Confidence: {result['confidence']:.3f}")
    print("    All probabilities:")
    for name, prob in result['probabilities'].items():
        print(f"      {name}: {prob:.3f}")
    
    # Benchmark
    print("\n[4] Running benchmark (100 iterations)...")
    bench = engine.benchmark(n_iterations=100)
    
    print(f"    Mean latency: {bench['mean_ms']:.3f} ms")
    print(f"    P99 latency: {bench['p99_ms']:.3f} ms")
    print(f"    Min/Max: {bench['min_ms']:.3f} / {bench['max_ms']:.3f} ms")
    
    # Check target
    if bench['p99_ms'] < 5.0:
        print("\n✅ TARGET MET: P99 < 5ms")
    else:
        print(f"\n⚠️  TARGET NOT MET: P99 = {bench['p99_ms']:.2f}ms")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
