"""
Property Prediction Model for Shadow Intelligence Layer.

Lightweight model for predicting object properties:
- Material type: rigid, soft, liquid
- Size category: small, medium, large
- Confidence scores for each prediction

Target: <2MB model, >90% accuracy, <3ms inference on Snapdragon 8 Gen 3 NPU
"""

from __future__ import annotations

import numpy as np
import tensorflow as tf
from tensorflow import keras
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any
import json


@dataclass
class PropertyPrediction:
    """Structured output for property prediction."""
    material: str
    material_confidence: float
    size_category: str
    size_confidence: float
    material_probabilities: Dict[str, float]
    size_probabilities: Dict[str, float]
    overall_confidence: float


@dataclass
class PropertyModelConfig:
    """Configuration for the property predictor."""
    input_shape: Tuple[int, int, int] = (64, 64, 1)
    num_materials: int = 3  # rigid, soft, liquid
    num_sizes: int = 3  # small, medium, large
    dropout_rate: float = 0.25
    use_separable_conv: bool = True
    
    # Class labels
    materials: List[str] = None
    size_categories: List[str] = None
    
    def __post_init__(self):
        if self.materials is None:
            self.materials = ["rigid", "soft", "liquid"]
        if self.size_categories is None:
            self.size_categories = ["small", "medium", "large"]


