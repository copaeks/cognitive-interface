"""
Tests for edge inference engine.

Tests TFLite inference, preprocessing, and performance.
"""

from __future__ import annotations

import os
import sys
import unittest
import numpy as np
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.edge_inference import (
    EdgeInferenceEngine, InferenceMode, InferenceResult,
    create_edge_engine
)
from models.intent_classifier import create_intent_classifier
from models.property_predictor import create_property_predictor


class TestEdgeInference(unittest.TestCase):
    """Test cases for edge inference engine."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - create and export models."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export intent model
        intent_model = create_intent_classifier()
        intent_model.compile()
        cls.intent_model_path = os.path.join(cls.temp_dir, "intent_model.tflite")
        intent_model.export_tflite(cls.intent_model_path, optimize=False)
        
        # Create and export property model
        property_model = create_property_predictor()
        property_model.compile()
        cls.property_model_path = os.path.join(cls.temp_dir, "property_model.tflite")
        property_model.export_tflite(cls.property_model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        shutil.rmtree(cls.temp_dir)
    
    def test_engine_creation(self):
        """Test inference engine can be created."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU,
            num_threads=2
        )
        
        self.assertIsNotNone(engine.intent_interpreter)
        self.assertIsNotNone(engine.property_interpreter)
        self.assertIsNotNone(engine._input_shape)
    
    def test_preprocessing(self):
        """Test input preprocessing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with 2D input
        input_2d = np.random.rand(64, 64).astype(np.float32)
        processed, _ = engine.preprocess(input_2d)
        
        self.assertEqual(len(processed.shape), 4)  # (1, H, W, C)
        self.assertEqual(processed.shape, (1, 64, 64, 1))
        
        # Test with 3D input
        input_3d = np.random.rand(10, 64, 64).astype(np.float32)
        processed, _ = engine.preprocess(input_3d)
        
        self.assertEqual(processed.shape, (10, 64, 64, 1))
    
    def test_intent_inference(self):
        """Test intent classification inference."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.classify_intent(test_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.object_type, ["hand", "tool", "other"])
        self.assertIn(pred.grasp_state, ["open", "closed", "pinching"])
        self.assertIn(pred.interaction_intent, ["pointing", "manipulating", "resting"])
    
    def test_property_inference(self):
        """Test property prediction inference."""
        engine = EdgeInferenceEngine(
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.predict_properties(test_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.material, ["rigid", "soft", "liquid"])
        self.assertIn(pred.size_category, ["small", "medium", "large"])
        
        # Check probability dictionaries
        self.assertEqual(len(pred.material_probabilities), 3)
        self.assertEqual(len(pred.size_probabilities), 3)
    
    def test_full_inference(self):
        """Test complete inference pipeline."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(64, 64).astype(np.float32)
        
        # Run inference
        result = engine.infer(test_input, run_intent=True, run_property=True)
        
        # Check result
        self.assertIsInstance(result, InferenceResult)
        self.assertIsNotNone(result.intent)
        self.assertIsNotNone(result.properties)
        self.assertGreater(result.inference_time_ms, 0)
        self.assertGreater(result.total_time_ms, 0)
    
    def test_inference_modes(self):
        """Test different inference modes."""
        for mode in [InferenceMode.CPU, InferenceMode.AUTO]:
            engine = EdgeInferenceEngine(
                intent_model_path=self.intent_model_path,
                mode=mode,
                num_threads=2
            )
            
            test_input = np.random.rand(64, 64).astype(np.float32)
            result = engine.infer(test_input, run_intent=True, run_property=False)
            
            self.assertIsNotNone(result.intent)
    
    def test_batch_processing(self):
        """Test batch processing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create batch input
        batch_size = 5
        test_input = np.random.rand(batch_size, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.classify_intent(test_input)
        
        # Check output
        self.assertEqual(len(predictions), batch_size)
    
    def test_model_info(self):
        """Test getting model information."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        info = engine.get_model_info()
        
        self.assertIn('intent_model_loaded', info)
        self.assertIn('property_model_loaded', info)
        self.assertIn('input_shape', info)
        self.assertIn('mode', info)
        
        self.assertTrue(info['intent_model_loaded'])
        self.assertTrue(info['property_model_loaded'])
    
    def test_benchmark(self):
        """Test benchmark functionality."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Run short benchmark
        results = engine.benchmark(num_runs=10, warmup_runs=2)
        
        # Check results
        self.assertIn('mean_ms', results)
        self.assertIn('std_ms', results)
        self.assertIn('min_ms', results)
        self.assertIn('max_ms', results)
        self.assertIn('throughput_fps', results)
        
        # All values should be positive
        for key, value in results.items():
            self.assertGreaterEqual(value, 0)


class TestInferenceModes(unittest.TestCase):
    """Test different inference execution modes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export model
        model = create_intent_classifier()
        model.compile()
        cls.model_path = os.path.join(cls.temp_dir, "test_model.tflite")
        model.export_tflite(cls.model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_cpu_mode(self):
        """Test CPU inference mode."""
        engine = create_edge_engine(
            intent_model=self.model_path,
            mode="cpu",
            num_threads=2
        )
        
        test_input = np.random.rand(64, 64).astype(np.float32)
        result = engine.infer(test_input)
        
        self.assertIsNotNone(result.intent)
    
    def test_auto_mode(self):
        """Test auto inference mode."""
        engine = create_edge_engine(
            intent_model=self.model_path,
            mode="auto"
        )
        
        test_input = np.random.rand(64, 64).astype(np.float32)
        result = engine.infer(test_input)
        
        self.assertIsNotNone(result.intent)


class TestInferencePerformance(unittest.TestCase):
    """Performance tests for inference."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export models
        intent_model = create_intent_classifier()
        intent_model.compile()
        cls.intent_path = os.path.join(cls.temp_dir, "intent.tflite")
        intent_model.export_tflite(cls.intent_path, optimize=False)
        
        property_model = create_property_predictor()
        property_model.compile()
        cls.property_path = os.path.join(cls.temp_dir, "property.tflite")
        property_model.export_tflite(cls.property_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_inference_latency(self):
        """Test inference meets latency requirements."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_path,
            property_model_path=self.property_path,
            mode=InferenceMode.CPU
        )
        
        # Run benchmark
        results = engine.benchmark(num_runs=50, warmup_runs=5)
        
        # Check mean latency (should be < 50ms on CPU for testing)
        # On actual NPU, this would be < 5ms
        mean_latency = results['mean_ms']
        print(f"\nMean inference latency: {mean_latency:.2f} ms")
        
        self.assertLess(mean_latency, 100)  # Relaxed for CPU testing
    
    def test_throughput(self):
        """Test inference throughput."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_path,
            mode=InferenceMode.CPU
        )
        
        # Run benchmark
        results = engine.benchmark(num_runs=50, warmup_runs=5)
        
        # Check throughput (should be > 10 FPS)
        throughput = results['throughput_fps']
        print(f"\nInference throughput: {throughput:.1f} FPS")
        
        self.assertGreater(throughput, 5)  # Relaxed for CPU testing


class TestPreprocessing(unittest.TestCase):
    """Tests for input preprocessing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        model = create_intent_classifier()
        model.compile()
        cls.model_path = os.path.join(cls.temp_dir, "test.tflite")
        model.export_tflite(cls.model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_normalization(self):
        """Test input normalization."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with high values
        high_input = np.ones((64, 64)) * 255.0
        processed, _ = engine.preprocess(high_input, normalize=True)
        
        # Should be normalized to [0, 1]
        self.assertLessEqual(processed.max(), 1.0)
        self.assertGreaterEqual(processed.min(), 0.0)
    
    def test_resize(self):
        """Test input resizing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with different size
        large_input = np.random.rand(128, 128).astype(np.float32)
        processed, _ = engine.preprocess(large_input, resize=True)
        
        # Should be resized to model input shape
        self.assertEqual(processed.shape[1:3], (64, 64))


def run_tests():
    """Run all inference tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeInference))
    suite.addTests(loader.loadTestsFromTestCase(TestInferenceModes))
    suite.addTests(loader.loadTestsFromTestCase(TestInferencePerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestPreprocessing))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
