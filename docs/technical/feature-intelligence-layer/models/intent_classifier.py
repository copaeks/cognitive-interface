"""
Intent Classification Model for Shadow Intelligence Layer.

Lightweight CNN for classifying:
- Object type: human hand, tool, other object
- Grasping state: open, closed, pinching
- Interaction intent: pointing, manipulating, resting

Target: <5MB model, >92% accuracy, <5ms inference on Snapdragon 8 Gen 3 NPU
"""

from __future__ import annotations

import numpy as np
import tensorflow as tf
from tensorflow import keras
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any
import json


@dataclass
class IntentPrediction:
    """Structured output for intent classification."""
    object_type: str
    object_confidence: float
    grasp_state: str
    grasp_confidence: float
    interaction_intent: str
    interaction_confidence: float
    overall_confidence: float
    raw_logits: Dict[str, np.ndarray]


@dataclass
class ModelConfig:
    """Configuration for the intent classifier."""
    input_shape: Tuple[int, int, int] = (64, 64, 1)
    num_object_types: int = 3  # hand, tool, other
    num_grasp_states: int = 3  # open, closed, pinching
    num_interaction_intents: int = 3  # pointing, manipulating, resting
    dropout_rate: float = 0.3
    use_separable_conv: bool = True  # For smaller model size
    
    # Class labels
    object_types: List[str] = None
    grasp_states: List[str] = None
    interaction_intents: List[str] = None
    
    def __post_init__(self):
        if self.object_types is None:
            self.object_types = ["hand", "tool", "other"]
        if self.grasp_states is None:
            self.grasp_states = ["open", "closed", "pinching"]
        if self.interaction_intents is None:
            self.interaction_intents = ["pointing", "manipulating", "resting"]


class IntentClassifier:
    """
    Lightweight CNN for intent classification from shadow data.
    
    Architecture optimized for edge deployment:
    - Depthwise separable convolutions for efficiency
    - Global average pooling instead of flatten
    - Multi-head output for different prediction tasks
    """
    
    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        """Initialize the intent classifier."""
        self.config = config or ModelConfig()
        self.model: Optional[keras.Model] = None
        self._build_model()
    
    def _build_model(self) -> None:
        """Build the lightweight CNN architecture."""
        cfg = self.config
        inputs = keras.Input(shape=cfg.input_shape, name="shadow_input")
        
        x = inputs
        
        # Block 1: Initial feature extraction
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
        
        # Block 2: Deeper features
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
        
        # Block 3: High-level features
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                128, (3, 3), padding='same', use_bias=False,
                name="sepconv3"
            )(x)
        else:
            x = keras.layers.Conv2D(
                128, (3, 3), padding='same', use_bias=False,
                name="conv3"
            )(x)
        x = keras.layers.BatchNormalization(name="bn3")(x)
        x = keras.layers.ReLU(name="relu3")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool3")(x)  # 8x8
        
        # Block 4: Final feature extraction
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                256, (3, 3), padding='same', use_bias=False,
                name="sepconv4"
            )(x)
        else:
            x = keras.layers.Conv2D(
                256, (3, 3), padding='same', use_bias=False,
                name="conv4"
            )(x)
        x = keras.layers.BatchNormalization(name="bn4")(x)
        x = keras.layers.ReLU(name="relu4")(x)
        
        # Global average pooling for efficiency
        x = keras.layers.GlobalAveragePooling2D(name="gap")(x)
        
        # Shared dense layer
        x = keras.layers.Dense(128, use_bias=False, name="dense_shared")(x)
        x = keras.layers.BatchNormalization(name="bn_shared")(x)
        x = keras.layers.ReLU(name="relu_shared")(x)
        x = keras.layers.Dropout(cfg.dropout_rate, name="dropout")(x)
        
        # Multi-head outputs
        # Object type classification
        object_out = keras.layers.Dense(
            cfg.num_object_types, activation='softmax',
            name="object_type"
        )(x)
        
        # Grasp state classification
        grasp_out = keras.layers.Dense(
            cfg.num_grasp_states, activation='softmax',
            name="grasp_state"
        )(x)
        
        # Interaction intent classification
        interaction_out = keras.layers.Dense(
            cfg.num_interaction_intents, activation='softmax',
            name="interaction_intent"
        )(x)
        
        self.model = keras.Model(
            inputs=inputs,
            outputs=[object_out, grasp_out, interaction_out],
            name="intent_classifier"
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
                "object_type": 1.0,
                "grasp_state": 1.0,
                "interaction_intent": 1.0
            }
        
        self.model.compile(
            optimizer=optimizer,
            loss={
                "object_type": "categorical_crossentropy",
                "grasp_state": "categorical_crossentropy",
                "interaction_intent": "categorical_crossentropy"
            },
            loss_weights=loss_weights,
            metrics={
                "object_type": ["accuracy"],
                "grasp_state": ["accuracy"],
                "interaction_intent": ["accuracy"]
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
    
    def predict(self, x: np.ndarray) -> List[IntentPrediction]:
        """
        Predict intent from shadow data.
        
        Args:
            x: Input array of shape (N, H, W, C) or (H, W, C)
        
        Returns:
            List of IntentPrediction objects
        """
        # Ensure batch dimension
        if len(x.shape) == 3:
            x = np.expand_dims(x, axis=0)
        
        # Get predictions
        object_pred, grasp_pred, interaction_pred = self.model.predict(x, verbose=0)
        
        # Convert to structured output
        predictions = []
        for i in range(len(x)):
            obj_idx = np.argmax(object_pred[i])
            grasp_idx = np.argmax(grasp_pred[i])
            interaction_idx = np.argmax(interaction_pred[i])
            
            pred = IntentPrediction(
                object_type=self.config.object_types[obj_idx],
                object_confidence=float(object_pred[i][obj_idx]),
                grasp_state=self.config.grasp_states[grasp_idx],
                grasp_confidence=float(grasp_pred[i][grasp_idx]),
                interaction_intent=self.config.interaction_intents[interaction_idx],
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
                'object_types': self.config.object_types,
                'grasp_states': self.config.grasp_states,
                'interaction_intents': self.config.interaction_intents
            }, f)
    
    @classmethod
    def load(cls, path: str) -> "IntentClassifier":
        """Load model from disk."""
        # Load config
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            config = ModelConfig(
                input_shape=tuple(config_dict['input_shape']),
                object_types=config_dict['object_types'],
                grasp_states=config_dict['grasp_states'],
                interaction_intents=config_dict['interaction_intents']
            )
        except FileNotFoundError:
            config = ModelConfig()
        
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


def create_intent_classifier(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    **kwargs
) -> IntentClassifier:
    """Factory function to create an intent classifier."""
    config = ModelConfig(input_shape=input_shape, **kwargs)
    return IntentClassifier(config)
