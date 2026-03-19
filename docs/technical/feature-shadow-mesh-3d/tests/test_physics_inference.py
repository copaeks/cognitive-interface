"""
Unit Tests for Physics Inference
================================

Comprehensive test suite for lightweight physics inference engine.

Run with: pytest test_physics_inference.py -v
"""

from __future__ import annotations

import numpy as np
import pytest
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from physics_inference import (
    MaterialType, PhysicsProperties, PhysicsInferenceEngine,
    ShadowFeatures, MiniMLP, ActivationFunction,
    benchmark_physics_inference
)


class TestActivationFunctions:
    """Tests for activation functions."""
    
    def test_relu(self):
        """Test ReLU activation."""
        x = np.array([-1.0, 0.0, 1.0, 2.0], dtype=np.float32)
        result = ActivationFunction.relu(x)
        
        expected = np.array([0.0, 0.0, 1.0, 2.0], dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_leaky_relu(self):
        """Test Leaky ReLU activation."""
        x = np.array([-1.0, 0.0, 1.0], dtype=np.float32)
        result = ActivationFunction.leaky_relu(x, alpha=0.1)
        
        assert result[0] == pytest.approx(-0.1, abs=1e-5)
        assert result[1] == 0.0
        assert result[2] == 1.0
    
    def test_sigmoid(self):
        """Test sigmoid activation."""
        x = np.array([0.0], dtype=np.float32)
        result = ActivationFunction.sigmoid(x)
        
        assert result[0] == pytest.approx(0.5, abs=1e-5)
    
    def test_tanh(self):
        """Test tanh activation."""
        x = np.array([0.0], dtype=np.float32)
        result = ActivationFunction.tanh(x)
        
        assert result[0] == pytest.approx(0.0, abs=1e-5)
    
    def test_softmax(self):
        """Test softmax activation."""
        x = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        result = ActivationFunction.softmax(x)
        
        # Should sum to 1
        assert pytest.approx(result.sum(), abs=1e-5) == 1.0
        # All equal inputs -> equal outputs
        np.testing.assert_array_almost_equal(result, [1/3, 1/3, 1/3])


class TestMiniMLP:
    """Tests for minimal MLP implementation."""
    
    def test_initialization(self):
        """Test MLP initialization."""
        mlp = MiniMLP(
            input_dim=10,
            hidden_dims=[32, 16],
            output_dim=5,
            activation='relu'
        )
        
        assert mlp.input_dim == 10
        assert mlp.hidden_dims == [32, 16]
        assert mlp.output_dim == 5
    
    def test_forward_pass(self):
        """Test forward pass."""
        mlp = MiniMLP(
            input_dim=5,
            hidden_dims=[10],
            output_dim=2,
            activation='relu'
        )
        
        x = np.random.randn(5).astype(np.float32)
        output = mlp.predict(x)
        
        assert output.shape == (1, 2)
    
    def test_batch_forward(self):
        """Test batch forward pass."""
        mlp = MiniMLP(
            input_dim=5,
            hidden_dims=[10],
            output_dim=2,
        )
        
        batch_size = 10
        x = np.random.randn(batch_size, 5).astype(np.float32)
        output = mlp.predict(x)
        
        assert output.shape == (batch_size, 2)
    
    def test_parameter_count(self):
        """Test parameter counting."""
        mlp = MiniMLP(
            input_dim=10,
            hidden_dims=[20, 10],
            output_dim=5,
        )
        
        # Expected: (10*20 + 20) + (20*10 + 10) + (10*5 + 5) = 220 + 210 + 55 = 485
        expected = (10 * 20 + 20) + (20 * 10 + 10) + (10 * 5 + 5)
        assert mlp.count_parameters() == expected
    
    def test_parameter_save_load(self):
        """Test saving and loading parameters."""
        mlp1 = MiniMLP(input_dim=5, hidden_dims=[10], output_dim=2)
        params = mlp1.get_parameters()
        
        mlp2 = MiniMLP(input_dim=5, hidden_dims=[10], output_dim=2)
        mlp2.set_parameters(params)
        
        # Test that both produce same output
        x = np.random.randn(5).astype(np.float32)
        out1 = mlp1.predict(x)
        out2 = mlp2.predict(x)
        
        np.testing.assert_array_almost_equal(out1, out2)


class TestShadowFeatures:
    """Tests for shadow feature extraction."""
    
    def test_from_contour_circle(self):
        """Test feature extraction from circular contour."""
        theta = np.linspace(0, 2 * np.pi, 32, endpoint=False)
        radius = 0.05
        contour = np.column_stack([
            radius * np.cos(theta),
            radius * np.sin(theta)
        ]).astype(np.float32)
        
        features = ShadowFeatures.from_contour(contour)
        
        # Circle should have high circularity
        assert features.circularity > 0.9
        
        # Circle should have aspect ratio close to 1
        assert abs(features.aspect_ratio - 1.0) < 0.1
        
        # Circle should be convex
        assert features.convexity > 0.95
    
    def test_from_contour_square(self):
        """Test feature extraction from square contour."""
        contour = np.array([
            [-0.05, -0.05], [0.05, -0.05],
            [0.05, 0.05], [-0.05, 0.05]
        ], dtype=np.float32)
        
        features = ShadowFeatures.from_contour(contour)
        
        # Square should have lower circularity than circle
        assert features.circularity < 0.9
        
        # Square should still be convex
        assert features.convexity > 0.9
    
    def test_empty_contour(self):
        """Test handling of empty contour."""
        contour = np.zeros((0, 2), dtype=np.float32)
        
        features = ShadowFeatures.from_contour(contour)
        
        # Should return default features
        assert features.area == 0.0
        assert features.perimeter == 0.0
    
    def test_small_contour(self):
        """Test handling of very small contour."""
        contour = np.array([[0, 0], [0.01, 0]], dtype=np.float32)
        
        features = ShadowFeatures.from_contour(contour)
        
        # Should handle gracefully
        assert features.area >= 0.0
    
    def test_feature_vector(self):
        """Test feature vector conversion."""
        features = ShadowFeatures(
            area=1.0, perimeter=2.0, circularity=0.8,
            aspect_ratio=1.2, convexity=0.9,
            deformation_rate=0.1, motion_stability=0.8,
            shadow_contrast=0.7, edge_sharpness=0.6,
            estimated_thickness=0.05, surface_roughness=0.3,
        )
        
        vector = features.to_vector()
        
        assert len(vector) == 11
        assert vector[0] == 1.0  # area
        assert vector[1] == 2.0  # perimeter


class TestPhysicsInferenceEngine:
    """Tests for physics inference engine."""
    
    @pytest.fixture
    def engine(self):
        """Create inference engine fixture."""
        return PhysicsInferenceEngine()
    
    @pytest.fixture
    def rigid_features(self):
        """Create features for rigid object."""
        return ShadowFeatures(
            area=0.00785,
            perimeter=0.314,
            circularity=1.0,
            aspect_ratio=1.0,
            convexity=1.0,
            deformation_rate=0.0,
            motion_stability=1.0,
            shadow_contrast=0.9,
            edge_sharpness=0.95,
            estimated_thickness=0.1,
            surface_roughness=0.1,
        )
    
    @pytest.fixture
    def soft_features(self):
        """Create features for soft object."""
        return ShadowFeatures(
            area=0.01,
            perimeter=0.4,
            circularity=0.7,
            aspect_ratio=1.2,
            convexity=0.9,
            deformation_rate=0.05,
            motion_stability=0.7,
            shadow_contrast=0.7,
            edge_sharpness=0.6,
            estimated_thickness=0.08,
            surface_roughness=0.4,
        )
    
    def test_rigid_object_inference(self, engine, rigid_features):
        """Test inference for rigid object."""
        volume = 0.001  # 1 liter
        
        props = engine.infer_properties(rigid_features, volume)
        
        # Should classify as rigid
        assert props.rigidity > 0.5
        
        # Should have reasonable density
        assert 100 < props.density < 25000
        
        # Should have reasonable mass
        assert props.mass > 0
        
        # Young's modulus should be high for rigid
        assert props.youngs_modulus > 1e9
    
    def test_soft_object_inference(self, engine, soft_features):
        """Test inference for soft object."""
        volume = 0.001
        
        props = engine.infer_properties(soft_features, volume)
        
        # Should have lower rigidity
        assert props.rigidity < 0.8
        
        # Young's modulus should be lower
        assert props.youngs_modulus < 50e9
    
    def test_volume_mass_relationship(self, engine, rigid_features):
        """Test that mass scales with volume."""
        volume1 = 0.001
        volume2 = 0.002
        
        props1 = engine.infer_properties(rigid_features, volume1)
        props2 = engine.infer_properties(rigid_features, volume2)
        
        # Density should be similar
        assert pytest.approx(props1.density, rel=0.1) == props2.density
        
        # Mass should scale with volume
        mass_ratio = props2.mass / props1.mass
        assert pytest.approx(mass_ratio, rel=0.1) == 2.0
    
    def test_confidence_range(self, engine, rigid_features):
        """Test that confidence is in valid range."""
        props = engine.infer_properties(rigid_features, 0.001)
        
        assert 0.0 <= props.confidence <= 1.0
    
    def test_inference_timing(self, engine, rigid_features):
        """Test that inference meets timing requirements."""
        import time
        
        n_iterations = 1000
        start = time.perf_counter()
        
        for _ in range(n_iterations):
            props = engine.infer_properties(rigid_features, 0.001)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_time = elapsed_ms / n_iterations
        
        # Should be under 5ms
        assert avg_time < 5.0, f"Inference too slow: {avg_time:.3f}ms"
    
    def test_physics_properties_serialization(self, engine, rigid_features):
        """Test serialization of physics properties."""
        props = engine.infer_properties(rigid_features, 0.001)
        
        # Convert to dict and back
        data = props.to_dict()
        props2 = PhysicsProperties.from_dict(data)
        
        assert props.material_type == props2.material_type
        assert pytest.approx(props.rigidity) == props2.rigidity
        assert pytest.approx(props.density) == props2.density
        assert pytest.approx(props.mass) == props2.mass


class TestMaterialTypeClassification:
    """Tests for material type classification."""
    
    @pytest.fixture
    def engine(self):
        return PhysicsInferenceEngine()
    
    def test_rigid_solid_classification(self, engine):
        """Test classification of rigid solid."""
        features = ShadowFeatures(
            area=0.01, perimeter=0.35, circularity=0.95,
            aspect_ratio=1.0, convexity=1.0,
            deformation_rate=0.0, motion_stability=1.0,
            shadow_contrast=0.9, edge_sharpness=0.9,
            estimated_thickness=0.1, surface_roughness=0.1,
        )
        
        props = engine.infer_properties(features, 0.001)
        
        # Should likely be rigid solid
        assert props.material_type in [MaterialType.RIGID_SOLID, MaterialType.SOFT_SOLID]
    
    def test_liquid_classification(self, engine):
        """Test classification of liquid."""
        features = ShadowFeatures(
            area=0.005, perimeter=0.25, circularity=0.95,
            aspect_ratio=1.0, convexity=1.0,
            deformation_rate=0.0, motion_stability=0.9,
            shadow_contrast=0.95, edge_sharpness=0.9,
            estimated_thickness=0.02, surface_roughness=0.05,
        )
        
        props = engine.infer_properties(features, 0.001)
        
        # Low thickness and surface roughness suggests liquid
        assert props.density < 2000  # Most liquids


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_zero_volume(self):
        """Test handling of zero volume."""
        engine = PhysicsInferenceEngine()
        features = ShadowFeatures.from_contour(np.random.randn(10, 2).astype(np.float32))
        
        props = engine.infer_properties(features, 0.0)
        
        # Mass should be zero
        assert props.mass == 0.0
    
    def test_negative_volume(self):
        """Test handling of negative volume."""
        engine = PhysicsInferenceEngine()
        features = ShadowFeatures.from_contour(np.random.randn(10, 2).astype(np.float32))
        
        # Should handle gracefully
        props = engine.infer_properties(features, -0.001)
        
        # Mass should be non-negative
        assert props.mass >= 0.0
    
    def test_very_large_volume(self):
        """Test handling of very large volume."""
        engine = PhysicsInferenceEngine()
        features = ShadowFeatures.from_contour(np.random.randn(10, 2).astype(np.float32))
        
        # Should handle gracefully
        props = engine.infer_properties(features, 1000.0)
        
        # Mass should be reasonable
        assert props.mass < 1e9  # Less than 1 million tons


class TestPerformance:
    """Performance benchmarks."""
    
    def test_model_size(self):
        """Test that model size is reasonable."""
        engine = PhysicsInferenceEngine()
        
        total_params = (
            engine.material_classifier.count_parameters() +
            engine.rigidity_estimator.count_parameters() +
            engine.density_estimator.count_parameters()
        )
        
        # Should be under 1000 parameters
        assert total_params < 1000, f"Model too large: {total_params} params"
        
        print(f"\n  Total parameters: {total_params}")
    
    def test_throughput(self):
        """Test inference throughput."""
        engine = PhysicsInferenceEngine()
        features = ShadowFeatures.from_contour(
            np.random.randn(32, 2).astype(np.float32)
        )
        
        import time
        n_iterations = 10000
        
        start = time.perf_counter()
        for _ in range(n_iterations):
            props = engine.infer_properties(features, 0.001)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        throughput = n_iterations / (elapsed_ms / 1000)
        
        print(f"\n  Throughput: {throughput:.0f} inferences/sec")
        
        # Should handle at least 1000 inferences/sec
        assert throughput > 1000


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
