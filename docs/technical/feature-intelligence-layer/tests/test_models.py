"""
Unit tests for Shadow Intelligence Layer models.

Tests model architecture, training, and prediction functionality.
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

from models.intent_classifier import (
    IntentClassifier, ModelConfig, create_intent_classifier
)
from models.property_predictor import (
    PropertyPredictor, PropertyModelConfig, create_property_predictor
)


class TestIntentClassifier(unittest.TestCase):
    """Test cases for intent classifier."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = ModelConfig(
            input_shape=(64, 64, 1),
            dropout_rate=0.3,
            use_separable_conv=True
        )
        cls.model = IntentClassifier(cls.config)
    
    def test_model_creation(self):
        """Test model can be created."""
        self.assertIsNotNone(self.model.model)
        self.assertIsNotNone(self.model.config)
    
    def test_model_architecture(self):
        """Test model architecture is correct."""
        # Check input shape
        self.assertEqual(
            self.model.model.input_shape,
            (None, 64, 64, 1)
        )
        
        # Check output shapes
        outputs = self.model.model.outputs
        self.assertEqual(len(outputs), 3)
        
        # Object type output
        self.assertEqual(outputs[0].shape[-1], 3)
        # Grasp state output
        self.assertEqual(outputs[1].shape[-1], 3)
        # Interaction intent output
        self.assertEqual(outputs[2].shape[-1], 3)
    
    def test_model_compilation(self):
        """Test model can be compiled."""
        try:
            self.model.compile()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Model compilation failed: {e}")
    
    def test_prediction_shape(self):
        """Test prediction output shape."""
        self.model.compile()
        
        # Create dummy input
        dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.object_type, ["hand", "tool", "other"])
        self.assertIn(pred.grasp_state, ["open", "closed", "pinching"])
        self.assertIn(pred.interaction_intent, ["pointing", "manipulating", "resting"])
        
        # Check confidence values
        self.assertGreaterEqual(pred.object_confidence, 0.0)
        self.assertLessEqual(pred.object_confidence, 1.0)
        self.assertGreaterEqual(pred.overall_confidence, 0.0)
        self.assertLessEqual(pred.overall_confidence, 1.0)
    
    def test_batch_prediction(self):
        """Test batch prediction."""
        self.model.compile()
        
        # Create batch input
        batch_size = 5
        dummy_input = np.random.rand(batch_size, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), batch_size)
    
    def test_model_parameters(self):
        """Test model parameter count."""
        param_count = self.model.count_parameters()
        
        # Model should be lightweight (< 1M params)
        self.assertLess(param_count, 1_000_000)
        print(f"Intent model parameters: {param_count:,}")
    
    def test_model_save_load(self):
        """Test model save and load."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save model
            save_path = os.path.join(temp_dir, "test_model.keras")
            self.model.save(save_path)
            
            # Check file exists
            self.assertTrue(os.path.exists(save_path))
            
            # Load model
            loaded_model = IntentClassifier.load(save_path)
            
            # Check loaded model works
            self.assertIsNotNone(loaded_model.model)
            
            # Test prediction
            dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
            predictions = loaded_model.predict(dummy_input)
            self.assertEqual(len(predictions), 1)
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
    
    def test_tflite_export(self):
        """Test TFLite export."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Export
            tflite_path = os.path.join(temp_dir, "test_model.tflite")
            self.model.export_tflite(tflite_path, optimize=False)
            
            # Check file exists and has content
            self.assertTrue(os.path.exists(tflite_path))
            self.assertGreater(os.path.getsize(tflite_path), 0)
            
            # Check size is reasonable (< 5MB)
            size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
            self.assertLess(size_mb, 5.0)
            print(f"TFLite model size: {size_mb:.2f} MB")
        
        finally:
            shutil.rmtree(temp_dir)


