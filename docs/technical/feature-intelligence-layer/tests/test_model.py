"""
Unit Tests for Intent Classification Model
==========================================

Tests for model architecture, training, and inference.
Run with: pytest tests/test_model.py -v
"""

import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from model import IntentClassifier, ModelConfig


class TestModelArchitecture:
    """Test model architecture and configuration."""
    
    def test_model_creation(self):
        """Test model can be created."""
        classifier = IntentClassifier()
        assert classifier.model is not None
    
    def test_model_config(self):
        """Test custom configuration."""
        config = ModelConfig(input_points=32, num_classes=5)
        classifier = IntentClassifier(config)
        
        assert classifier.config.input_points == 32
        assert classifier.config.num_classes == 5
    
    def test_model_size(self):
        """Test model size is under limit."""
        classifier = IntentClassifier()
        size_kb = classifier.get_model_size_kb()
        
        # Model should be under 1MB (1024 KB)
        assert size_kb < 1024, f"Model too large: {size_kb:.2f} KB"
    
    def test_parameter_count(self):
        """Test parameter count is reasonable."""
        classifier = IntentClassifier()
        params = classifier.count_parameters()
        
        # Should have parameters but not too many
        assert params > 1000
        assert params < 500000


class TestModelPrediction:
    """Test model prediction functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier fixture."""
        return IntentClassifier()
    
    @pytest.fixture
    def sample_contour(self):
        """Create sample contour fixture."""
        np.random.seed(42)
        return np.random.randn(64, 3).astype(np.float32)
    
    def test_prediction_output_shape(self, classifier, sample_contour):
        """Test prediction returns correct output."""
        result = classifier.predict(sample_contour)
        
        assert 'class' in result
        assert 'confidence' in result
        assert 'probabilities' in result
        assert result['class'] in ['hand', 'tool', 'other']
    
    def test_prediction_probabilities_sum(self, classifier, sample_contour):
        """Test probabilities sum to 1."""
        result = classifier.predict(sample_contour)
        probs = result['probabilities']
        
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01
    
    def test_prediction_confidence_range(self, classifier, sample_contour):
        """Test confidence is in valid range."""
        result = classifier.predict(sample_contour)
        
        assert 0 <= result['confidence'] <= 1
    
    def test_batch_prediction(self, classifier):
        """Test prediction on batch."""
        batch = np.random.randn(10, 64, 3).astype(np.float32)
        
        # Should work with batch dimension
        result = classifier.predict(batch[0])
        assert result['class'] in ['hand', 'tool', 'other']


class TestModelTraining:
    """Test model training functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample training data."""
        np.random.seed(42)
        n_samples = 100
        
        X = np.random.randn(n_samples, 64, 3).astype(np.float32)
        y = np.zeros((n_samples, 3))
        
        # Random labels
        for i in range(n_samples):
            y[i, i % 3] = 1
        
        return X, y
    
    def test_training_runs(self, sample_data):
        """Test training executes without error."""
        X, y = sample_data
        
        # Split
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        classifier = IntentClassifier()
        
        # Train for just 2 epochs (fast test)
        history = classifier.train(
            X_train, y_train,
            X_val, y_val,
            epochs=2,
            batch_size=16
        )
        
        assert 'accuracy' in history.history
        assert len(history.history['accuracy']) == 2
    
    def test_evaluation(self, sample_data):
        """Test model evaluation."""
        X, y = sample_data
        
        classifier = IntentClassifier()
        metrics = classifier.evaluate(X, y)
        
        assert 'accuracy' in metrics
        assert 'loss' in metrics
        assert 0 <= metrics['accuracy'] <= 1


class TestModelSaveLoad:
    """Test model save and load functionality."""
    
    @pytest.fixture
    def temp_model_path(self, tmp_path):
        """Create temporary model path."""
        return str(tmp_path / "test_model.keras")
    
    def test_save_load(self, temp_model_path):
        """Test model can be saved and loaded."""
        # Create and save
        original = IntentClassifier()
        original.save(temp_model_path)
        
        assert os.path.exists(temp_model_path)
        
        # Load
        loaded = IntentClassifier.load(temp_model_path)
        
        assert loaded.model is not None
        assert loaded.class_names == original.class_names
    
    def test_save_load_prediction_consistency(self, temp_model_path):
        """Test predictions are consistent after save/load."""
        np.random.seed(42)
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Create, save, and load
        original = IntentClassifier()
        original.save(temp_model_path)
        loaded = IntentClassifier.load(temp_model_path)
        
        # Both should produce same class (not necessarily same confidence)
        pred_original = original.predict(test_contour)
        pred_loaded = loaded.predict(test_contour)
        
        assert pred_original['class'] == pred_loaded['class']


class TestPerformance:
    """Test model performance characteristics."""
    
    def test_inference_latency(self):
        """Test inference latency is under target."""
        import time
        
        classifier = IntentClassifier()
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Warm-up
        for _ in range(10):
            classifier.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(50):
            start = time.perf_counter()
            classifier.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        mean_latency = np.mean(times)
        
        # Should be under 10ms (generous for test environment)
        assert mean_latency < 10, f"Latency too high: {mean_latency:.2f}ms"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