class PropertyPredictor:
    """
    Lightweight model for predicting object properties from shadow data.
    
    Uses efficient architecture with depthwise separable convolutions
    for minimal model size and fast inference on edge devices.
    """
    
    def __init__(self, config: Optional[PropertyModelConfig] = None) -> None:
        """Initialize the property predictor."""
        self.config = config or PropertyModelConfig()
        self.model: Optional[keras.Model] = None
        self._build_model()
    
    def _build_model(self) -> None:
        """Build the lightweight property prediction architecture."""
        cfg = self.config
        inputs = keras.Input(shape=cfg.input_shape, name="shadow_input")
        
        x = inputs
        
        # Block 1: Initial feature extraction (32 filters)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="sepconv1"
            )(x)
        else:
            x = keras.layers.Conv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="conv1"
            )(x)
        x = keras.layers.BatchNormalization(name="bn1")(x)
        x = keras.layers.ReLU(name="relu1")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool1")(x)  # 32x32
        
        # Block 2: Deeper features (64 filters)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="sepconv2"
            )(x)
        else:
            x = keras.layers.Conv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="conv2"
            )(x)
        x = keras.layers.BatchNormalization(name="bn2")(x)
        x = keras.layers.ReLU(name="relu2")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool2")(x)  # 16x16
        
        # Block 3: High-level features (96 filters - smaller than intent model)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                96, (3, 3), padding='same', use_bias=False,
                name="sepconv3"
            )(x)
        else:
            x = keras.layers.Conv2D(
                96, (3, 3), padding='same', use_bias=False,
                name="conv3"
            )(x)
        x = keras.layers.BatchNormalization(name="bn3")(x)
        x = keras.layers.ReLU(name="relu3")(x)
        
        # Global average pooling
        x = keras.layers.GlobalAveragePooling2D(name="gap")(x)
        
        # Shared dense layer (smaller than intent model)
        x = keras.layers.Dense(64, use_bias=False, name="dense_shared")(x)
        x = keras.layers.BatchNormalization(name="bn_shared")(x)
        x = keras.layers.ReLU(name="relu_shared")(x)
        x = keras.layers.Dropout(cfg.dropout_rate, name="dropout")(x)
        
        # Multi-head outputs
        # Material classification
        material_out = keras.layers.Dense(
            cfg.num_materials, activation='softmax',
            name="material"
        )(x)
        
        # Size category classification
        size_out = keras.layers.Dense(
            cfg.num_sizes, activation='softmax',
            name="size_category"
        )(x)
        
        self.model = keras.Model(
            inputs=inputs,
            outputs=[material_out, size_out],
            name="property_predictor"
        )
    
    def compile(
        self,
        optimizer: Optional[keras.optimizers.Optimizer] = None,
        loss_weights: Optional[Dict[str, float]] = None
    ) -> None:
        """Compile the model with multi-task loss."""
        if optimizer is None:
            optimizer = keras.optimizers.Adam(learning_rate=0.001)
        
        if loss_weights is None:
            loss_weights = {
                "material": 1.0,
                "size_category": 1.0
            }
        
        self.model.compile(
            optimizer=optimizer,
            loss={
                "material": "categorical_crossentropy",
                "size_category": "categorical_crossentropy"
            },
            loss_weights=loss_weights,
            metrics={
                "material": ["accuracy"],
                "size_category": ["accuracy"]
            }
        )
    
    def fit(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray],
        validation_data: Optional[Tuple[np.ndarray, Dict[str, np.ndarray]]] = None,
        epochs: int = 50,
        batch_size: int = 32,
        callbacks: Optional[List[keras.callbacks.Callback]] = None,
        **kwargs
    ) -> keras.callbacks.History:
        """Train the model."""
        if callbacks is None:
            callbacks = self._get_default_callbacks()
        
        return self.model.fit(
            x, y,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            **kwargs
        )
    
    def _get_default_callbacks(self) -> List[keras.callbacks.Callback]:
        """Get default training callbacks."""
        return [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
    
    def predict(self, x: np.ndarray) -> List[PropertyPrediction]:
        """
        Predict properties from shadow data.
        
        Args:
            x: Input array of shape (N, H, W, C) or (H, W, C)
        
        Returns:
            List of PropertyPrediction objects
        """
        # Ensure batch dimension
        if len(x.shape) == 3:
            x = np.expand_dims(x, axis=0)
        
        # Get predictions
        material_pred, size_pred = self.model.predict(x, verbose=0)
        
        # Convert to structured output
        predictions = []
        cfg = self.config
        for i in range(len(x)):
            mat_idx = np.argmax(material_pred[i])
            size_idx = np.argmax(size_pred[i])
            
            # Build probability dictionaries
            mat_probs = {
                cfg.materials[j]: float(material_pred[i][j])
                for j in range(len(cfg.materials))
            }
            size_probs = {
                cfg.size_categories[j]: float(size_pred[i][j])
                for j in range(len(cfg.size_categories))
            }
            
            pred = PropertyPrediction(
                material=cfg.materials[mat_idx],
                material_confidence=float(material_pred[i][mat_idx]),
                size_category=cfg.size_categories[size_idx],
                size_confidence=float(size_pred[i][size_idx]),
                material_probabilities=mat_probs,
                size_probabilities=size_probs,
                overall_confidence=float(
                    material_pred[i][mat_idx] * size_pred[i][size_idx]
                )
            )
            predictions.append(pred)
        
        return predictions
    
    def evaluate(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Evaluate model performance."""
        results = self.model.evaluate(x, y, verbose=0, return_dict=True)
        return results
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        self.model.save(path)
        # Save config separately
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'input_shape': self.config.input_shape,
                'materials': self.config.materials,
                'size_categories': self.config.size_categories
            }, f)
    
    @classmethod
    def load(cls, path: str) -> "PropertyPredictor":
        """Load model from disk."""
        # Load config
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            config = PropertyModelConfig(
                input_shape=tuple(config_dict['input_shape']),
                materials=config_dict['materials'],
                size_categories=config_dict['size_categories']
            )
        except FileNotFoundError:
            config = PropertyModelConfig()
        
        # Create instance and load weights
        instance = cls(config)
        instance.model = keras.models.load_model(path)
        return instance
    
    def export_tflite(
        self,
        path: str,
        optimize: bool = True,
        representative_dataset: Optional[Callable] = None
    ) -> None:
        """
        Export model to TensorFlow Lite format.
        
        Args:
            path: Output path for .tflite file
            optimize: Whether to apply optimizations
            representative_dataset: Dataset for full integer quantization
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if optimize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            if representative_dataset is not None:
                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [
                    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
                ]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        with open(path, 'wb') as f:
            f.write(tflite_model)
        
        # Log model size
        size_mb = len(tflite_model) / (1024 * 1024)
        print(f"TFLite model exported: {path}")
        print(f"Model size: {size_mb:.2f} MB")
    
    def get_model_size(self) -> float:
        """Get model size in MB."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as f:
            temp_path = f.name
        
        self.save(temp_path)
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        os.remove(temp_path)
        
        return size_mb
    
    def summary(self) -> None:
        """Print model summary."""
        self.model.summary()
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return self.model.count_params()


def create_property_predictor(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    **kwargs
) -> PropertyPredictor:
    """Factory function to create a property predictor."""
    config = PropertyModelConfig(input_shape=input_shape, **kwargs)
    return PropertyPredictor(config)