class TestPropertyPredictor(unittest.TestCase):
    """Test cases for property predictor."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = PropertyModelConfig(
            input_shape=(64, 64, 1),
            dropout_rate=0.25,
            use_separable_conv=True
        )
        cls.model = PropertyPredictor(cls.config)
    
    def test_model_creation(self):
        """Test model can be created."""
        self.assertIsNotNone(self.model.model)
        self.assertIsNotNone(self.model.config)
    
    def test_model_architecture(self):
        """Test model architecture is correct."""
        # Check input shape
        self.assertEqual(
            self.model.model.input_shape,
            (None, 64, 64, 1)
        )
        
        # Check output shapes
        outputs = self.model.model.outputs
        self.assertEqual(len(outputs), 2)
        
        # Material output
        self.assertEqual(outputs[0].shape[-1], 3)
        # Size category output
        self.assertEqual(outputs[1].shape[-1], 3)
    
    def test_prediction_shape(self):
        """Test prediction output shape."""
        self.model.compile()
        
        # Create dummy input
        dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.material, ["rigid", "soft", "liquid"])
        self.assertIn(pred.size_category, ["small", "medium", "large"])
        
        # Check confidence values
        self.assertGreaterEqual(pred.material_confidence, 0.0)
        self.assertLessEqual(pred.material_confidence, 1.0)
        self.assertGreaterEqual(pred.overall_confidence, 0.0)
        self.assertLessEqual(pred.overall_confidence, 1.0)
        
        # Check probability dictionaries
        self.assertEqual(len(pred.material_probabilities), 3)
        self.assertEqual(len(pred.size_probabilities), 3)
    
    def test_model_parameters(self):
        """Test model parameter count."""
        param_count = self.model.count_parameters()
        
        # Model should be lightweight (< 500K params)
        self.assertLess(param_count, 500_000)
        print(f"Property model parameters: {param_count:,}")
    
    def test_model_save_load(self):
        """Test model save and load."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save model
            save_path = os.path.join(temp_dir, "test_property_model.keras")
            self.model.save(save_path)
            
            # Load model
            loaded_model = PropertyPredictor.load(save_path)
            
            # Test prediction
            dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
            predictions = loaded_model.predict(dummy_input)
            self.assertEqual(len(predictions), 1)
        
        finally:
            shutil.rmtree(temp_dir)


class TestModelIntegration(unittest.TestCase):
    """Integration tests for both models."""
    
    def test_models_work_together(self):
        """Test both models can work with same input."""
        # Create models
        intent_model = create_intent_classifier()
        property_model = create_property_predictor()
        
        # Compile
        intent_model.compile()
        property_model.compile()
        
        # Create shared input
        dummy_input = np.random.rand(5, 64, 64, 1).astype(np.float32)
        
        # Run both predictions
        intent_preds = intent_model.predict(dummy_input)
        property_preds = property_model.predict(dummy_input)
        
        # Check outputs match
        self.assertEqual(len(intent_preds), len(property_preds))
        self.assertEqual(len(intent_preds), 5)
    
    def test_model_sizes(self):
        """Test combined model sizes."""
        intent_model = create_intent_classifier()
        property_model = create_property_predictor()
        
        intent_params = intent_model.count_parameters()
        property_params = property_model.count_parameters()
        total_params = intent_params + property_params
        
        # Combined should be < 1.5M params
        self.assertLess(total_params, 1_500_000)
        print(f"\nTotal parameters: {total_params:,}")
        print(f"  Intent: {intent_params:,}")
        print(f"  Property: {property_params:,}")


class TestModelTraining(unittest.TestCase):
    """Tests for model training functionality."""
    
    def test_intent_training(self):
        """Test intent model can be trained."""
        model = create_intent_classifier()
        model.compile()
        
        # Create small synthetic dataset
        n_samples = 50
        X = np.random.rand(n_samples, 64, 64, 1).astype(np.float32)
        
        y = {
            "object_type": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "grasp_state": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "interaction_intent": np.eye(3)[np.random.randint(0, 3, n_samples)]
        }
        
        # Train for a few epochs
        history = model.fit(
            X, y,
            epochs=2,
            batch_size=10,
            verbose=0
        )
        
        # Check history has expected keys
        self.assertIn('loss', history)
        self.assertIn('object_type_accuracy', history)
    
    def test_property_training(self):
        """Test property model can be trained."""
        model = create_property_predictor()
        model.compile()
        
        # Create small synthetic dataset
        n_samples = 50
        X = np.random.rand(n_samples, 64, 64, 1).astype(np.float32)
        
        y = {
            "material": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "size_category": np.eye(3)[np.random.randint(0, 3, n_samples)]
        }
        
        # Train for a few epochs
        history = model.fit(
            X, y,
            epochs=2,
            batch_size=10,
            verbose=0
        )
        
        # Check history has expected keys
        self.assertIn('loss', history)
        self.assertIn('material_accuracy', history)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntentClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestPropertyPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestModelIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestModelTraining))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
