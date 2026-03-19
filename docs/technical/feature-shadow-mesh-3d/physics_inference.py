"""
Lightweight Differentiable Physics Inference
============================================

Infers physical properties (rigidity, mass, material type) from shadow
characteristics using a minimal 2-3 layer neural network.

No PyTorch/TensorFlow dependencies - pure NumPy implementation.
Performance target: <5ms inference time

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import time


class MaterialType(Enum):
    """Material type classification."""
    RIGID_SOLID = "rigid_solid"           # Metal, ceramic, hard plastic
    SOFT_SOLID = "soft_solid"             # Rubber, foam, soft plastic
    LIQUID = "liquid"                     # Water, oil, gel
    GRANULAR = "granular"                 # Sand, rice, beans
    GAS = "gas"                           # Air, helium (rare in shadow context)
    UNKNOWN = "unknown"


@dataclass
class PhysicsProperties:
    """
    Inferred physical properties of a reconstructed object.
    
    Attributes:
        material_type: Classification of material behavior
        rigidity: Stiffness score (0.0 = very soft, 1.0 = perfectly rigid)
        youngs_modulus: Elastic modulus in Pascals
        density: Mass density in kg/m³
        mass: Estimated total mass in kg
        volume: Object volume in m³
        friction_coefficient: Surface friction (0.0-1.0)
        restitution: Bounciness coefficient (0.0-1.0)
        confidence: Inference confidence (0.0-1.0)
        inference_time_ms: Time taken for inference
    """
    material_type: MaterialType
    rigidity: float
    youngs_modulus: float  # Pa
    density: float  # kg/m³
    mass: float  # kg
    volume: float  # m³
    friction_coefficient: float
    restitution: float
    confidence: float
    inference_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'material_type': self.material_type.value,
            'rigidity': float(self.rigidity),
            'youngs_modulus_pa': float(self.youngs_modulus),
            'density_kg_m3': float(self.density),
            'mass_kg': float(self.mass),
            'volume_m3': float(self.volume),
            'friction_coefficient': float(self.friction_coefficient),
            'restitution': float(self.restitution),
            'confidence': float(self.confidence),
            'inference_time_ms': float(self.inference_time_ms),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhysicsProperties':
        """Create from dictionary."""
        return cls(
            material_type=MaterialType(data.get('material_type', 'unknown')),
            rigidity=data['rigidity'],
            youngs_modulus=data['youngs_modulus_pa'],
            density=data['density_kg_m3'],
            mass=data['mass_kg'],
            volume=data['volume_m3'],
            friction_coefficient=data['friction_coefficient'],
            restitution=data['restitution'],
            confidence=data['confidence'],
            inference_time_ms=data.get('inference_time_ms', 0.0),
        )


class ActivationFunction:
    """Neural network activation functions."""
    
    @staticmethod
    def relu(x: NDArray[np.float32]) -> NDArray[np.float32]:
        """ReLU activation: max(0, x)."""
        return np.maximum(0, x).astype(np.float32)
    
    @staticmethod
    def leaky_relu(x: NDArray[np.float32], alpha: float = 0.01) -> NDArray[np.float32]:
        """Leaky ReLU activation."""
        return np.where(x > 0, x, alpha * x).astype(np.float32)
    
    @staticmethod
    def sigmoid(x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Sigmoid activation: 1 / (1 + exp(-x))."""
        return (1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))).astype(np.float32)
    
    @staticmethod
    def tanh(x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Hyperbolic tangent."""
        return np.tanh(x).astype(np.float32)
    
    @staticmethod
    def softmax(x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Softmax activation."""
        exp_x = np.exp(x - np.max(x))
        return (exp_x / np.sum(exp_x)).astype(np.float32)


class MiniMLP:
    """
    Minimal Multi-Layer Perceptron for physics inference.
    
    Architecture: Input -> Hidden1 -> Hidden2 -> Output
    - 2-3 hidden layers max
    - <1000 parameters total
    - <5ms inference on CPU
    
    Example:
        >>> mlp = MiniMLP(input_dim=10, hidden_dims=[32, 16], output_dim=5)
        >>> output = mlp.predict(input_features)
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        output_dim: int,
        activation: str = 'leaky_relu',
        output_activation: Optional[str] = None,
    ):
        """
        Initialize MLP.
        
        Args:
            input_dim: Input feature dimension
            hidden_dims: List of hidden layer dimensions
            output_dim: Output dimension
            activation: Activation function for hidden layers
            output_activation: Optional activation for output layer
        """
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        
        # Select activation functions
        self.activation = self._get_activation(activation)
        self.output_activation = self._get_activation(output_activation) if output_activation else None
        
        # Initialize weights and biases
        self.weights: List[NDArray[np.float32]] = []
        self.biases: List[NDArray[np.float32]] = []
        
        self._initialize_weights()
    
    def _get_activation(self, name: str) -> Callable:
        """Get activation function by name."""
        activations = {
            'relu': ActivationFunction.relu,
            'leaky_relu': ActivationFunction.leaky_relu,
            'sigmoid': ActivationFunction.sigmoid,
            'tanh': ActivationFunction.tanh,
            'softmax': ActivationFunction.softmax,
        }
        return activations.get(name, ActivationFunction.leaky_relu)
    
    def _initialize_weights(self) -> None:
        """Initialize weights using Xavier/He initialization."""
        dims = [self.input_dim] + self.hidden_dims + [self.output_dim]
        
        for i in range(len(dims) - 1):
            # He initialization for ReLU variants
            std = np.sqrt(2.0 / dims[i])
            w = np.random.randn(dims[i], dims[i + 1]).astype(np.float32) * std
            b = np.zeros(dims[i + 1], dtype=np.float32)
            
            self.weights.append(w)
            self.biases.append(b)
    
    def predict(self, x: NDArray[np.float32]) -> NDArray[np.float32]:
        """
        Forward pass through the network.
        
        Args:
            x: Input features (input_dim,) or (batch, input_dim)
            
        Returns:
            Network output
        """
        # Ensure 2D input
        if x.ndim == 1:
            x = x.reshape(1, -1)
        
        # Forward pass
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            x = x @ w + b
            
            # Apply activation
            if i < len(self.weights) - 1:
                x = self.activation(x)
            elif self.output_activation is not None:
                x = self.output_activation(x)
        
        return x.astype(np.float32)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get all parameters as dictionary."""
        return {
            'input_dim': self.input_dim,
            'hidden_dims': self.hidden_dims,
            'output_dim': self.output_dim,
            'weights': [w.tolist() for w in self.weights],
            'biases': [b.tolist() for b in self.biases],
        }
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set parameters from dictionary."""
        self.weights = [np.array(w, dtype=np.float32) for w in params['weights']]
        self.biases = [np.array(b, dtype=np.float32) for b in params['biases']]
    
    def count_parameters(self) -> int:
        """Count total number of parameters."""
        return sum(w.size + b.size for w, b in zip(self.weights, self.biases))


@dataclass
class ShadowFeatures:
    """Features extracted from shadow contour for physics inference."""
    # Geometric features
    area: float
    perimeter: float
    circularity: float
    aspect_ratio: float
    convexity: float
    
    # Temporal features (if tracking over time)
    deformation_rate: float
    motion_stability: float
    
    # Acoustic features
    shadow_contrast: float
    edge_sharpness: float
    
    # Derived features
    estimated_thickness: float
    surface_roughness: float
    
    def to_vector(self) -> NDArray[np.float32]:
        """Convert to feature vector."""
        return np.array([
            self.area,
            self.perimeter,
            self.circularity,
            self.aspect_ratio,
            self.convexity,
            self.deformation_rate,
            self.motion_stability,
            self.shadow_contrast,
            self.edge_sharpness,
            self.estimated_thickness,
            self.surface_roughness,
        ], dtype=np.float32)
    
    @classmethod
    def from_contour(
        cls,
        contour: NDArray[np.float32],
        confidence: Optional[NDArray[np.float32]] = None,
        prev_contour: Optional[NDArray[np.float32]] = None,
        dt: float = 1.0,
    ) -> 'ShadowFeatures':
        """Extract features from contour."""
        n_points = len(contour)
        
        if n_points < 3:
            return cls(
                area=0.0, perimeter=0.0, circularity=0.0,
                aspect_ratio=1.0, convexity=1.0,
                deformation_rate=0.0, motion_stability=1.0,
                shadow_contrast=0.5, edge_sharpness=0.5,
                estimated_thickness=0.01, surface_roughness=0.5,
            )
        
        # Area using shoelace formula
        x, y = contour[:, 0], contour[:, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        # Perimeter
        diffs = np.diff(contour, axis=0, append=contour[:1])
        perimeter = np.sum(np.linalg.norm(diffs, axis=1))
        
        # Circularity: 4πA / P² (1.0 for perfect circle)
        circularity = 4 * np.pi * area / (perimeter ** 2 + 1e-10)
        circularity = np.clip(circularity, 0.0, 1.0)
        
        # Aspect ratio
        bbox_min = contour.min(axis=0)
        bbox_max = contour.max(axis=0)
        bbox_size = bbox_max - bbox_min
        aspect_ratio = bbox_size[0] / (bbox_size[1] + 1e-10)
        aspect_ratio = np.clip(aspect_ratio, 0.1, 10.0)
        
        # Convexity
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(contour)
            hull_area = hull.volume  # In 2D, volume = area
            convexity = area / (hull_area + 1e-10)
        except Exception:
            convexity = 1.0
        
        # Deformation rate
        deformation_rate = 0.0
        if prev_contour is not None and dt > 0:
            # Compute contour similarity
            n = min(len(contour), len(prev_contour))
            if n > 0:
                diff = np.mean(np.linalg.norm(contour[:n] - prev_contour[:n], axis=1))
                deformation_rate = diff / dt
        
        # Motion stability
        motion_stability = 1.0 - np.clip(deformation_rate / 0.1, 0.0, 1.0)
        
        # Shadow contrast from confidence
        shadow_contrast = np.mean(confidence) if confidence is not None else 0.5
        
        # Edge sharpness
        if confidence is not None and len(confidence) > 2:
            edge_sharpness = 1.0 - np.std(confidence)
        else:
            edge_sharpness = 0.5
        
        # Estimated thickness (heuristic based on area)
        estimated_thickness = np.sqrt(area) * 0.1
        
        # Surface roughness from contour variation
        if n_points > 3:
            angles = np.arctan2(np.diff(contour[:, 1]), np.diff(contour[:, 0]))
            surface_roughness = np.std(angles) / np.pi
        else:
            surface_roughness = 0.5
        
        return cls(
            area=float(area),
            perimeter=float(perimeter),
            circularity=float(circularity),
            aspect_ratio=float(aspect_ratio),
            convexity=float(convexity),
            deformation_rate=float(deformation_rate),
            motion_stability=float(motion_stability),
            shadow_contrast=float(shadow_contrast),
            edge_sharpness=float(edge_sharpness),
            estimated_thickness=float(estimated_thickness),
            surface_roughness=float(surface_roughness),
        )


class PhysicsInferenceEngine:
    """
    Lightweight physics inference engine using minimal neural networks.
    
    Infers material properties from shadow characteristics without
    requiring heavy ML frameworks.
    
    Example:
        >>> engine = PhysicsInferenceEngine()
        >>> features = ShadowFeatures.from_contour(contour, confidence)
        >>> props = engine.infer_properties(features, volume=0.001)
        >>> print(f"Material: {props.material_type.value}, Mass: {props.mass:.3f}kg")
    """
    
    def __init__(self):
        """Initialize inference engine with pre-trained models."""
        self._init_material_classifier()
        self._init_rigidity_estimator()
        self._init_density_estimator()
    
    def _init_material_classifier(self) -> None:
        """Initialize material type classifier (3-layer MLP)."""
        # Input: 11 features -> Hidden: 24 -> Hidden: 12 -> Output: 5 material types
        self.material_classifier = MiniMLP(
            input_dim=11,
            hidden_dims=[24, 12],
            output_dim=5,
            activation='leaky_relu',
            output_activation='softmax',
        )
        
        # Set pre-trained weights (simplified - would load from file in production)
        self._init_pretrained_classifier()
    
    def _init_rigidity_estimator(self) -> None:
        """Initialize rigidity estimator (2-layer MLP)."""
        # Input: 11 features -> Hidden: 16 -> Output: 1 (rigidity 0-1)
        self.rigidity_estimator = MiniMLP(
            input_dim=11,
            hidden_dims=[16],
            output_dim=1,
            activation='leaky_relu',
            output_activation='sigmoid',
        )
        
        self._init_pretrained_rigidity()
    
    def _init_density_estimator(self) -> None:
        """Initialize density estimator (2-layer MLP)."""
        # Input: 11 features + rigidity -> Hidden: 16 -> Output: 1 (log density)
        self.density_estimator = MiniMLP(
            input_dim=12,
            hidden_dims=[16],
            output_dim=1,
            activation='leaky_relu',
            output_activation=None,
        )
        
        self._init_pretrained_density()
    
    def _init_pretrained_classifier(self) -> None:
        """Initialize classifier with pre-trained weights."""
        # Simplified heuristic-based initialization
        # In production, load from trained model file
        np.random.seed(42)
        
        # Material classification heuristics encoded in weights:
        # - High circularity + low deformation = rigid solid
        # - Low circularity + high deformation = soft solid
        # - Very low deformation + uniform confidence = liquid
        # - Irregular shape + medium deformation = granular
        
        w0 = np.random.randn(11, 24).astype(np.float32) * 0.1
        b0 = np.zeros(24, dtype=np.float32)
        
        # Encode heuristics in first layer
        # Feature indices: area=0, perimeter=1, circularity=2, aspect_ratio=3,
        # convexity=4, deformation_rate=5, motion_stability=6, shadow_contrast=7,
        # edge_sharpness=8, estimated_thickness=9, surface_roughness=10
        
        # Rigid solid: high circularity, low deformation, high stability
        w0[2, 0] = 0.5  # circularity
        w0[5, 0] = -0.5  # deformation
        w0[6, 0] = 0.3  # stability
        
        # Soft solid: medium circularity, medium deformation
        w0[2, 1] = 0.2
        w0[5, 1] = 0.3
        
        # Liquid: high circularity, very low deformation, high contrast
        w0[2, 2] = 0.4
        w0[5, 2] = -0.7
        w0[7, 2] = 0.3
        
        # Granular: low circularity, irregular
        w0[2, 3] = -0.3
        w0[10, 3] = 0.4
        
        # Gas: very low density features
        w0[0, 4] = -0.5
        w0[9, 4] = -0.5
        
        w1 = np.random.randn(24, 12).astype(np.float32) * 0.1
        b1 = np.zeros(12, dtype=np.float32)
        
        w2 = np.random.randn(12, 5).astype(np.float32) * 0.1
        b2 = np.zeros(5, dtype=np.float32)
        
        self.material_classifier.weights = [w0, w1, w2]
        self.material_classifier.biases = [b0, b1, b2]
    
    def _init_pretrained_rigidity(self) -> None:
        """Initialize rigidity estimator with pre-trained weights."""
        np.random.seed(43)
        
        w0 = np.random.randn(11, 16).astype(np.float32) * 0.1
        b0 = np.zeros(16, dtype=np.float32)
        
        # Rigidity correlates with: high circularity, low deformation, high edge sharpness
        w0[2, 0] = 0.4   # circularity
        w0[5, 0] = -0.6  # deformation
        w0[8, 0] = 0.3   # edge sharpness
        w0[6, 0] = 0.2   # motion stability
        
        w1 = np.random.randn(16, 1).astype(np.float32) * 0.1
        b1 = np.array([0.5], dtype=np.float32)  # Baseline rigidity
        
        self.rigidity_estimator.weights = [w0, w1]
        self.rigidity_estimator.biases = [b0, b1]
    
    def _init_pretrained_density(self) -> None:
        """Initialize density estimator with pre-trained weights."""
        np.random.seed(44)
        
        w0 = np.random.randn(12, 16).astype(np.float32) * 0.1
        b0 = np.zeros(16, dtype=np.float32)
        
        # Density correlates with: thickness, rigidity, low deformation
        w0[9, 0] = 0.5   # estimated thickness
        w0[11, 0] = 0.3  # rigidity (input index 11)
        w0[5, 0] = -0.2  # deformation
        
        w1 = np.random.randn(16, 1).astype(np.float32) * 0.1
        b1 = np.array([np.log(500)], dtype=np.float32)  # Baseline ~500 kg/m³
        
        self.density_estimator.weights = [w0, w1]
        self.density_estimator.biases = [b0, b1]
    
    def infer_properties(
        self,
        features: ShadowFeatures,
        volume: float,
        prev_features: Optional[ShadowFeatures] = None,
    ) -> PhysicsProperties:
        """
        Infer physical properties from shadow features.
        
        Args:
            features: Extracted shadow features
            volume: Object volume in m³
            prev_features: Previous frame features for temporal analysis
            
        Returns:
            PhysicsProperties with inferred values
        """
        start_time = time.perf_counter()
        
        # Get feature vector
        feature_vector = features.to_vector()
        
        # Classify material type
        material_probs = self.material_classifier.predict(feature_vector)[0]
        material_idx = np.argmax(material_probs)
        material_type = [
            MaterialType.RIGID_SOLID,
            MaterialType.SOFT_SOLID,
            MaterialType.LIQUID,
            MaterialType.GRANULAR,
            MaterialType.GAS,
        ][material_idx]
        
        # Estimate rigidity
        rigidity = float(self.rigidity_estimator.predict(feature_vector)[0, 0])
        rigidity = np.clip(rigidity, 0.0, 1.0)
        
        # Estimate density (using rigidity as additional feature)
        density_input = np.concatenate([feature_vector, [rigidity]])
        log_density = self.density_estimator.predict(density_input)[0, 0]
        density = np.exp(log_density)
        
        # Clamp density to realistic values
        density = np.clip(density, 10.0, 25000.0)
        
        # Compute Young's modulus from rigidity and density
        youngs_modulus = self._estimate_youngs_modulus(rigidity, material_type)
        
        # Compute mass
        mass = density * volume
        
        # Estimate friction coefficient
        friction = self._estimate_friction(rigidity, material_type)
        
        # Estimate restitution (bounciness)
        restitution = self._estimate_restitution(rigidity, material_type)
        
        # Compute confidence from probability and feature quality
        confidence = self._compute_confidence(material_probs, features)
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000
        
        return PhysicsProperties(
            material_type=material_type,
            rigidity=rigidity,
            youngs_modulus=youngs_modulus,
            density=density,
            mass=mass,
            volume=volume,
            friction_coefficient=friction,
            restitution=restitution,
            confidence=confidence,
            inference_time_ms=inference_time_ms,
        )
    
    def _estimate_youngs_modulus(
        self,
        rigidity: float,
        material_type: MaterialType,
    ) -> float:
        """Estimate Young's modulus from rigidity and material type."""
        # Base values for different material types (Pa)
        base_modulus = {
            MaterialType.RIGID_SOLID: 10e9,    # ~10 GPa (plastic/ceramic)
            MaterialType.SOFT_SOLID: 1e6,      # ~1 MPa (rubber)
            MaterialType.LIQUID: 2.2e9,        # ~2.2 GPa (water bulk modulus)
            MaterialType.GRANULAR: 100e6,      # ~100 MPa
            MaterialType.GAS: 100e3,           # ~100 kPa
            MaterialType.UNKNOWN: 1e9,
        }
        
        base = base_modulus.get(material_type, 1e9)
        
        # Scale by rigidity (0.1 to 10x)
        scale = 0.1 + rigidity * 9.9
        
        return base * scale
    
    def _estimate_friction(
        self,
        rigidity: float,
        material_type: MaterialType,
    ) -> float:
        """Estimate friction coefficient."""
        # Base friction values
        base_friction = {
            MaterialType.RIGID_SOLID: 0.3,
            MaterialType.SOFT_SOLID: 0.8,
            MaterialType.LIQUID: 0.01,
            MaterialType.GRANULAR: 0.6,
            MaterialType.GAS: 0.0,
            MaterialType.UNKNOWN: 0.5,
        }
        
        base = base_friction.get(material_type, 0.5)
        
        # Slight variation based on rigidity
        variation = (rigidity - 0.5) * 0.2
        
        return np.clip(base + variation, 0.0, 1.0)
    
    def _estimate_restitution(
        self,
        rigidity: float,
        material_type: MaterialType,
    ) -> float:
        """Estimate restitution (bounciness) coefficient."""
        # Base restitution values
        base_restitution = {
            MaterialType.RIGID_SOLID: 0.7,
            MaterialType.SOFT_SOLID: 0.2,
            MaterialType.LIQUID: 0.0,
            MaterialType.GRANULAR: 0.1,
            MaterialType.GAS: 0.9,
            MaterialType.UNKNOWN: 0.5,
        }
        
        base = base_restitution.get(material_type, 0.5)
        
        # Higher rigidity = higher restitution
        scale = 0.5 + rigidity * 0.5
        
        return np.clip(base * scale, 0.0, 1.0)
    
    def _compute_confidence(
        self,
        material_probs: NDArray[np.float32],
        features: ShadowFeatures,
    ) -> float:
        """Compute overall confidence in inference."""
        # Confidence from material classification certainty
        max_prob = np.max(material_probs)
        entropy = -np.sum(material_probs * np.log(material_probs + 1e-10))
        max_entropy = np.log(len(material_probs))
        certainty = 1.0 - entropy / max_entropy
        
        # Confidence from feature quality
        feature_confidence = features.shadow_contrast * features.edge_sharpness
        
        # Combined confidence
        confidence = 0.6 * certainty + 0.4 * feature_confidence
        
        return np.clip(confidence, 0.0, 1.0)


def benchmark_physics_inference():
    """Benchmark physics inference performance."""
    print("=" * 60)
    print("PHYSICS INFERENCE BENCHMARK")
    print("=" * 60)
    
    engine = PhysicsInferenceEngine()
    
    # Print model sizes
    print("\nModel Architecture:")
    print(f"  Material classifier: {engine.material_classifier.count_parameters()} params")
    print(f"  Rigidity estimator: {engine.rigidity_estimator.count_parameters()} params")
    print(f"  Density estimator: {engine.density_estimator.count_parameters()} params")
    total_params = (
        engine.material_classifier.count_parameters() +
        engine.rigidity_estimator.count_parameters() +
        engine.density_estimator.count_parameters()
    )
    print(f"  Total: {total_params} parameters")
    
    # Test different object types
    test_cases = [
        ("Rigid sphere", _create_rigid_sphere_features()),
        ("Soft object", _create_soft_object_features()),
        ("Liquid drop", _create_liquid_features()),
        ("Granular pile", _create_granular_features()),
    ]
    
    print("\nInference Results:")
    print("-" * 60)
    
    for name, features in test_cases:
        volume = 0.001  # 1 liter
        
        # Warm-up
        for _ in range(100):
            engine.infer_properties(features, volume)
        
        # Benchmark
        n_iterations = 1000
        start = time.perf_counter()
        
        for _ in range(n_iterations):
            props = engine.infer_properties(features, volume)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        latency = elapsed_ms / n_iterations
        
        print(f"\n{name}:")
        print(f"  Material: {props.material_type.value}")
        print(f"  Rigidity: {props.rigidity:.2f}")
        print(f"  Density: {props.density:.1f} kg/m³")
        print(f"  Mass: {props.mass*1000:.2f} g")
        print(f"  Young's modulus: {props.youngs_modulus/1e9:.2f} GPa")
        print(f"  Confidence: {props.confidence:.2f}")
        print(f"  Inference time: {latency:.3f}ms")
    
    print("\n" + "=" * 60)
    print("TARGET: <5ms inference time")
    print("=" * 60)


def _create_rigid_sphere_features() -> ShadowFeatures:
    """Create features for a rigid spherical object."""
    return ShadowFeatures(
        area=0.00785,  # ~10cm diameter circle
        perimeter=0.314,
        circularity=1.0,  # Perfect circle
        aspect_ratio=1.0,
        convexity=1.0,
        deformation_rate=0.0,  # No deformation
        motion_stability=1.0,
        shadow_contrast=0.9,
        edge_sharpness=0.95,
        estimated_thickness=0.1,
        surface_roughness=0.1,
    )


def _create_soft_object_features() -> ShadowFeatures:
    """Create features for a soft deformable object."""
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


def _create_liquid_features() -> ShadowFeatures:
    """Create features for a liquid object."""
    return ShadowFeatures(
        area=0.005,
        perimeter=0.25,
        circularity=0.95,  # Surface tension makes drops circular
        aspect_ratio=1.0,
        convexity=1.0,
        deformation_rate=0.0,  # No permanent deformation
        motion_stability=0.9,
        shadow_contrast=0.95,
        edge_sharpness=0.9,
        estimated_thickness=0.02,
        surface_roughness=0.05,
    )


def _create_granular_features() -> ShadowFeatures:
    """Create features for a granular material pile."""
    return ShadowFeatures(
        area=0.012,
        perimeter=0.5,
        circularity=0.5,  # Irregular shape
        aspect_ratio=1.5,
        convexity=0.8,
        deformation_rate=0.02,
        motion_stability=0.5,
        shadow_contrast=0.6,
        edge_sharpness=0.4,
        estimated_thickness=0.15,
        surface_roughness=0.8,
    )


if __name__ == "__main__":
    benchmark_physics_inference()
