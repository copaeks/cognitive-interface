"""
Edge Inference Engine for Shadow Intelligence Layer.

Optimized inference for mobile NPUs using TensorFlow Lite.
Supports both intent classification and property prediction.
"""

from __future__ import annotations

import os
import sys
import numpy as np
import tensorflow as tf
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.intent_classifier import IntentPrediction
from models.property_predictor import PropertyPrediction


class InferenceMode(Enum):
    """Inference execution mode."""
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"  # Neural Processing Unit (e.g., Hexagon DSP)
    AUTO = "auto"


@dataclass
class InferenceResult:
    """Result from edge inference."""
    intent: Optional[IntentPrediction]
    properties: Optional[PropertyPrediction]
    inference_time_ms: float
    preprocessing_time_ms: float
    total_time_ms: float


class EdgeInferenceEngine:
    """
    Optimized edge inference engine for shadow intelligence.
    
    Features:
    - TFLite interpreter with delegate support
    - Batch processing for efficiency
    - Input preprocessing pipeline
    - Performance monitoring
    """
    
    def __init__(
        self,
        intent_model_path: Optional[str] = None,
        property_model_path: Optional[str] = None,
        mode: InferenceMode = InferenceMode.AUTO,
        num_threads: int = 4,
        enable_profiling: bool = False
    ) -> None:
        """
        Initialize edge inference engine.
        
        Args:
            intent_model_path: Path to intent classifier TFLite model
            property_model_path: Path to property predictor TFLite model
            mode: Inference execution mode
            num_threads: Number of CPU threads
            enable_profiling: Enable detailed profiling
        """
        self.intent_model_path = intent_model_path
        self.property_model_path = property_model_path
        self.mode = mode
        self.num_threads = num_threads
        self.enable_profiling = enable_profiling
        
        self.intent_interpreter: Optional[tf.lite.Interpreter] = None
        self.property_interpreter: Optional[tf.lite.Interpreter] = None
        
        self._input_shape: Optional[Tuple[int, ...]] = None
        self._preprocessing_pipeline: List[Callable] = []
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load TFLite models with appropriate delegates."""
        # Load intent classifier
        if self.intent_model_path and os.path.exists(self.intent_model_path):
            print(f"Loading intent model: {self.intent_model_path}")
            
            delegates = self._get_delegates()
            
            self.intent_interpreter = tf.lite.Interpreter(
                model_path=self.intent_model_path,
                experimental_delegates=delegates if delegates else None,
                num_threads=self.num_threads
            )
            self.intent_interpreter.allocate_tensors()
            
            # Cache input shape
            input_details = self.intent_interpreter.get_input_details()
            self._input_shape = tuple(input_details[0]['shape'][1:])
            
            print(f"  Input shape: {self._input_shape}")
            print(f"  Delegates: {[d.__class__.__name__ for d in delegates] if delegates else 'None'}")
        
        # Load property predictor
        if self.property_model_path and os.path.exists(self.property_model_path):
            print(f"Loading property model: {self.property_model_path}")
            
            delegates = self._get_delegates()
            
            self.property_interpreter = tf.lite.Interpreter(
                model_path=self.property_model_path,
                experimental_delegates=delegates if delegates else None,
                num_threads=self.num_threads
            )
            self.property_interpreter.allocate_tensors()
            
            if self._input_shape is None:
                input_details = self.property_interpreter.get_input_details()
                self._input_shape = tuple(input_details[0]['shape'][1:])
            
            print(f"  Input shape: {self._input_shape}")
    
    def _get_delegates(self) -> List[tf.lite.experimental.Delegate]:
        """Get appropriate delegates for the execution mode."""
        delegates = []
        
        if self.mode == InferenceMode.GPU:
            try:
                gpu_delegate = tf.lite.experimental.load_delegate('libgpu_delegate.so')
                delegates.append(gpu_delegate)
            except Exception as e:
                print(f"  Warning: GPU delegate not available: {e}")
        
        elif self.mode == InferenceMode.NPU:
            # Try Hexagon delegate for Qualcomm DSP
            try:
                hexagon_delegate = tf.lite.experimental.load_delegate(
                    'libhexagon_delegate.so',
                    {'inference_priority': 'fp16'}
                )
                delegates.append(hexagon_delegate)
            except Exception as e:
                print(f"  Warning: Hexagon delegate not available: {e}")
            
            # Try NNAPI delegate for Android NPU
            try:
                from tensorflow.lite.python.interpreter import load_delegate
                nnapi_delegate = load_delegate('libnnapi_delegate.so')
                delegates.append(nnapi_delegate)
            except Exception as e:
                print(f"  Warning: NNAPI delegate not available: {e}")
        
        elif self.mode == InferenceMode.AUTO:
            # Try all available delegates
            for delegate_name in ['libnnapi_delegate.so', 'libgpu_delegate.so']:
                try:
                    from tensorflow.lite.python.interpreter import load_delegate
                    delegate = load_delegate(delegate_name)
                    delegates.append(delegate)
                    break  # Use first available
                except:
                    continue
        
        return delegates
    
    def preprocess(
        self,
        shadow_data: np.ndarray,
        normalize: bool = True,
        resize: bool = True
    ) -> np.ndarray:
        """
        Preprocess shadow data for inference.
        
        Args:
            shadow_data: Input shadow data (H, W) or (N, H, W)
            normalize: Normalize to [0, 1]
            resize: Resize to model input shape
        
        Returns:
            Preprocessed data ready for inference
        """
        start_time = time.perf_counter()
        
        # Ensure correct shape
        if len(shadow_data.shape) == 2:
            shadow_data = np.expand_dims(shadow_data, axis=0)
        
        # Add channel dimension if needed
        if len(shadow_data.shape) == 3:
            shadow_data = np.expand_dims(shadow_data, axis=-1)
        
        # Resize if needed
        if resize and self._input_shape is not None:
            target_h, target_w = self._input_shape[:2]
            if shadow_data.shape[1:3] != (target_h, target_w):
                shadow_data = tf.image.resize(
                    shadow_data,
                    [target_h, target_w],
                    method='bilinear'
                ).numpy()
        
        # Normalize
        if normalize:
            if shadow_data.max() > 1.0:
                shadow_data = shadow_data / 255.0
            shadow_data = shadow_data.astype(np.float32)
        
        preprocessing_time = (time.perf_counter() - start_time) * 1000
        
        return shadow_data, preprocessing_time
    
    def classify_intent(
        self,
        shadow_data: np.ndarray
    ) -> List[IntentPrediction]:
        """
        Classify intent from shadow data.
        
        Args:
            shadow_data: Preprocessed shadow data
        
        Returns:
            List of IntentPrediction objects
        """
        if self.intent_interpreter is None:
            raise RuntimeError("Intent model not loaded")
        
        # Get interpreter details
        input_details = self.intent_interpreter.get_input_details()
        output_details = self.intent_interpreter.get_output_details()
        
        # Ensure correct dtype
        input_dtype = input_details[0]['dtype']
        if input_dtype == np.int8:
            # Quantized model - convert to int8
            scale, zero_point = input_details[0]['quantization']
            shadow_data = (shadow_data / scale + zero_point).astype(np.int8)
        
        # Run inference
        self.intent_interpreter.set_tensor(input_details[0]['index'], shadow_data)
        self.intent_interpreter.invoke()
        
        # Get outputs
        outputs = []
        for output_detail in output_details:
            output = self.intent_interpreter.get_tensor(output_detail['index'])
            
            # Dequantize if needed
            if output_detail['dtype'] == np.int8:
                scale, zero_point = output_detail['quantization']
                output = (output.astype(np.float32) - zero_point) * scale
            
            outputs.append(output)
        
        # Convert to predictions
        object_pred, grasp_pred, interaction_pred = outputs
        
        predictions = []
        for i in range(len(shadow_data)):
            obj_idx = np.argmax(object_pred[i])
            grasp_idx = np.argmax(grasp_pred[i])
            interaction_idx = np.argmax(interaction_pred[i])
            
            pred = IntentPrediction(
                object_type=["hand", "tool", "other"][obj_idx],
                object_confidence=float(object_pred[i][obj_idx]),
                grasp_state=["open", "closed", "pinching"][grasp_idx],
                grasp_confidence=float(grasp_pred[i][grasp_idx]),
                interaction_intent=["pointing", "manipulating", "resting"][interaction_idx],
                interaction_confidence=float(interaction_pred[i][interaction_idx]),
                overall_confidence=float(
                    object_pred[i][obj_idx] * 
                    grasp_pred[i][grasp_idx] * 
                    interaction_pred[i][interaction_idx]
                ),
                raw_logits={
                    "object_type": object_pred[i],
                    "grasp_state": grasp_pred[i],
                    "interaction_intent": interaction_pred[i]
                }
            )
            predictions.append(pred)
        
        return predictions
    
    def predict_properties(
        self,
        shadow_data: np.ndarray
    ) -> List[PropertyPrediction]:
        """
        Predict properties from shadow data.
        
        Args:
            shadow_data: Preprocessed shadow data
        
        Returns:
            List of PropertyPrediction objects
        """
        if self.property_interpreter is None:
            raise RuntimeError("Property model not loaded")
        
        # Get interpreter details
        input_details = self.property_interpreter.get_input_details()
        output_details = self.property_interpreter.get_output_details()
        
        # Ensure correct dtype
        input_dtype = input_details[0]['dtype']
        if input_dtype == np.int8:
            scale, zero_point = input_details[0]['quantization']
            shadow_data = (shadow_data / scale + zero_point).astype(np.int8)
        
        # Run inference
        self.property_interpreter.set_tensor(input_details[0]['index'], shadow_data)
        self.property_interpreter.invoke()
        
        # Get outputs
        outputs = []
        for output_detail in output_details:
            output = self.property_interpreter.get_tensor(output_detail['index'])
            
            # Dequantize if needed
            if output_detail['dtype'] == np.int8:
                scale, zero_point = output_detail['quantization']
                output = (output.astype(np.float32) - zero_point) * scale
            
            outputs.append(output)
        
        # Convert to predictions
        material_pred, size_pred = outputs
        
        predictions = []
        materials = ["rigid", "soft", "liquid"]
        size_categories = ["small", "medium", "large"]
        
        for i in range(len(shadow_data)):
            mat_idx = np.argmax(material_pred[i])
            size_idx = np.argmax(size_pred[i])
            
            mat_probs = {
                materials[j]: float(material_pred[i][j])
                for j in range(len(materials))
            }
            size_probs = {
                size_categories[j]: float(size_pred[i][j])
                for j in range(len(size_categories))
            }
            
            pred = PropertyPrediction(
                material=materials[mat_idx],
                material_confidence=float(material_pred[i][mat_idx]),
                size_category=size_categories[size_idx],
                size_confidence=float(size_pred[i][size_idx]),
                material_probabilities=mat_probs,
                size_probabilities=size_probs,
                overall_confidence=float(
                    material_pred[i][mat_idx] * size_pred[i][size_idx]
                )
            )
            predictions.append(pred)
        
        return predictions
    
    def infer(
        self,
        shadow_data: np.ndarray,
        run_intent: bool = True,
        run_property: bool = True
    ) -> InferenceResult:
        """
        Run complete inference pipeline.
        
        Args:
            shadow_data: Raw shadow data
            run_intent: Run intent classification
            run_property: Run property prediction
        
        Returns:
            InferenceResult with all predictions
        """
        total_start = time.perf_counter()
        
        # Preprocess
        processed_data, preprocessing_time = self.preprocess(shadow_data)
        
        # Run intent classification
        intent_start = time.perf_counter()
        intent_result = None
        if run_intent and self.intent_interpreter is not None:
            intent_result = self.classify_intent(processed_data)[0]
        intent_time = (time.perf_counter() - intent_start) * 1000
        
        # Run property prediction
        property_start = time.perf_counter()
        property_result = None
        if run_property and self.property_interpreter is not None:
            property_result = self.predict_properties(processed_data)[0]
        property_time = (time.perf_counter() - property_start) * 1000
        
        total_time = (time.perf_counter() - total_start) * 1000
        inference_time = intent_time + property_time
        
        return InferenceResult(
            intent=intent_result,
            properties=property_result,
            inference_time_ms=inference_time,
            preprocessing_time_ms=preprocessing_time,
            total_time_ms=total_time
        )
    
    def benchmark(
        self,
        num_runs: int = 100,
        warmup_runs: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark inference performance.
        
        Args:
            num_runs: Number of benchmark runs
            warmup_runs: Number of warmup runs
        
        Returns:
            Dictionary with benchmark results
        """
        if self._input_shape is None:
            raise RuntimeError("Models not loaded")
        
        # Create dummy input
        dummy_input = np.random.rand(1, *self._input_shape).astype(np.float32)
        
        # Warmup
        print(f"Warming up ({warmup_runs} runs)...")
        for _ in range(warmup_runs):
            self.infer(dummy_input)
        
        # Benchmark
        print(f"Benchmarking ({num_runs} runs)...")
        times = []
        
        for _ in range(num_runs):
            result = self.infer(dummy_input)
            times.append(result.total_time_ms)
        
        results = {
            'mean_ms': np.mean(times),
            'std_ms': np.std(times),
            'min_ms': np.min(times),
            'max_ms': np.max(times),
            'p50_ms': np.percentile(times, 50),
            'p95_ms': np.percentile(times, 95),
            'p99_ms': np.percentile(times, 99),
            'throughput_fps': 1000 / np.mean(times)
        }
        
        print("\nBenchmark Results:")
        print(f"  Mean: {results['mean_ms']:.2f} ms")
        print(f"  Std:  {results['std_ms']:.2f} ms")
        print(f"  Min:  {results['min_ms']:.2f} ms")
        print(f"  Max:  {results['max_ms']:.2f} ms")
        print(f"  P95:  {results['p95_ms']:.2f} ms")
        print(f"  P99:  {results['p99_ms']:.2f} ms")
        print(f"  Throughput: {results['throughput_fps']:.1f} FPS")
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        info = {
            'intent_model_loaded': self.intent_interpreter is not None,
            'property_model_loaded': self.property_interpreter is not None,
            'input_shape': self._input_shape,
            'mode': self.mode.value,
            'num_threads': self.num_threads
        }
        
        if self.intent_interpreter:
            input_details = self.intent_interpreter.get_input_details()
            output_details = self.intent_interpreter.get_output_details()
            
            info['intent_input'] = {
                'shape': input_details[0]['shape'].tolist(),
                'dtype': str(input_details[0]['dtype']),
                'quantization': input_details[0]['quantization']
            }
            info['intent_outputs'] = [
                {
                    'shape': o['shape'].tolist(),
                    'dtype': str(o['dtype']),
                    'quantization': o['quantization']
                }
                for o in output_details
            ]
        
        return info


def create_edge_engine(
    intent_model: Optional[str] = None,
    property_model: Optional[str] = None,
    mode: str = "auto",
    num_threads: int = 4
) -> EdgeInferenceEngine:
    """Factory function to create edge inference engine."""
    inference_mode = InferenceMode(mode)
    return EdgeInferenceEngine(
        intent_model_path=intent_model,
        property_model_path=property_model,
        mode=inference_mode,
        num_threads=num_threads
    )
